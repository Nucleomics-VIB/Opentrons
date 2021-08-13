# Illumina DNA Library Prep: Part-3/3 - Clean up Libraries

### Authors
[Opentrons](https://opentrons.com/) and [VIB Nucleomics Core](https://www.nucleomics.be)

## Categories
* NGS Library Prep
	* Illumina DNA Library Prep

## Description
This protocol performs the 'Tagment DNA' section of the [Illumina DNA Library Prep protocol](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html).

Links:
* [Dilute DNA Samples and Tagment](../NC_Illumina_DNA_pt1)
* [Post Tagmentation Cleanup](../NC_Illumina_DNA_pt2)
* Amplify Tagmented DNA using the lab thermocycler
* [Cleanup Libraries](../NC_Illumina_DNA_pt3) - (this potocol)

---
## Materials

* 3x [Bio-Rad Hard Shell 96-well low profile PCR plate 200ul #hsp9601 (well diameter:5.46mm, well depth:14.81mm)](bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Opentrons: NEST 12 Well Reservoir 15 mL (360102)](https://www.cell-nest.com/page94?_l=en&product_id=102) - **(New empty reservoir)**
* [P20 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [20ul Opentrons tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [P300 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* 5x [300ul Opentrons tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


---
## Setup

Prepare solutions and fill the reservoir slots when prompted

### reservoir layout: **(New empty reservoir)**
* col3: RSB
* col4: 70% Ethanol
* col5: 70% Ethanol
* col6: 70% Ethanol
* col10: waste
* col11: waste

### Robot
* [OT-2](https://opentrons.com/ot-2)

---
## Process

1. Input the mount side for your P50 single-channel pipette, whether you are using a P50 multi-channel pipette, the mount for your P50 multi-channel pipette (if applicable), and the number of samples to process.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).
