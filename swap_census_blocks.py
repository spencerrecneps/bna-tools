#! /usr/bin/python

##################################
# Traverse directory of downloaded
# BNA results and organize
# by state and city.
##################################
import sys
from tempfile import mkdtemp
import argparse
import os
import shutil
import json
import re
import zipfile
try:
    # For Python 3.0 and later
    from urllib.request import urlopen, URLError, HTTPError
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, URLError, HTTPError


def get_jsonparsed_data(url):
    """Receive the content of ``url``, parse it as JSON and return the
       object.
    """
    response = urlopen(url)
    data = unicode(response.read(), 'utf-8')
    return json.loads(data)


def main(argv):
    parser = argparse.ArgumentParser(description='Swap old census block shapefiles on production S3 for new ones with category scores')
    parser.add_argument('-v',dest='verbose',action='store_true',help='Verbose mode')
    parser.add_argument('-u','--url',dest='url',help='URL to grab JSON neighborhood data from',required=True) # https://bna.peopleforbikes.org/api/neighborhoods/?format=json
    parser.add_argument('-w','--overwrite',dest='overwrite',help='Overwrite existing files',action='store_true')
    parser.add_argument('-i','--id',dest='uuid',help='Neighborhood UUID (if given, only this neighborhood is downloaded)')
    parser.add_argument('-k','--keep',dest='outdir',help='Keep downloaded originals (OUTDIR = target directory)')
    parser.add_argument('-c','--copy',dest='copy',help='Copy new output back to S3',action='store_true')
    args = parser.parse_args()

    # set vars
    verbose = args.verbose
    if verbose:
        print(' ')
    outPath = args.outdir
    url = args.url
    overwrite = args.overwrite
    uuid = args.uuid
    copy = args.copy

    # grab json data from url
    if verbose:
        print('Getting json data from %s' % url)
    data = get_jsonparsed_data(url)

    # json returns 20 at a time so fetch new results when we're done
    while data:
        for city in data['results']:
            if uuid is not None and uuid != city['uuid']:
                continue
            else:
                print('Processing: %s' % city['label'])

                if outPath is None:
                    outPath = mkdtemp()

                targetPath = os.path.join(outPath,city['state_abbrev'],city['name'])
                oldFile = os.path.join(targetPath,'neighborhood_census_blocks_old.zip')
                newFile = os.path.join(targetPath,'neighborhood_census_blocks.zip')
                # check file if overwrite is not active
                if os.path.isfile(oldFile) and not overwrite:
                    print('  %s already exists, skipping' % oldFile)
                    continue
                # create target directory if it doesn't exist
                if not os.path.isdir(targetPath):
                    os.makedirs(targetPath)

                # download file
                jobUrl = 'https://bna.peopleforbikes.org/api/analysis_jobs/' \
                            + city['last_job'] \
                            + '/results/?format=json'
                if verbose:
                    print('  Downloading job data from %s' % jobUrl)
                try:
                    job = get_jsonparsed_data(jobUrl)
                except HTTPError, e:
                    print "  HTTP Error:", e.code, url
                    continue
                except URLError, e:
                    print "  URL Error:", e.reason, url
                    continue

                fileUrl = job['census_blocks_url']
                try:
                    f = urlopen(fileUrl)
                    if verbose:
                        print('  Downloading file from %s' % fileUrl)

                    # Open our local file for writing
                    with open(oldFile, "wb") as local_file:
                        local_file.write(f.read())

                #handle errors
                except HTTPError, e:
                    print "HTTP Error:", e.code, url
                    continue
                except URLError, e:
                    print "URL Error:", e.reason, url
                    continue

                # copy to new shapefile with additional attributes
                if verbose:
                    print('  Adding scores to neighborhood_census_blocks and saving')
                os.system(os.path.join(os.getcwd(),"add_scores.sh %s %s") % (oldFile,newFile))
                # shutil.make_archive(newFile,"zip",newFile)

                # copy to s3
                if copy:
                    s3url = re.sub('https://s3.amazonaws.com/','s3://',fileUrl)
                    if verbose:
                        print('  Uploading %s to %s' % (newFile,s3url))
                    os.system('aws s3 cp %s %s' % (newFile,s3url))

        if data['next'] is None:
            break
        else:
            data = get_jsonparsed_data(data['next'])

if __name__ == "__main__":
    main(sys.argv[1:])
