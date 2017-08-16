#! /usr/bin/python

##################################
# Download BNA results and
# optionally organize by state and
# city.
##################################
import sys
import argparse
import os
import shutil
import json
import re
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
    parser.add_argument(help='Input directory',dest='indir')
    parser.add_argument('-v',dest='verbose',action='store_true',help='Verbose mode')
    parser.add_argument('-u','--url',dest='url',help='URL to grab JSON neighborhood data from',required=True)
    parser.add_argument('-i','--id',dest='uuid',help='Neighborhood UUID (if given, only this neighborhood is uploaded)')
    args = parser.parse_args()

    # set vars
    verbose = args.verbose
    if verbose:
        print(' ')
    inPath = args.indir
    url = args.url
    uuid = args.uuid

    # grab json data from url
    if verbose:
        print('Getting json data from %s' % url)
    data = get_jsonparsed_data(url)

    # json returns 20 at a time so fetch new results when we're done
    while data:
        for city in data['results']:
            if uuid is not None and uuid != city['uuid']:
                continue

            print('Processing: %s' % city['label'])

            localPath = os.path.join(inPath,city['state_abbrev'],city['name'],'neighborhood_census_blocks')
            localFile = os.path.join(localPath,'neighborhood_census_blocks.zip')

            # make sure file exists at assumed path
            if verbose:
                print('Checking file at %s' % localFile)
            if not os.path.isfile(localFile):
                print('----> !!!!! No file at %s' % localFile)
                continue

            # save target s3 path as s3Url
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
            s3url = re.sub('https://s3.amazonaws.com/','s3://',fileUrl)

            # upload file
            if verbose:
                print('  Uploading %s to %s' % (localFile,s3url))
            os.system('aws s3 cp %s %s' % (localFile,s3url))

        if data['next'] is None:
            break
        else:
            data = get_jsonparsed_data(data['next'])

if __name__ == "__main__":
    main(sys.argv[1:])
