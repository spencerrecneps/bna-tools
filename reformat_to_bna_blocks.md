# Data preparation for international BNA runs

This page describes the process of taking a shapefile dataset and preparing it
to be used as an input in the BNA for locations where the BNA can't
automatically download census data. We will cover two datasets needed as BNA
inputs:

- Population
- Jobs

This process can be followed for running the BNA in locations outside of the
United States (or within the US but where the US Census does not maintain the
full complement of census datasets, such as Puerto Rico).

There are three main steps to follow:

1. Manually develop population and employment data
2. Transform the data developed in Step 1 into a BNA-ready format
3. Run the BNA with the datasets prepared in Step 2

## Manually developing data

There's no single right way to prepare population and employment data for BNA.
In some locations there may be a census-equivalent dataset that can be easily
adapted for BNA. For example, Canadian cities have postal-zone level population
data at geographies that are very similar to US census blocks. However, the
Canadian government does not make this data public out of concerns for privacy.
It is possible that a local agency can provide this.

In the absence of pre-existing block-sized geographies it's necessary to create
polygon features that are suitable. There are tools available for this in
ArcMap, QGIS, and other GIS platforms. One strategy involves using street
network data to define block boundaries.

Once block features have been created, it is necessary to assign population and
employment data to each feature. This can be done by assuming a uniform
distribution throughout features in an aggregated source dataset.

For example, assume you can only find US Census Block Group data for a location and you have created "block" features using the street centerlines as boundaries. Now assume a block group has a population of 120, and one of your "blocks" covers 20% of the block group's area. A uniform distribution would result in 24 people being assigned to your "block" (120 * 20% = 24).

The same process can be followed for employment data.

## Transforming data into a BNA-ready format

The reformat_to_bna_blocks.py script in this repository takes a polygon dataset
with population figures (and optionally, employment numbers) and transforms it
into the format expected by the BNA. The BNA was developed to use US Census
Block data and relies on the standardized naming of the US Census. The reformat
script applies these conventions seamlessly for you.

The script takes three required inputs:

- path to an input shapefile
- location to save an output shapefile
- name of a column in the input shapefile that holds population data

The script can also accept an input indicating the name of a column holding employment data but this is not required. In its absence, no employment outputs are created.

More information on how the script works is available by running:

`python reformat_to_bna_blocks.py --help`

Example:

```
python reformat_to_bna_blocks.py \
    /path/to/input/shapefile.shp \
    /path/to/save/output/shapefile.shp \
    pop_column \
    -e emp_column
```

## Running the BNA with BNA-formatted inputs

The population and employment data created in the above steps can be use in the
same way as if the datasets had come directly from the US Census. Thus, you
would plug them in at the same point as you would for pre-downloaded Census
datasets.
