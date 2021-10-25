# NC 4to1 pooling

### Authors
[VIB Nucleomics Core](https://www.nucleomics.be)

## Categories
* DNA method
	* library pooling

## Description

This protocol takes a libraries from 4 half-plates and consolidates them in to two full plates. It then takes a small volume (fixed) of each well to a global pool distributed over 8 tubes. The 8 tubes required further mixing, done by hand to achieve the final pool, ready for sequencing.

The concentration of the individual samples is not taken into account in this protocol and all samples are considered equal. Subsequent differences found by sequencing can be compensated by doing a re-pooling and re-sequencing.


---
## Materials

* 4x [Bio-Rad 96 Well Plate 200 µL PCR (hsp9601)](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?_gl=1*1a9qcug*_gcl_aw*R0NMLjE2MzE4MDAxNDUuQ2owS0NRanc4SWFHQmhDSEFSSXNBR0lSUllvamg1ZkhXczd1RUt2QTRLRE12cGE5WnBTbndpSmxybkxnVU54QTVJVEowRm04V2txTzhxTWFBbWxIRUFMd193Y0I.*_ga*MjA3NDg2NzQ1MC4xNjMwMDczMjAw*_ga_GNSMNLW4RY*MTYzMTc5OTI5Ny40My4xLjE2MzE4MDAyNTYuMA..)
* 3x extra plates for consolidation and for pooling [Bio-Rad 96 Well Plate 200 µL PCR (hsp9601)](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?_gl=1*1a9qcug*_gcl_aw*R0NMLjE2MzE4MDAxNDUuQ2owS0NRanc4SWFHQmhDSEFSSXNBR0lSUllvamg1ZkhXczd1RUt2QTRLRE12cGE5WnBTbndpSmxybkxnVU54QTVJVEowRm04V2txTzhxTWFBbWxIRUFMd193Y0I.*_ga*MjA3NDg2NzQ1MC4xNjMwMDczMjAw*_ga_GNSMNLW4RY*MTYzMTc5OTI5Ny40My4xLjE2MzE4MDAyNTYuMA..)
* [Opentrons: NEST 12 Well Reservoir 15 mL (360102)](https://www.cell-nest.com/page94?_l=en&product_id=102)
* [P20 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* 2x [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)

---
## Setup

* place 4 sample plates with sequencing libraries (in their right halves) in positions #[5,6,2,3] (in that order)
* place two consolidation plates on the top of the two magnetic modules in positions #1 and #4
* place the pooling plate in position #10
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
