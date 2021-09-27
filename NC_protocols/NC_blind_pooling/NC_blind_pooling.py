from opentrons import protocol_api
import math


metadata = {
        'protocolName': 'NC_blind_pooling',
        'author': 'nucleomics@vib.be',
        'description': 'Fixed-volume pooling from 1-4 96well plates \
        to two columns in a new plate',
        'source': 'VIB Nucleomics',
        'apiLevel': '2.11'
        }

# template version 1.0; 2021_09_27 (SP)
# edit date 2021-09-27


def get_values(*names):
    import json
    _all_values = json.loads("""{
        "sp_vol":2.0,
        "sp_num":4,
        "sp_type":"biorad_96_wellplate_200ul_pcr",
        "dp_type":"biorad_96_wellplate_200ul_pcr"
        }""")
    return [_all_values[n] for n in names]


def run(ctx: protocol_api.ProtocolContext):
    [sp_vol,
        sp_num,
        sp_type,
        dp_type] = get_values(    # noqa: F821
        'sp_vol',
        'sp_num',
        'sp_type',
        'dp_type')

    # reservoir slot for Tris
    reservoir = ctx.load_labware(
        'nest_12_reservoir_15ml',
        '4',
        label='Reservoir')
    tris = reservoir['A1']

    # initial volume for pool tubes
    ini_tris = 20

    if not int(sp_num) in range(1, 5, 1):
        usrmsg = (
            'sample plate number should be' +
            ' an integer between 1 and 4')
        raise Exception(usrmsg)

    # up top 4 customer plates to pick samples from
    slots = ['5', '6', '2', '3'][:sp_num]    # slots[0:sp_number]
    source_list = [
        ctx.load_labware(sp_type, slot, 'Source plates')
        for slot in slots]

    destination_plate = ctx.load_labware(
        dp_type,
        '1',
        'Destination plate')

    # set speed for all pipette operations
    pspeed = 7.56

    ###################################
    # do some testing on the user data
    ###################################

    # provision enough tips
    total_tips = sp_num*96+8
    tiprack_num = math.ceil(total_tips/96)
    slots = ['7', '8', '9', '10', '11'][:tiprack_num]
    tips = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in slots]

    # define pipette
    pipette = ctx.load_instrument(
        'p20_single_gen2',
        'left',
        tip_racks=tips)

    # set speed for all pipette operations
    pspeed = 7.56

    ctx.pause(
        '\n\n' + '#'*75 +
        '\nPut Sample plates in deck positions : [' +
        ' ,'.join(str(e) for e in slots) + '] (in that plate order!)' +
        '\nThen select "Resume" in the Opentrons App\n' +
        '#'*75
        )

    ###########
    # routines
    ###########

    def set_speeds(pip, aspeed, dspeed=None, bspeed=None):
        pip.flow_rate.aspirate = aspeed
        pip.flow_rate.dispense = dspeed if dspeed is not None else aspeed
        pip.flow_rate.blow_out = bspeed if bspeed is not None else aspeed

    ############################
    # PROTOCOL STARTS HERE
    ############################

    set_speeds(pipette, pspeed)

    ############################
    # fill pool tube 20 uL Tris
    ############################

    ctx.comment(
        "\n    #############################################" +
        "\n    ## prefilling destination tubes with Tris" +
        "\n    #############################################\n")

    # prefill pool columns with ini_tris uL to receive small volumes
    pipette.pick_up_tip()
    pool_cols = ['A1', 'B1']
    for col in pool_cols[:sp_num]:
        pipette.transfer(
            ini_tris,
            tris,
            destination_plate[col],
            new_tip='never'
            )
    pipette.drop_tip()

    ############################
    # pool samples
    ############################

    ctx.comment(
        "\n    #############################################" +
        "\n    ## pooling samples to two column pools" +
        "\n    #############################################\n")

    for pltidx in range(0, sp_num, 1):
        # even plates pooled in A1 and odd plates pooled in B1
        p_col = 'A1' if pltidx % 2 == 0 else 'B1'
        sample_plate = source_list[pltidx]
        for col in sample_plate.columns()[0:12][0]:
            pipette.transfer(
                sp_vol,
                col,
                destination_plate[p_col]
                )

    ctx.comment(
      "\n    #############################################" +
      "\n    ## All done!" +
      "\n    ## you can now pool the column pools" +
      "\n    ## located in the A1 and B1 columns" +
      "\n    #############################################")
