#!/bin/bash

#############################################################
## Processing instructions adding category scores
## to all BNA census blocks
#############################################################

cd "$(dirname "$0")"

# grab all zips and iterate over them
for f in `find . -type f -name '*.zip'`; do
    echo "Processing $f"
    d=`dirname $f`
    of="$d/neighborhood_census_blocks_catscores.shp"
    ./add_scores.py "${f}" "$of" -v -w
done
