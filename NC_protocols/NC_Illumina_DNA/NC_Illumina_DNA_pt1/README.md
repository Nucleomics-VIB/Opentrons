# Illumina DNA Library Prep: Part-1/3 - Tagment DNA

### Authors
[Opentrons](https://opentrons.com/) and [VIB Nucleomics Core](https://www.nucleomics.be)

## Categories
* NGS Library Prep
	* Illumina DNA Library Prep

## Description
This protocol performs the 'Tagment DNA' section of the [Illumina DNA Library Prep protocol](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html).

Links:
* [Dilute DNA Samples and Tagment](../NC_Illumina_DNA_pt1) - (this potocol)
* [Post Tagmentation Cleanup](../NC_Illumina_DNA_pt2)
* Amplify Tagmented DNA using the lab thermocycler
* [Cleanup Libraries](../NC_Illumina_DNA_pt3)

![deck_48]("./Deck layout pt1_48s.png")

---
## Materials

* [Bio-Rad Hard Shell 96-well low profile PCR plate 200ul #hsp9601 (well diameter:5.46mm, well depth:14.81mm)](bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Opentrons: NEST 12 Well Reservoir 15 mL (360102)](https://www.cell-nest.com/page94?_l=en&product_id=102)
* [P20 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* 3x [20ul Opentrons tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [P300 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [300ul Opentrons tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

---
## Setup

Vortex BLT and TB1 vigorously for 10 seconds before dispensing in the mastermix plate. Preprogram the thermocycler according to the TAG program parameters described in the kit manual.

### reservoir layout:
* col1: water
* col5: waste (empty)

### reagent plate layout:
* col1: mastermix from the kit BLT and TB1 stocks (vortexed before adding to plate)

### Robot
* [OT-2](https://opentrons.com/ot-2)

---
## Process
1. Attach the p20 multichanel to the left mount and the p300 multichanel to the right mount and calibrate them if not yet done.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".
7. Transfer the plate to the thermocycler adn run the TAG program.
8. Continue to Part-2 or store the plate for later resume.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).
