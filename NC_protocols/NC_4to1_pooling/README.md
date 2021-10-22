# NC blind pooling

### Authors
[VIB Nucleomics Core](https://www.nucleomics.be)

## Categories
* DNA method
	* library pooling

## Description

This protocol takes a fixed volume of all samples from several 96well plates (1..4) and pools them column-wise to two columns in a new plate. The resulting two-columns can be mixed to create a global pool ready for concentration and QC'ed before processing in a Illumina library prep workflow.

The concentration of the individual samples is not taken into account in this protocol and all samples are considered equal. Subsequent differences found by sequencing can be compensated by doing a re-pooling and re-sequencing.


---
## Materials

* 5x [Bio-Rad 96 Well Plate 200 µL PCR (hsp9601)](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?_gl=1*1a9qcug*_gcl_aw*R0NMLjE2MzE4MDAxNDUuQ2owS0NRanc4SWFHQmhDSEFSSXNBR0lSUllvamg1ZkhXczd1RUt2QTRLRE12cGE5WnBTbndpSmxybkxnVU54QTVJVEowRm04V2txTzhxTWFBbWxIRUFMd193Y0I.*_ga*MjA3NDg2NzQ1MC4xNjMwMDczMjAw*_ga_GNSMNLW4RY*MTYzMTc5OTI5Ny40My4xLjE2MzE4MDAyNTYuMA..)
* [Opentrons: NEST 12 Well Reservoir 15 mL (360102)](https://www.cell-nest.com/page94?_l=en&product_id=102)
* [P20 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* 5x [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)

---
## Setup

* place up to 4 sample plates with DNA samples in positions #[5,6,2,3] (in that order)
* place the empty dilution plate in position #4
* NEST 12 Well Reservoir in position #1 with 1ml Tris in the first column (320uL required for 16 tubes)

### reservoir layout:
* col1: Tris buffer

### Robot
* [OT-2](https://opentrons.com/ot-2)

---
## Process
1. Attach the p20 multie-chanel to the right mount and calibrate if not yet done.
2. Download your protocol or adapt it using the NC tool and your CSV file.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).
