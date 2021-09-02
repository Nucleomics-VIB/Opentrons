metadata = {
    'apiLevel': '2.10',
    'protocolName': 'NC Rapid Barcoding Kit (SQK-RBK004)',
    'description': 'version without thermocycler',
    'author': 'Opentrons <protocols@opentrons.com> \
        VIB Nucleomics <nucleomics@vib.be>',
    'source': 'Adapted from protocol 3bc25d.py'
}

# script version 1.0; 2021_08_27 (SP)


def get_values(*names):
    import json
    _all_values = json.loads("""{"sample_count":1,"sample_vol":2.5}""")
    return [_all_values[n] for n in names]


def run(ctx):

    sample_count, sample_vol = get_values(  # noqa: F821
            'sample_count', 'sample_vol')

    # thermocycler on position #2
    # replaced by precooled +4°C aluminumBlock + BioRad 96 plate
    block_sample_plate = ctx.load_labware(
        'nc_opentrons_aluminumblock_96_biorad_hsp9601_200ul',
        '2')

    # magnetic module on position #4
    magdeck = ctx.load_module('magnetic module gen2', '4')
    magdeck.disengage()
    mag_plate = magdeck.load_labware('biorad_96_wellplate_200ul_pcr')
    mag_well = mag_plate.wells_by_name()["A1"]

    # temperature module on position #1
    tempdeck = ctx.load_module(
        'temperature module gen2',
        '1')
    temp_plate = tempdeck.load_labware(
        'opentrons_24_aluminumblock_generic_2ml_screwcap')

    RAP = temp_plate.wells_by_name()["A1"]
    AMPure_beads = temp_plate.wells_by_name()["A2"]

    fragmentation_mixes = [temp_plate.wells_by_name()["{}{}".format(
        a, b)] for a in ["B", "C"] for b in range(1, 7)][0:sample_count]

    # tube rack (24 eppendorf) on position #5
    tube_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '5')
    H2O = tube_rack.wells_by_name()["A1"]
    ethanol_70 = tube_rack.wells_by_name()["A2"]
    tris_nacl = tube_rack.wells_by_name()["A3"]
    liquid_trash = tube_rack.wells_by_name()["B1"]
    cleaned_library = tube_rack.wells_by_name()["C1"]

    p20s = ctx.load_instrument(
        'p20_single_gen2', 'left', tip_racks=[
            ctx.load_labware(
                'opentrons_96_filtertiprack_20ul', '6')])
    p300s = ctx.load_instrument(
        'p300_single_gen2', "right", tip_racks=[
            ctx.load_labware(
                'opentrons_96_filtertiprack_200ul', '9')])

    ctx.pause(
        '''
        place the 4°C cooled 96-well aluminumBlock on position #2
        place a new BioRad PCR plate on the aluminumBlock
        Select "Resume" in the Opentrons App.
        '''
        )

    tempdeck.set_temperature(4)

    ctx.comment('''
    #################################################
    ### adjust volume and transfer to PCR plate
    #################################################
    ''')

    p20s.default_speed = 50  # Slow to 1/8 speed
    # Adjust to 7.5 with H2O
    for well in block_sample_plate.wells()[0:sample_count]:
        p20s.transfer((7.5 - sample_vol), H2O, well, mix_after=(2, 4))

    # Move 2.5 of fragmentation mixes to block
    for i, f in enumerate(fragmentation_mixes):
        p20s.transfer(2.5, f, block_sample_plate.wells()[
                      i], mix_after=(2, 5), new_tip='always')
    p20s.default_speed = 400

    ctx.comment('''
    #################################################
    ### fragment DNA in thermocycler
    #################################################
    ''')

    # Thermocycle off-deck
    ctx.pause('''
        transfer the PCR plate on position #2 to a lab thermocycler
        run the following `ONT barcoding` one-cycle program on the thermocycler
        - 30°C for 1 min
        - 80°C for 1 min
        - 15°C (hold)
        when finished, transfer the PCR plate back to the OT-2 deck (#2)
        Select "Resume" in the Opentrons App.
        ''')

    ctx.comment('''
    #################################################
    ### pool fragmented samples to single tube
    #################################################
    ''')

    # Pool Samples
    if 20 * sample_count > 200:
        pooled_library = tube_rack.wells_by_name()["B2"]
    else:
        pooled_library = mag_plate.wells_by_name()["A1"]

    for well in block_sample_plate.wells()[0:sample_count]:
        p20s.transfer(10, well, pooled_library, new_tip='always')

    ctx.comment('''
    #################################################
    ### add AMPure beads
    #################################################
    ''')

    # Wash

    # Add beads, wait
    p300s.transfer(
        (10 * sample_count),
        AMPure_beads,
        pooled_library,
        mix_before=(
            10,
            (8 * sample_count)),
        mix_after=(
            2,
            (10 * sample_count)),
        new_tip='always')
    ctx.delay(300)

    ctx.comment('''
    #############################################################
    ### move AMPure beads mix to magnetic module (in two times)
    #############################################################
    ''')

    # Move half of beads to magplate, pull down, move rest.
    if 20 * sample_count > 200:
        p300s.transfer(
            (10 * sample_count),
            pooled_library,
            mag_well,
            mix_before=(
                3,
                (15 * sample_count)),
            new_tip='always')
        magdeck.engage()
        ctx.delay(450)
        p300s.transfer(200, mag_well, liquid_trash, new_tip='always')
        p300s.transfer(
            (10 * sample_count),
            pooled_library,
            mag_well,
            mix_before=(
                3,
                (5 * sample_count)),
            new_tip='always')

    magdeck.engage()
    ctx.delay(600)  # Drag down for a full 10 minutes
    p300s.transfer(200, mag_well, liquid_trash, new_tip='always')

    ctx.comment('''
    #################################################
    ### wash AMPure beads twice with Ethanol
    #################################################
    ''')

    p300s.default_speed = 100  # Slow down pipette speed to 1/8
    for _ in range(0, 2):
        p300s.transfer(
            200,
            ethanol_70,
            mag_well.bottom(7),
            new_tip='always')  # halfway
        ctx.delay(10)
        p300s.transfer(200, mag_well, liquid_trash, new_tip='always')
        ctx.delay(10)
    p300s.default_speed = 400

    # Dry for 10 minutes
    ctx.delay(600)
    magdeck.disengage()

    ctx.comment('''
    #################################################
    ### transfer cleaned library to final tube
    #################################################
    ''')

    p20s.transfer(10, tris_nacl, mag_well, mix_after=(3, 8), new_tip='always')
    ctx.delay(120)
    magdeck.engage()
    ctx.delay(300)
    p20s.transfer(10, mag_well, cleaned_library, new_tip='always')

    ctx.comment('''
    #################################################
    ### add RAP to cleaned library
    #################################################
    ''')

    # Add RAP
    p20s.transfer(1, RAP, mag_well, mix_after=(2, 5), new_tip='always')
    ctx.delay(300)

    ctx.comment('''
    ###############################################################
    ### ALL done, you can load the library on the GridIon flowcell
    ###############################################################
    ''')
