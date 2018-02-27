#!/bin/bash

#############################################################
## Add missing BNA category scores to shapefile and
## save to new location
##  Inputs:
##      input file     -> $1
##      output file    -> $2
#############################################################

cd "$(dirname "$0")"


# check that input file exists
if [ ! -e ${1} ]; then
    echo "${1} is not a file"
    exit 1
fi
echo "From ${1} to ${2}"

# input
indir=`dirname ${1}`
if [[ ${1} == *.shp ]]; then
    infile=`basename ${1} .shp`
    inext="shp"
elif [[ ${1} == *.zip ]]; then
    infile=`basename ${1} .zip`
    inext="zip"
else
    echo "Cannot process ${1}"
    exit 1
fi

# output
outdir=`dirname ${2}`
if [[ ${2} == *.shp ]]; then
    outfile=`basename ${2} .shp`
    outext="shp"
elif [[ ${2} == *.zip ]]; then
    outfile=`basename ${2} .zip`
    outext="zip"
else
    echo "Cannot output to ${2}"
    exit 1
fi

# prepare output shp
if [[ inext == "shp" ]]; then
    if [[ outext == "shp" ]]; then
        for f in ${indir}/${infile}.*; do cp -- "$f" "${outdir}/${outfile}.${f##*.}"; done
        file="${outdir}/${outfile}.shp"
    else
        tempdir=`mktemp -d`
        for f in ${indir}/${infile}.*; do cp -- "$f" "${tempdir}/${outfile}.${f##*.}"; done
        file="${tempdir}/${outfile}.shp"
    fi
else
    if [[ outext == "shp" ]]; then
        unzip ${1} -d ${outdir}
        file="${outdir}/${outfile}.shp"
    else
        tempdir=`mktemp -d`
        unzip ${1} -d ${tempdir}
        file="${tempdir}/${outfile}.shp"
    fi
fi

# add fields to shapefile
ogrinfo ${file} \
    -sql "ALTER TABLE ${outfile} ADD COLUMN \"CORESVCS\" float"
ogrinfo ${file} \
    -sql "ALTER TABLE ${outfile} ADD COLUMN \"OPPRTNTY\" float"
ogrinfo ${file} \
    -sql "ALTER TABLE ${outfile} ADD COLUMN \"RECREATION\" float"

################################
# calculate scores
################################
# CORESVCS
ogrinfo ${file} \
    -dialect SQLite \
    -sql "  UPDATE  ${outfile}
            SET     \"CORESVCS\" = (
                        20 * COALESCE(\"DOCTORS_SC\",0) +
                        10 * COALESCE(\"DENTISTS_S\",0) +
                        20 * COALESCE(\"HOSPITA_02\",0) +
                        10 * COALESCE(\"PHARMAC_02\",0) +
                        25 * COALESCE(\"SUPERMA_02\",0) +
                        15 * COALESCE(\"SOCIAL__02\",0)
                    ) / (
                        20 * (CASE WHEN COALESCE(\"DOCTORS_HI\",0) = 0 THEN 0 ELSE 1 END) +
                        10 * (CASE WHEN COALESCE(\"DENTISTS_H\",0) = 0 THEN 0 ELSE 1 END) +
                        20 * (CASE WHEN COALESCE(\"HOSPITA_01\",0) = 0 THEN 0 ELSE 1 END) +
                        10 * (CASE WHEN COALESCE(\"PHARMAC_01\",0) = 0 THEN 0 ELSE 1 END) +
                        25 * (CASE WHEN COALESCE(\"SUPERMA_01\",0) = 0 THEN 0 ELSE 1 END) +
                        15 * (CASE WHEN COALESCE(\"SOCIAL__01\",0) = 0 THEN 0 ELSE 1 END)
                    )
            WHERE   \"OVERALL_SC\" IS NOT NULL
            AND     COALESCE(\"DOCTORS_HI\",0) + COALESCE(\"DENTISTS_H\",0)
                    + COALESCE(\"HOSPITA_01\",0) + COALESCE(\"PHARMAC_01\",0)
                    + COALESCE(\"SUPERMA_01\",0) + COALESCE(\"SOCIAL__01\",0) > 0"

# OPPRTNTY
ogrinfo ${file} \
    -dialect SQLite \
    -sql "  UPDATE  ${outfile}
            SET     \"OPPRTNTY\" = (
                        35 * COALESCE(\"EMP_SCORE\",0) +
                        35 * COALESCE(\"SCHOOLS_SC\",0) +
                        10 * COALESCE(\"COLLEGES_S\",0) +
                        20 * COALESCE(\"UNIVERS_02\",0)
                    ) / (
                        35 * (CASE WHEN COALESCE(\"EMP_HIGH_S\",0) = 0 THEN 0 ELSE 1 END) +
                        35 * (CASE WHEN COALESCE(\"SCHOOLS_HI\",0) = 0 THEN 0 ELSE 1 END) +
                        10 * (CASE WHEN COALESCE(\"COLLEGES_H\",0) = 0 THEN 0 ELSE 1 END) +
                        20 * (CASE WHEN COALESCE(\"UNIVERS_02\",0) = 0 THEN 0 ELSE 1 END)
                    )
            WHERE   \"OVERALL_SC\" IS NOT NULL
            AND     COALESCE(\"EMP_HIGH_S\",0) + COALESCE(\"SCHOOLS_HI\",0)
                    + COALESCE(\"COLLEGES_H\",0) + COALESCE(\"UNIVERS_02\",0) > 0"

# RECREATION
ogrinfo ${file} \
    -dialect SQLite \
    -sql "  UPDATE  ${outfile}
            SET     \"RECREATION\" = (
                        40 * COALESCE(\"PARKS_SCOR\",0) +
                        35 * COALESCE(\"TRAILS_SCO\",0) +
                        25 * COALESCE(\"COMMUNI_02\",0)
                    ) / (
                        40 * (CASE WHEN COALESCE(\"PARKS_HIGH\",0) = 0 THEN 0 ELSE 1 END) +
                        35 * (CASE WHEN COALESCE(\"TRAILS_HIG\",0) = 0 THEN 0 ELSE 1 END) +
                        25 * (CASE WHEN COALESCE(\"COMMUNI_01\",0) = 0 THEN 0 ELSE 1 END)
                    )
            WHERE   \"OVERALL_SC\" IS NOT NULL
            AND     COALESCE(\"PARKS_HIGH\",0) + COALESCE(\"TRAILS_HIG\",0)
                    + COALESCE(\"COMMUNI_01\",0) > 0"

# rezip if necessary
if [[ ${outext} == ".zip" ]]; then
    zip -r ${2} ${tempdir}/${outfile}.*
fi
