#! /usr/bin/python

##################################
# Adds missing category scores
# to zipped census block shapefile
# and zips it back up to given
# location
##################################
import argparse
import tempfile
import zipfile
import geopandas
import numpy as np
import sys
import os
import shutil


def main(argv):
    parser = argparse.ArgumentParser(description='Add missing category scores to BNA census block outputs')
    parser.add_argument('infile',help='Input file')
    parser.add_argument('outfile',help='Output file')
    parser.add_argument('-v',dest='verbose',action='store_true',help='Verbose mode')
    parser.add_argument('-w','--overwrite',dest='overwrite',help='Overwrite existing files',action='store_true')
    args = parser.parse_args()

    # set vars
    verbose = args.verbose
    if verbose:
        print(' ')
    inFile = args.infile
    outFile = args.outfile
    overwrite = args.overwrite

    # quit if outfile exists and overwrite is not set
    if verbose:
        print('  Checking %s doesn\'t exist' % outFile)
    if os.path.isfile(outFile) and not overwrite:
        print('  %s already exists, skipping' % outFile)
        sys.exit()

    # create temp directory and unzip the shapefile to it
    if verbose:
        print('  unzipping')
    tempPath = tempfile.mkdtemp()
    zip_ref = zipfile.ZipFile(inFile,'r')
    zip_ref.extractall(tempPath)
    zip_ref.close()
    tempFile = os.path.join(tempPath,'neighborhood_census_blocks.shp')

    # open the shapefile
    if verbose:
        print('  opening shapefile')
    blocks = geopandas.read_file(tempFile)

    # add the core services score
    if verbose:
        print('  calculating core services score')
    blocks['CORESVCS'] = np.where(
        blocks['DOCTORS_HI'] + blocks['DENTISTS_H'] + blocks['HOSPITA_01'] \
            + blocks['PHARMAC_01'] + blocks['SUPERMA_01'] + blocks['SOCIAL__01'] == 0,
        0,
        1 \
            * (20 * blocks['DOCTORS_SC'] \
                + 10 * blocks['DENTISTS_S'] \
                + 20 * blocks['HOSPITA_02'] \
                + 10 * blocks['PHARMAC_02'] \
                + 25 * blocks['SUPERMA_02'] \
                + 15 * blocks['SOCIAL__02']) \
            / (20 * np.where(blocks['DOCTORS_HI'] == 0,0,1) \
                + 10 * np.where(blocks['DENTISTS_H'] == 0,0,1) \
                + 20 * np.where(blocks['HOSPITA_01'] == 0,0,1) \
                + 10 * np.where(blocks['PHARMAC_01'] == 0,0,1) \
                + 25 * np.where(blocks['SUPERMA_01'] == 0,0,1) \
                + 15 * np.where(blocks['SOCIAL__01'] == 0,0,1) \
            )
    )

    # add the opportunity score
    if verbose:
        print('  calculating opportunity score')
    blocks['OPPRTNTY'] = np.where(
        blocks['EMP_HIGH_S'] + blocks['SCHOOLS_HI'] + blocks['COLLEGES_H'] \
            + blocks['UNIVERS_01'] == 0,
        0,
        1 \
            * (35 * blocks['EMP_SCORE'] \
                + 35 * blocks['SCHOOLS_SC'] \
                + 10 * blocks['COLLEGES_S'] \
                + 20 * blocks['UNIVERS_02']) \
            / (35 * np.where(blocks['EMP_HIGH_S'] == 0,0,1) \
                + 35 * np.where(blocks['SCHOOLS_HI'] == 0,0,1) \
                + 10 * np.where(blocks['COLLEGES_H'] == 0,0,1) \
                + 20 * np.where(blocks['UNIVERS_01'] == 0,0,1) \
            )
    )

    # add the recreation score
    if verbose:
        print('  calculating recreation score')
    blocks['RECREATION'] = np.where(
        blocks['PARKS_HIGH'] + blocks['TRAILS_HIG'] + blocks['COMMUNI_01'] == 0,
        0,
        1 \
            * (40 * blocks['PARKS_SCOR'] \
                + 35 * blocks['TRAILS_SCO'] \
                + 25 * blocks['COMMUNI_02']) \
            / (40 * np.where(blocks['PARKS_HIGH'] == 0,0,1) \
                + 35 * np.where(blocks['TRAILS_HIG'] == 0,0,1) \
                + 25 * np.where(blocks['COMMUNI_01'] == 0,0,1) \
            )
    )

    # fix conversion from zeros to nulls
    blocks['POP_SCORE'] = np.where(blocks['POP_HIGH_S'] == 0, np.nan, blocks['POP_SCORE'])
    blocks['EMP_SCORE'] = np.where(blocks['EMP_HIGH_S'] == 0, np.nan, blocks['EMP_SCORE'])
    blocks['SCHOOLS_SC'] = np.where(blocks['SCHOOLS_HI'] == 0, np.nan, blocks['SCHOOLS_SC'])
    blocks['UNIVERS_02'] = np.where(blocks['UNIVERS_01'] == 0, np.nan, blocks['UNIVERS_02'])
    blocks['COLLEGES_S'] = np.where(blocks['COLLEGES_H'] == 0, np.nan, blocks['COLLEGES_S'])
    blocks['DOCTORS_SC'] = np.where(blocks['DOCTORS_HI'] == 0, np.nan, blocks['DOCTORS_SC'])
    blocks['DENTISTS_S'] = np.where(blocks['DENTISTS_H'] == 0, np.nan, blocks['DENTISTS_S'])
    blocks['HOSPITA_02'] = np.where(blocks['HOSPITA_01'] == 0, np.nan, blocks['HOSPITA_02'])
    blocks['PHARMAC_02'] = np.where(blocks['PHARMAC_01'] == 0, np.nan, blocks['PHARMAC_02'])
    blocks['RETAIL_SCO'] = np.where(blocks['RETAIL_HIG'] == 0, np.nan, blocks['RETAIL_SCO'])
    blocks['SUPERMA_02'] = np.where(blocks['SUPERMA_01'] == 0, np.nan, blocks['SUPERMA_02'])
    blocks['SOCIAL__02'] = np.where(blocks['SOCIAL__01'] == 0, np.nan, blocks['SOCIAL__02'])
    blocks['PARKS_SCOR'] = np.where(blocks['PARKS_HIGH'] == 0, np.nan, blocks['PARKS_SCOR'])
    blocks['TRAILS_SCO'] = np.where(blocks['TRAILS_HIG'] == 0, np.nan, blocks['TRAILS_SCO'])
    blocks['COMMUNI_02'] = np.where(blocks['COMMUNI_01'] == 0, np.nan, blocks['COMMUNI_02'])
    blocks['TRANSIT_SC'] = np.where(blocks['TRANSIT_HI'] == 0, np.nan, blocks['TRANSIT_SC'])

    # save the result
    if verbose:
        print('  saving')
    blocks.to_file(outFile)

    # clean up
    shutil.rmtree(tempPath)


if __name__ == "__main__":
    main(sys.argv[1:])
