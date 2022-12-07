# Simple dilution 96w

### Authors
[VIB Nucleomics Core](https://www.nucleomics.be)

## Categories
* DNA method
	* library pooling

## Description

This protocol takes samples from 96well plates applies the same fixed dilution factor to all wells to produce a diluted plate. 

When the dilution factor is more than 20x, an intermediate dilution step at 1:10 is made to an intermediate plate, followed by the remaining dilution to the final plate.

---
## Materials

* 3x [Bio-Rad 96 Well Plate 200 µL PCR (hsp9601)](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?_gl=1*1a9qcug*_gcl_aw*R0NMLjE2MzE4MDAxNDUuQ2owS0NRanc4SWFHQmhDSEFSSXNBR0lSUllvamg1ZkhXczd1RUt2QTRLRE12cGE5WnBTbndpSmxybkxnVU54QTVJVEowRm04V2txTzhxTWFBbWxIRUFMd193Y0I.*_ga*MjA3NDg2NzQ1MC4xNjMwMDczMjAw*_ga_GNSMNLW4RY*MTYzMTc5OTI5Ny40My4xLjE2MzE4MDAyNTYuMA..)
* 1x [nest_12_reservoir_15ml](https://labware.opentrons.com/nest_12_reservoir_15ml?category=tubeRack) - 12 channel reservoir
* 1x [P20 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* 1x [P200 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* 2x [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)
* 1x [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)

---
## Setup

* place the DNA input pate with DNA on 'magnetic module gen2' in position #1
* place the intermediate dilution plate in position #2
* place the final plate in position #3


### container (position #1):
*  1: solvant in sufficient quantity to process the whole plate (15ml)
* 12: liquid waste

### Robot
* [OT-2](https://opentrons.com/ot-2)

---
## Process
1. Attach the p20 single-chanel to the left mount and calibrate if not yet done.
2. Download your protocol or adapt it using the NC tool and your CSV file.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).
