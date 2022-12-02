# NC_dilute_96w_plate

### Authors
[VIB Nucleomics Core](https://www.nucleomics.be)

## Categories
* General method
	* sample dilution
	* concentration normalization
	
## Description

This protocol normalizes samples from a 96 well sample plate to a destination 96 well plate.
When dilution is less than max_dil (20), the samples are first diluted _sqrt(dil)_ times in a dilution plate then a volume is taken and diluted again _sqrt(dil)_ times to the destination plate.

The program computes volumes based on the provided dilution factors in order to:

* never pipet less than _min_vol_ (2.5) microliters
* minimize the use of the start material
* distribute at least _min_fin_ (20) microliters in each well of the destination plate


### IMPORTANT NOTE ###

The CSV data should be saved as a comma-separated text file (!! _Windows user_ : ',' => not ';' !!) with '_Position_' being well addresses (A1) and all '_Dilution_' ('Value') given with a dot => '.' as decimal separator as in the following example

```
Position,Dilution
A1,1.0
A2,18.3
A3,80.5
...
```

* _A1,1.0_ will lead to transfer of _min_fin_ (20) microliters of pure sample to the destination plate
* _A2,18.3_ will lead to direct 18.3x dilution of the sample in the destination plate (min_vol=2.5 microL sample + 43.25 microL buffer)
* _A3,80.5_ will lead to a first 8.97x dilution (sqrt(80.5)) of min_vol=2.5 microL sample with 19.93 microL buffer in the _dilution plate_ 
  (pos A3, final volume 22.4 microL)
  followed by the dilution of min_vol=2.5 microL of the first dilution with 19.93 microL buffer in the _destination plate_ 
  (pos A3, final volume 22.4 microL)

The number of wells in the CSV and their order are not relevant (any order will do) as long as there are not more than 96 wells in the CSV

_The 'Position,Dilution' header line should not be altered as these names are used in the code_

The volumes 
---
## Materials

* 1x [Bio-Rad 96 Well Plate 200 µL PCR (hsp9601)](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?_gl=1*1a9qcug*_gcl_aw*R0NMLjE2MzE4MDAxNDUuQ2owS0NRanc4SWFHQmhDSEFSSXNBR0lSUllvamg1ZkhXczd1RUt2QTRLRE12cGE5WnBTbndpSmxybkxnVU54QTVJVEowRm04V2txTzhxTWFBbWxIRUFMd193Y0I.*_ga*MjA3NDg2NzQ1MC4xNjMwMDczMjAw*_ga_GNSMNLW4RY*MTYzMTc5OTI5Ny40My4xLjE2MzE4MDAyNTYuMA..)
* 1x [opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap?category=tubeRack)
* [P20 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes) in the left position
* 2x [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)
* [P300 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes) in the right position
* 2x [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_200ul?category=tipRack)

---
## Setup

* place the sample plate in position #1*
* place empty plates in position #2 and #3
* tube-rack in position #4 with 1..4 eppendorf tubes in first row; buffer: [A1..A4]
* tip boxes in 7,8 (p20-filter) and 9,10 (p200-filter)

### tube rack layout:
* first row: 1.2mL Tris buffer 10mM in each buffer tube

### YAML config file

The user must edit the dilute_96w_plate_config.yaml file to match the needs. Especially, the name of the CSV file must match the name of the file that will be injected in the NC web APP

```
params:
  sp_type: "biorad_96_wellplate_200ul_pcr"
  tp_type: "biorad_96_wellplate_200ul_pcr"
  dp_type: "biorad_96_wellplate_200ul_pcr"
  tube_rack: "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap"
  buf_vol: 1000.0
  min_vol: 2.0
  max_vol: 100.0
  max_dil: 20.0
  min_fin: 20.0
  pspeed: 24.0
  mix_times: 4
csv:
  uploaded_csv: "data.csv"
```

With:

```
buf_vol    max usable per eppendorf tube
smpl_vol   min usable sample volume in any well
min_vol    min pipettable volume
max_dil    max direct dilution (one step)
min_fin    min volume in dest well
pspeed     pipette speed (standard 7.56)
mix_times  mix sample and buffer after dispensing
```

### Robot
* [OT-2](https://opentrons.com/ot-2)

---
## Process
1. Attach the p20 single-chanel to the left mount and calibrate if not yet done.
1. Attach the p300 single-chanel to the right mount and calibrate if not yet done.
2. Download your protocol template (**from the template folder**)
3. Edit the config.yaml file and prepare a data.csv CSV file
4. Inject the _yaml_ and _CSV_ data in the template using the **[NC webtool](http://10.112.84.39/cgi-bin/OT2MakeProtocol/OT2MakeProtocol.php)** 
5. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
5. Set up your deck according to the deck map.
6. **Calibrate your labware, tiprack and pipette using the OT App**. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

_last update: SP - 2022-12-02_