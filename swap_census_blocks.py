#! /usr/bin/python

##################################
# Traverse directory of downloaded
# BNA results and organize
# by state and city.
##################################
import sys
import argparse
import os
import shutil
import json
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
    parser = argparse.ArgumentParser(description='Organize downloaded BNA results by state and city')
    parser.add_argument('outdir',help='Output directory')
    parser.add_argument('-v',dest='verbose',action='store_true',help='Verbose mode')
    parser.add_argument('-u','--url',dest='url',help='URL to grab JSON neighborhood data from',required=True) # https://bna.peopleforbikes.org/api/neighborhoods/?format=json
    parser.add_argument('-w','--overwrite',dest='overwrite',help='Overwrite existing files',action='store_true')
    parser.add_argument('-i','--id',dest='uuid',help='Neighborhood UUID (if given, only this neighborhood is downloaded)')
    args = parser.parse_args()

    # set vars
    verbose = args.verbose
    if verbose:
        print(' ')
    outPath = args.outdir
    url = args.url
    overwrite = args.overwrite
    uuid = args.uuid

    # grab json data from url
    if verbose:
        print('Getting json data from %s' % url)
    data = get_jsonparsed_data(url)

    # json returns 20 at a time so fetch new results when we're done
    while data:
        for city in data['results']:
            print('Processing: %s' % city['label'])

            targetPath = os.path.join(outPath,city['state_abbrev'],city['name'])
            targetFile = os.path.join(targetPath,'neighborhood_census_blocks.zip')
            # check file if overwrite is not active
            if os.path.isfile(targetFile) and not overwrite:
                print('  %s already exists, skipping' % targetFile)
                continue
            # create target directory if it doesn't exist
            if not os.path.isdir(targetPath):
                os.makedirs(targetPath)

            # download file or copy, depending on args
            if download:
                jobUrl = 'https://bna.peopleforbikes.org/api/analysis_jobs/' \
                            + city['last_job'] \
                            + '/results/?format=json'
                if verbose:
                    print('Downloading job data from %s' % jobUrl)
                try:
                    job = get_jsonparsed_data(jobUrl)
                except HTTPError, e:
                    print "HTTP Error:", e.code, url
                    continue
                except URLError, e:
                    print "URL Error:", e.reason, url
                    continue

                fileUrl = job['census_blocks_url']
                try:
                    f = urlopen(fileUrl)
                    if verbose:
                        print('Downloading file from %s' % fileUrl)

                    # Open our local file for writing
                    with open(targetFile, "wb") as local_file:
                        local_file.write(f.read())

                #handle errors
                except HTTPError, e:
                    print "HTTP Error:", e.code, url
                    continue
                except URLError, e:
                    print "URL Error:", e.reason, url
                    continue

            else:
                sourcePath = os.path.join(inPath,city['last_job'])

                # check to make sure source directory exists
                if not os.path.isdir(sourcePath):
                    print('    %s does not exist' % sourcePath)
                    break

                # copy file
                if verbose:
                    print('Copying neighborhood_census_blocks.zip from %s to %s' % (sourcePath,targetPath))
                shutil.copyfile(
                    os.path.join(sourcePath,'neighborhood_census_blocks.zip'),
                    os.path.join(targetFile)
                )

        if data['next'] is None:
            break
        else:
            data = get_jsonparsed_data(data['next'])

if __name__ == "__main__":
    main(sys.argv[1:])
