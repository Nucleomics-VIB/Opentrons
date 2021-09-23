<img src="https://raw.githubusercontent.com/Nucleomics-VIB/Opentrons/main/pictures/NC_logo.png" width=150px>

# OT2MakeProtocol

A standalone bash **script OT_inject_params.sh** takes a protocol template and a yaml file defining the protocol variables (+ accessorily a CVS file with user data) and combines them into a ready to run Opentron-2 protocol.

A test dataset is provided as a zip archive to check the functionality of the code.

*Note:* For our convenience, I added some php wrapper files in a folder inside our web-server (apache) cgi-bin folder (edit code accordingly). The bash script should be made executable and owned by the apache user. These details are not developed here as they are known by experienced web-coding users.

<img src="https://raw.githubusercontent.com/Nucleomics-VIB/Opentrons/main/pictures/OT2MakeProtocol.png" width=900px>

v1.0, 2021_09_21