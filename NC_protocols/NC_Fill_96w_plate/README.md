# NC_fill_96w_plate

### Authors
[VIB Nucleomics Core](https://www.nucleomics.be)

## Categories
* General method
	* sample dilution
	
## Description

This protocol distributes a solution (buffer) to a 96 well plate based on a CSV file providing [well-names + volume] pairs.

The protocol exist in two *flavors*, one using a reservoir for buffer and liquid trash (*costly*) and a *savvy* one using eppendorf tubes in a tube-rack.

---
## Materials

* 1x [Bio-Rad 96 Well Plate 200 µL PCR (hsp9601)](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?_gl=1*1a9qcug*_gcl_aw*R0NMLjE2MzE4MDAxNDUuQ2owS0NRanc4SWFHQmhDSEFSSXNBR0lSUllvamg1ZkhXczd1RUt2QTRLRE12cGE5WnBTbndpSmxybkxnVU54QTVJVEowRm04V2txTzhxTWFBbWxIRUFMd193Y0I.*_ga*MjA3NDg2NzQ1MC4xNjMwMDczMjAw*_ga_GNSMNLW4RY*MTYzMTc5OTI5Ny40My4xLjE2MzE4MDAyNTYuMA..)
* 1x [Opentrons: NEST 12 Well Reservoir 15 mL (360102)](https://www.cell-nest.com/page94?_l=en&product_id=102)
* _ALT:_ 1x [opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap?category=tubeRack)
* [P20 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* 1x [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)
* [P300 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* 1x [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_200ul?category=tipRack)

---
## Setup

* place 1 empty plates in position  #[1]
* NEST 12 Well Reservoir in position #4 with 6mL Tris in col#1
* _ALT_ tube-rack with eppendorf tubes in the first row (A1..A4) for buffer and A6 as waste tube

### reservoir layout:
* col#1: Tris buffer 10mM
* _ALT_ first row: 1mL Tris buffer 10mM in each buffer tube


### Robot
* [OT-2](https://opentrons.com/ot-2)

---
## Process
1. Attach the p20 single-chanel to the left mount and calibrate if not yet done.
1. Attach the p300 single-chanel to the right mount and calibrate if not yet done.
2. Download your protocol template (**from the template folder**)
3. Edit the config.yaml file and prepare a data.csv CSV file
4. Inject the ''yaml'' and ''CSV'' data in the template using the **[NC webtool](http://10.112.84.39/cgi-bin/OT2MakeProtocol/OT2MakeProtocol.php)** 
5. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

_last update: SP - 2022-11-29_