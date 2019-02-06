#! /usr/bin/python

# this script copies an input shapefile to an output location and reformats
# the attributes to conform with the expectations of a BNA input


import argparse
import sys, os
import geopandas as gpd

BNA_POPULATION = "POP10"
BNA_EMPLOYMENT = "EMP10"
BNA_BLOCKID = "BLOCKID10"


def main(argv):
    parser = argparse.ArgumentParser(description='Convert an input shapefile into a BNA-ready format')
    parser.add_argument('input_shapefile',help='Input shapefile')
    parser.add_argument('output_shapefile',help='Output shapefile')
    parser.add_argument('population_column',help='Name of the column with population data')
    parser.add_argument('-e',dest='employment_column',help='Name of the column with employment data (if omitted employment is left out of the output)',default="")
    parser.add_argument('-o',dest='overwrite',action='store_true',help='Overwrite an existing shapefile (if one exists)',default=False)
    args = parser.parse_args()

    # set vars
    overwrite = args.overwrite
    input_shapefile = args.input_shapefile
    output_shapefile = args.output_shapefile
    population_column = args.population_column
    if args.employment_column == "":
        employment_column = None
    else:
        employment_column = args.employment_column

    # check inputs
    if not os.path.isfile(input_shapefile):
        raise ValueError("File {} not found".format(input_shapefile))
    if not overwrite and os.path.isfile(output_shapefile):
        raise ValueError("File {} already exists (hint: use the -o flag to overwrite)".format(output_shapefile))

    # load input shapefile and check for columns
    gdf = gpd.read_file(input_shapefile)
    if not population_column in gdf.columns:
        raise ValueError("Column {} not found in {}".format(population_column,input_shapefile))
    if employment_column and not employment_column in gdf.columns:
        raise ValueError("Column {} not found in {}".format(employment_column,input_shapefile))

    # drop extra columns
    keep_cols = [gdf.geometry,population_column]
    if employment_column:
        keep_cols.append(employment_column)
    gdf = gpd.GeoDataFrame(gdf[keep_cols])

    # rename columns
    gdf = gdf.rename(columns={population_column:BNA_POPULATION})
    if employment_column:
        gdf = gdf.rename(columns={employment_column:BNA_EMPLOYMENT})

    # add block ids


    # save to output
    gdf.to_file(output_shapefile)


if __name__ == "__main__":
    main(sys.argv[1:])
