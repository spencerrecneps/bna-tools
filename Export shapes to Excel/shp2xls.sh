#!/bin/bash

#############################################################
## Exports a shapefile's attribute table to Excel
## Args:    1) File path to input shapefile
##          2) File path to output xls
#############################################################

# make temporary directory
tempdir=`mktemp -d`

# export shapefile to temporary directory
ogr2ogr -f "CSV" ${tempdir}/convert.csv $1

# convert to excel and save in final location
unoconv --format xlsx ${tempdir}/convert.csv

# copy to new location
cp ${tempdir}/convert.xlsx $2

# cleanup
rm -rf ${tempdir}
