# NC repooling with dilution

### Authors
[VIB Nucleomics Core](https://www.nucleomics.be)

## Categories
* DNA method
	* magnetic bead purification

## Description

This protocol performs a 'magbead capture' of 20uL DNA samples (1:96) taken from a 96-well PCR plate and returns 50uL purified DNA in 200uL PCR 8-tube strips.

The m300 head is used to speed-up the process, making this protocol more suited for multiple of 8 samples.

Samples should be present in the leftmost columns of the plate.

---
## Materials

* [Bio-Rad 96 Well Plate 200 µL PCR (hsp9601)](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?_gl=1*1a9qcug*_gcl_aw*R0NMLjE2MzE4MDAxNDUuQ2owS0NRanc4SWFHQmhDSEFSSXNBR0lSUllvamg1ZkhXczd1RUt2QTRLRE12cGE5WnBTbndpSmxybkxnVU54QTVJVEowRm04V2txTzhxTWFBbWxIRUFMd193Y0I.*_ga*MjA3NDg2NzQ1MC4xNjMwMDczMjAw*_ga_GNSMNLW4RY*MTYzMTc5OTI5Ny40My4xLjE2MzE4MDAyNTYuMA..)
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://labware.opentrons.com/opentrons_96_aluminumblock_generic_pcr_strip_200ul?category=aluminumBlock)
* [Opentrons: NEST 12 Well Reservoir 15 mL (360102)](https://www.cell-nest.com/page94?_l=en&product_id=102)
* [P300 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [200ul Opentrons filter-tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

---
## Setup

Place the PCR plate with DNA samples in position #1
Place the aluminum block with enough 200uL PCR strips in position #2

### reservoir layout:
* col1: magnetic beads (AMPure XP; 500uL dead volume + enough for all samples)
* col2: 70% Ethanol (500uL dead volume + enough for all samples)
* col3: elution buffer (Tris 1mM, pH9 or water; 500uL dead volume + enough for all samples)
* col4-col11: empty
* col12: waste

### Robot
* [OT-2](https://opentrons.com/ot-2)

---
## Process
1. Attach the p300 multichanel to the right mount and calibrate them if not yet done.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".
7. Transfer the plate to the thermocycler adn run the TAG program.
8. Continue to Part-2 or store the plate for later resume.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).
