#!/usr/bin/env bash

# scriptname: OT_inject_params.sh
# A script to replace placeholders in an Opentrons protocol template
# placeholders are filled from a yaml file for single variables
# when the yaml file contains a CSV entry: CSV data is injected on top of the script
#
# Stephane Plaisance VIB-NC September-17-2021 v1.0
# requires: sed, yq (https://github.com/mikefarah/yq/ for yaml parsing)
#
# visit our Git: https://github.com/Nucleomics-VIB

version="1.1, 2021-09-20"
datetag=$(date '+%Y-%m-%d')

usage='# Usage: OT_inject_params.sh
#    -i <opentrons protocol template>
#    -o <output file name (default to "OT2_protocol.py")
#    -y <yaml parameter file with variables to inject
#    -h <this help message>
# version: '${version}

while getopts "i:y:o:h" opt; do
  case $opt in
    i) TEMPLATE=${OPTARG} ;;
    y) YAML=${OPTARG} ;;
    o) opt_out=${OPTARG} ;;
    h | *) echo "${usage}" >&2; exit 0 ;;
  esac
done

# check dependencies
eval hash yq 2>/dev/null || ( echo "# yq (https://github.com/mikefarah/yq/) is not installed or not in PATH"; exit 1 )

# check if template & yaml are provided
if [ -z "${TEMPLATE}" ]
then
   echo "# provide an OT2 protocol template file with placeholders"
   echo "${usage}"
   exit 1
fi

if [ -z "${YAML}" ]
then
   echo "# provide a yaml file with variables to replace th etemplate placeholders"
   echo "${usage}"
   exit 1
fi

# define output file path and name and create it from the template
PROTOCOL=${opt_out:-"OT2_protocol.py"}
cp "${TEMPLATE}" "${PROTOCOL}" || \
  ( echo "# input file could not be copied to output file"; exit 1 ; )

#######################
## parameter functions

function list_params() {
# $1 is ${YAML}
# list of yaml parameters
eval yq eval '.params*' "$1" | sed 's/:.*//g'
}

function eval_params() {
# $1 is ${YAML}
# set yaml parameter values to corresponding variables
eval $(yq eval '.params*' "$1" | sed 's/: /=/g')
}

function show_params() {
# debug: show parameter values at placeholders
for PARAM in "${PARAMS[@]}"
do
  echo "# ${PARAM} has now value: ${!PARAM}"
done
}

function inject_params() {
# inject parameter values at placeholders
for PARAM in "${PARAMS[@]}";
do
  # sed -i should be followed by '' under OSX
  if [[ "$OSTYPE" =~ ^[dD]arwin* ]]; then
    sed -i '' "s/<${PARAM}>/${!PARAM}/" "${PROTOCOL}"
  else
    sed -i "s/<${PARAM}>/${!PARAM}/" "${PROTOCOL}"
fi
done
}

function inject_edit_date() {
# inject edit_version at placeholder
# sed -i should be followed by '' under OSX
if [[ "$OSTYPE" =~ ^[dD]arwin* ]]; then
  sed -i '' "s/<edit_date>/${datetag}/" "${PROTOCOL}"
else
  sed -i "s/<edit_date>/${datetag}/" "${PROTOCOL}"
fi
}

#######################
## CSV functions

function get_csv_placeholder() {
# $1 is ${YAML}
# set yaml csv placeholder to variable
yq eval '.csv' "$1" | sed 's/:.*//g'
}

function get_csv_filename() {
# $1 is ${YAML}
# set yaml csv file name to variable
yq eval '.csv' "$1" | sed 's/.*: //g'
}

function parse_csv() {
cat "${1}" | tr -d '\r' | perl -0p -e "s/\R*\z//g" | perl -p -e 's/\n/\\\\n/'
}

function print_csv() {
# $1 is ${YAML}
# print out CSV data
CSVPLACEHOLDER=$(get_csv_placeholder "$1")
CSVFILENAME=$(get_csv_filename "$1" | sed 's/\"//g')
CSVDATA=$(parse_csv "${CSVFILENAME}")
echo "# ${CSVPLACEHOLDER} has content: ${CSVDATA}"
}

function inject_csv() {
# $1 is ${YAML}
# inject CSV data at placeholder
CSVPLACEHOLDER=$(get_csv_placeholder "$1")
CSVFILENAME=$(get_csv_filename "$1" | sed 's/\"//g')
CSVDATA=$(parse_csv "${CSVFILENAME}")
# sed -i should be followed by '' under OSX
if [[ "$OSTYPE" =~ ^[dD]arwin* ]]; then
  sed -i '' "s/<${CSVPLACEHOLDER}>/$(echo ${CSVDATA} | sed -e 's/\\/\\\\/'g)/" "${PROTOCOL}"
else
  sed -i "s/<${CSVPLACEHOLDER}>/$(echo ${CSVDATA} | sed -e 's/\\/\\\\/'g)/" "${PROTOCOL}"
fi
}


############## MAIN ##############

# create global array to store parameters
declare -a PARAMS
PARAMS=()

# read yaml for PARAMS
PARAMS=( $(list_params "${YAML}") )
eval_params "${YAML}"
show_params "${YAML}"

# inject parameters from yaml
inject_params "${YAML}"

# inject edit date
inject_edit_date

# check if CSV info is present in yaml
hascsv=$(get_csv_filename "${YAML}")
if [ -n "${hascsv}" ]; then

  # inject CSV data if CSV is linked in yaml
  if [ -z "${hascsv}" ]
    then
     echo "# the CSV file linked in the config file was not found"
     echo "${usage}"
     exit 1
  fi

  # debug print_csv ${YAML}
  echo "# CSV file ${hascsv} found and injected"
  print_csv "${YAML}"
  inject_csv "${YAML}"

fi

exit 0


############################### EXAMPLE ##############################
# OT_inject_csv.sh -i template.py -y config.yaml -o my_protocol.py
#
# ######### template.py #########
# def get_values(*names):
#     import json
#     _all_values = json.loads("""{
#         "uploaded_csv":"<uploaded_csv>",
#         "min_vol":"<min_vol>",
#         "sp_type":"<sp_type>",
#         "dp_type":"<dp_type>"
#         }""")
#     return [_all_values[n] for n in names]
#
# ######### config.yaml #########
# params:
#   min_vol: 2.5
#   sp_type: "biorad_96_wellplate_200ul_pcr"
#   dp_type: "biorad_96_wellplate_200ul_pcr"
# csv:
#   uploaded_csv: "data.csv"
#
# ######### data.csv (linked in yaml above) #########
# source_plate,source_well,source_volume,dil_factor
# 1,A1,2.5,1
# 1,A8,5,1
# 2,B4,2.5,10
# 3,F6,2.5,80
# 4,H8,20,50
#
# ######## my_protocol.py #########
# def get_values(*names):
#     import json
#     _all_values = json.loads("""{
#         "uploaded_csv":"source_plate,source_well,source_volume,dil_factor\n1,A1,2.5,1\n1,A8,5,1\n2,B4,2.5,10\n3,F6,2.5,80\n4,H8,20,50",
#         "min_vol":"2.5",
#         "sp_type":"biorad_96_wellplate_200ul_pcr",
#         "dp_type":"biorad_96_wellplate_200ul_pcr"
#         }""")
#     return [_all_values[n] for n in names]
#

