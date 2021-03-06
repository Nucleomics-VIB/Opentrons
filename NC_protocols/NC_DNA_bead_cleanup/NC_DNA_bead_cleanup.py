import math

# uses the multichannel m300
# Sample number: Customize the number of samples to run per protocol.
# A multiple of 8 is recommended when you are using a multichannel pipette.
# Sample volume: Specify the starting volume (in uL) of the input sample.
# Bead Ratio: Customize the ratio of beads for left or right side
# size-selection of fragments.
# The default bead ratio is 1.8x the input sample volume.
# Elution Volume: Specify the final volume (in uL) to elute the purified
# nucleic acid. The Opentrons MagDeck only supports elution volumes above 10µL.
# Incubation Time: Specify the amount of time (in minutes) that the bead
# solution and input sample interact.
# Settling Time: Specify the amount of time (in minutes) needed to pellet the
# beads. Higher volumes may require a longer settling time.
# Drying Time: Specify the drying time (in minutes) needed after wash steps.

# Container options: to be able to further use the same container
# beads_position (default to 0)
# ethanol_position (default to 1)
# elution_buffer_position (default to 2)
# waste_position (set by default to the last column of the reservoir: -1)


metadata = {
    'protocolName': 'NC_DNA_bead_cleanup',
    'description': 'magnetic bead cleanup using multichannel m300 for speedup',
    'author': 'Opentrons <protocols@opentrons.com>, \
        NucleomicsCore <nucleomics@vib.be>',
    'source': 'NC Protocol Library',
    'apiLevel': '2.10'
    }

# version 1.1 SP@NC 2021/09/22
# status: passed simulation


def get_values(*names):
    import json
    _all_values = json.loads("""{
        "pipette_mount":"right",
        "input_plate_type":"biorad_96_wellplate_200ul_pcr",
        "output_plate_type":"opentrons_96_aluminumblock_generic_pcr_strip_200ul",
        "sample_number":1,
        "sample_volume":20,
        "bead_ratio":1.8,
        "beads_position":0,
        "ethanol_position":1,
        "elution_buffer_position":2,
        "waste_position":-1,
        "elution_buffer_volume":50,
        "incubation_time":1,
        "capture_time":2,
        "drying_time":5
        }""")
    return [_all_values[n] for n in names]


def run(ctx):

    # create reference for functions
    jakadi = ctx

    [pipette_type,
        pipette_mount,
        input_plate_type,
        output_plate_type,
        sample_number,
        sample_volume,
        bead_ratio,
        beads_position,
        ethanol_position,
        elution_buffer_position,
        waste_position,
        elution_buffer_volume,
        incubation_time,
        capture_time,
        drying_time] = get_values(  # noqa: F821
        "pipette_mount",
        "input_plate_type",
        "output_plate_type",
        "sample_number",
        "sample_volume",
        "bead_ratio",
        "beads_position",
        "ethanol_position",
        "elution_buffer_position",
        "waste_position",
        "elution_buffer_volume",
        "incubation_time",
        "capture_time",
        "drying_time")

    mag_deck = ctx.load_module("magnetic module gen2",
                               '1')

    mag_plate = mag_deck.load_labware(
        input_plate_type,
        'input plate')

    output_plate = ctx.load_labware(
        output_plate_type,
        '2',
        'output plate')

    total_tips = sample_number*8
    tiprack_num = math.ceil(total_tips/96)

    # reserve enough tips boxes for all samples
    slots = ['3', '5', '6', '7', '8', '9', '10', '11'][:tiprack_num]
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                for slot in slots]

    pipette = ctx.load_instrument(
        pipette_type, pipette_mount, tip_racks=tipracks)

    reagent_container = ctx.load_labware(
            'nest_12_reservoir_15ml',
            '4')
    # Define reagents and liquid waste
    # by default these are 0, 1, and 2
    #   (can be more to further use the same reservoir)
    beads = reagent_container.wells()[beads_position]
    ethanol = reagent_container.wells()[ethanol_position]
    elution_buffer = reagent_container.wells()[elution_buffer_position]
    liquid_waste = reagent_container.wells()[waste_position]

    col_num = math.ceil(sample_number/8)
    samples = [col for col in mag_plate.rows()[0][:col_num]]
    output = [col for col in output_plate.rows()[0][:col_num]]

    # Define bead and mix volume
    bead_volume = sample_volume*bead_ratio
    if bead_volume/2 > pipette.max_volume:
        mix_vol = pipette.max_volume
    else:
        mix_vol = bead_volume/2
    total_vol = bead_volume + sample_volume + 5

    # --------------- custom functions ---------------
    def set_speeds(pip, aspeed, dspeed=None, bspeed=None):
        pip.flow_rate.aspirate = aspeed
        pip.flow_rate.dispense = dspeed if dspeed is not None else aspeed
        pip.flow_rate.blow_out = bspeed if bspeed is not None else aspeed

    def reset_speeds(pip):
        # req: jakadi reference created on top of the code
        pip.flow_rate.set_defaults(jakadi.api_version)

    def xcomment(text):
        # req: jakadi reference created on top of the code
        import io
        width = len(max(io.StringIO(text), key=len).rstrip())+6
        jakadi.comment('\n' + '#'*width)
        for line in io.StringIO(text):
            if not line.isspace():  # omit empty lines
                jakadi.comment('#'*3 + line.rstrip())  # remove trailing spaces
        jakadi.comment('#'*width + '\n')  # leave one empty line below

    def xpause(text):
        xcomment(text)
        jakadi.pause("==> select 'Resume' in the Opentrons App")
    # --------------- end custom functions ---------------

    # --------------- protocol ---------------
    xpause('''
      make sure you have placed enough labelled PCR strips
      on the Alu-block (position #2) to receive the purified DNA
      ''')

    xcomment('''
    Bead DNA capture
    ''')

    for target in samples:
        pipette.pick_up_tip()
        pipette.mix(
            5,
            mix_vol,
            beads)
        pipette.transfer(
            bead_volume,
            beads,
            target,
            new_tip='never')
        pipette.mix(
            10,
            mix_vol,
            target)
        pipette.blow_out()
        pipette.drop_tip()

    # bind DNA to beads
    ctx.delay(minutes=incubation_time)

    # capture beads
    mag_deck.engage()
    ctx.delay(minutes=capture_time)

    xcomment('''
    Remove bead supernatant
    ''')

    set_speeds(pipette, 25, 150)

    for target in samples:
        pipette.transfer(
            total_vol,
            target,
            liquid_waste,
            blow_out=True)

    reset_speeds(pipette)

    xcomment('''
    Wash beads twice with 70% ethanol
      (using air_gap to prevent leak)
    ''')

    air_vol = 10
    # pipette.max_volume * 0.1
    for cycle in range(2):
        # add EtOH to beads pellet
        for target in samples:
            pipette.transfer(
                190,
                ethanol,
                target,
                air_gap=air_vol,
                new_tip='once')
        # apply for 1 extra min (last wells)
        ctx.delay(minutes=1)
        # remove EtOH
        for target in samples:
            pipette.transfer(
                190,
                target,
                liquid_waste,
                air_gap=air_vol)
    # Dry at RT
    ctx.delay(minutes=drying_time)

    # Disengage MagDeck
    mag_deck.disengage()

    xcomment('''
    Elute DNA from beads
    ''')

    if elution_buffer_volume/2 > pipette.max_volume:
        mix_vol = pipette.max_volume
    else:
        mix_vol = elution_buffer_volume/2

    for target in samples:
        pipette.pick_up_tip()
        pipette.transfer(
            elution_buffer_volume,
            elution_buffer,
            target,
            new_tip='never')
        pipette.mix(
            20,
            mix_vol,
            target)
        pipette.drop_tip()

    # Incubate at RT
    ctx.delay(minutes=5)

    # Engage MagDeck and remain engaged for DNA elution
    mag_deck.engage()
    ctx.delay(minutes=capture_time)

    xcomment('''
    Transfer clean DNA to the PCR-strip on position #2
    ''')

    set_speeds(pipette, 25, 150)
    for target, dest in zip(samples, output):
        pipette.transfer(
            elution_buffer_volume,
            target,
            dest,
            blow_out=True)

    xcomment('''
    All done!
    the PCR strip(s) on position #2 contain purified DNA
    Make sure to label them!
    ''')
