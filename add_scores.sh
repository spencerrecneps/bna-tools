#!/bin/bash

#############################################################
## Add missing BNA category scores to shapefile and
## save to new location
##  Inputs:
##      input shapefile     -> $1
#############################################################

cd "$(dirname "$0")"

file="${1}"

# check that input file exists
if [ ! -e "${file}" ]; then
    echo "${file} is not a file"
    exit 1
fi

if [[ "${file}" == *.shp ]]; then
    tablename=`basename "${file}" .shp`
elif [[ "${file}" == *.zip ]]; then
    tempdir=`mktemp -d`
    unzip ${file} -d ${tempdir}
    tablename=`basename ${file} .zip`
    file="${tempdir}/${tablename}.shp"
else
fi

# add fields to shapefile
ogrinfo "${file}" \
    -sql "ALTER TABLE ${tablename} ADD COLUMN \"CORESVCS\" float"
ogrinfo "${file}" \
    -sql "ALTER TABLE ${tablename} ADD COLUMN \"OPPRTNTY\" float"
ogrinfo "${file}" \
    -sql "ALTER TABLE ${tablename} ADD COLUMN \"RECREATION\" float"

################################
# calculate scores
################################
# CORESVCS
ogrinfo "${file}" \
    -dialect SQLite \
    -sql "  UPDATE  ${tablename}
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
ogrinfo "${file}" \
    -dialect SQLite \
    -sql "  UPDATE  ${tablename}
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
ogrinfo "${file}" \
    -dialect SQLite \
    -sql "  UPDATE  ${tablename}
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
if [[ "${1}" == *.zip ]]; then
    zip -r ${1} ${tempdir}/${tablename}.*
fi
