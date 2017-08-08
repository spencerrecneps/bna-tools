#!/bin/bash

#############################################################
## Finds all shapefiles in the given directory and all child
## directories and converts shapefile attributes to xls.
## Args:    1) Directory to process
#############################################################

fullpath=`readlink -f $1`

# grab all shps and iterate over them
for f in `find ${fullpath} -type f -name '*.shp'`; do
    d=`dirname $f`
    parent=${d##*/}
    of="$d/${parent}.xlsx"
    echo "Processing $d"
    ./shp2xls.sh "${f}" "$of"
done
