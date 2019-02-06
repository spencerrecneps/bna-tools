#! /usr/bin/python

# this script copies an input shapefile to an output location and reformats
# the attributes to conform with the expectations of a BNA input


import argparse
import sys, os, random, csv
import geopandas as gpd

BNA_POPULATION = "POP10"
BNA_EMPLOYMENT = "S000"
BNA_BLOCKID = "BLOCKID10"


def main(argv):
    parser = argparse.ArgumentParser(description="Convert an input shapefile into a BNA-ready format")
    parser.add_argument("input_shapefile",help="Input shapefile")
    parser.add_argument("output_shapefile",help="Output shapefile")
    parser.add_argument("population_column",help="Name of the column with population data")
    parser.add_argument("-e",dest="employment_column",help="Name of the column with employment data (if omitted employment is left out of the output)",default="")
    parser.add_argument("-o",dest="overwrite",action="store_true",help="Overwrite an existing shapefile (if one exists)",default=False)
    parser.add_argument("--crs",dest="crs",help="Coordinate system for the output")
    args = parser.parse_args()

    # set vars
    overwrite = args.overwrite
    input_shapefile = args.input_shapefile
    output_shapefile = args.output_shapefile
    output_file_name = os.path.splitext(output_shapefile)[0]
    output_jobs_main_csv = output_file_name+"_main.csv"
    output_jobs_aux_csv = output_file_name+"_aux.csv"
    population_column = args.population_column
    if args.employment_column == "":
        employment_column = None
    else:
        employment_column = args.employment_column
    if args.crs:
        crs = args.crs
    else:
        crs = None

    # check inputs
    if not os.path.isfile(input_shapefile):
        raise ValueError("File {} not found".format(input_shapefile))
    if not overwrite and os.path.isfile(output_shapefile):
        raise ValueError("File {} already exists (hint: use the -o flag to overwrite)".format(output_shapefile))
    if not overwrite and employment_column:
        for f in [output_jobs_main_csv,output_jobs_aux_csv]:
            if os.path.isfile(f):
                raise ValueError("File {} already exists (hint: use the -o flag to overwrite)".format(f))
    try:
        int(crs)
    except:
        raise ValueError("Given CRS \"{}\" can't be processed".format(crs))

    # load input shapefile and check for columns
    gdf = gpd.read_file(input_shapefile)
    if not population_column in gdf.columns:
        raise ValueError("Column \"{}\" not found in {}".format(population_column,input_shapefile))
    if employment_column and not employment_column in gdf.columns:
        raise ValueError("Column \"{}\" not found in {}".format(employment_column,input_shapefile))

    # (re)projection
    if not crs:
        crs = gdf.crs
    else:
        print("Reprojecting to SRID {}".format(crs))
        crs = {"init":"epsg:{:d}".format(int(crs))}
        gdf = gdf.to_crs(crs)

    # drop extra columns
    keep_cols = [gdf.geometry.name,population_column]
    if employment_column:
        keep_cols.append(employment_column)
    gdf = gpd.GeoDataFrame(gdf[keep_cols])

    # rename columns
    print("Renaming columns")
    gdf = gdf.rename(columns={population_column:BNA_POPULATION})
    if employment_column:
        gdf = gdf.rename(columns={employment_column:BNA_EMPLOYMENT})

    # add block ids
    print("Creating {}".format(BNA_BLOCKID))
    ids = set()
    def assign_ids(row):
        i = int(random.random()*1000000000000)
        if i in ids:
            return assign_ids()
        else:
            ids.add(i)
            return "{:015d}".format(i)
    gdf[BNA_BLOCKID] = gdf.apply(assign_ids,axis=1)

    # save population to output
    gdf.crs = crs
    gdf.to_file(output_shapefile)

    # create jobs
    print(employment_column)
    print(output_jobs_main_csv)
    print(output_jobs_aux_csv)
    if employment_column:
        # gdf = gdf.drop(columns=[BNA_POPULATION,gdf.geometry.name])
        gdf["w_geocode"] = gdf[BNA_BLOCKID].copy()
        gdf["h_geocode"] = gdf[BNA_BLOCKID].copy()
        gdf = gdf[["w_geocode","h_geocode",BNA_EMPLOYMENT]]
        gdf["SA01"] = 0
        gdf["SA02"] = 0
        gdf["SA03"] = 0
        gdf["SE01"] = 0
        gdf["SE02"] = 0
        gdf["SE03"] = 0
        gdf["SI01"] = 0
        gdf["SI02"] = 0
        gdf["SI03"] = 0
        gdf["createdate"] = " "

        gdf.to_csv(output_jobs_main_csv,index=False,quoting=csv.QUOTE_NONNUMERIC)

        gdf[BNA_EMPLOYMENT] = 0
        gdf.to_csv(output_jobs_aux_csv,index=False,quoting=csv.QUOTE_NONNUMERIC)


if __name__ == "__main__":
    main(sys.argv[1:])
