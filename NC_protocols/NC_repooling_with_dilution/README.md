# NC repooling with dilution

### Authors
[VIB Nucleomics Core](https://www.nucleomics.be)

## Categories
* DNA method
	* library pooling

## Description

This protocol takes samples from 96well plates and pools a given quantity (or dilution thereof) to a pool tube. The Pool is later concentrated and QC'ed before processing in a Illumina library prep workflow.


---
## Materials

* [Bio-Rad 96 Well Plate 200 µL PCR (hsp9601)](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?_gl=1*1a9qcug*_gcl_aw*R0NMLjE2MzE4MDAxNDUuQ2owS0NRanc4SWFHQmhDSEFSSXNBR0lSUllvamg1ZkhXczd1RUt2QTRLRE12cGE5WnBTbndpSmxybkxnVU54QTVJVEowRm04V2txTzhxTWFBbWxIRUFMd193Y0I.*_ga*MjA3NDg2NzQ1MC4xNjMwMDczMjAw*_ga_GNSMNLW4RY*MTYzMTc5OTI5Ny40My4xLjE2MzE4MDAyNTYuMA..)
* [opentrons_15_tuberack_falcon_15ml_conical](https://labware.opentrons.com/opentrons_15_tuberack_falcon_15ml_conical?category=tubeRack)
* [P20 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)

---
## Setup

* place up to 4 sample plates with DNA samples in positions #[5,6,2,3] (in that order)
* place the empty dilution plate in position #4

### tube rack layout (position #1):
* A1: 15ml tube with Tris buffer for dilution (0.5ml unless more required)
* C5: 15ml tube for pool

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
