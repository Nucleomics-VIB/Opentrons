from opentrons import protocol_api


metadata = {
        'protocolName': 'NC_4to1_pooling',
        'author': 'nucleomics@vib.be',
        'description': 'Consolidate 4 x 1/2 plates to 2 ful plates \
        and create a 8-well pool series with fixed volumes of each well',
        'source': 'VIB Nucleomics',
        'apiLevel': '2.11'
        }

# template version 1.01; 2021_10_22 (SP)
# edit date 2021-10-25


def get_values(*names):
    import json
    _all_values = json.loads("""{
        "tot_vol":30.0,
        "sp_vol":2.0,
        "ini_tris":10.0,
        "sp_type":"biorad_96_wellplate_200ul_pcr",
        "dp_type":"biorad_96_wellplate_200ul_pcr",
        "m20_mount":"left"
        }""")
    return [_all_values[n] for n in names]


def run(ctx: protocol_api.ProtocolContext):
    [tot_vol,
        sp_vol,
        ini_tris,
        sp_type,
        dp_type,
        m20_mount] = get_values(    # noqa: F821
            'tot_vol',
            'sp_vol',
            'ini_tris',
            'sp_type',
            'dp_type',
            'm20_mount')

    ##############
    # DEFINE DECK
    ##############

    mag_module1 = ctx.load_module(
        'magnetic module gen2',
        '4')
    merge_plate1 = mag_module1.load_labware(
        sp_type,
        label='Consolidation plate for 1A + 1B')

    mag_module2 = ctx.load_module(
        'magnetic module gen2',
        '1')
    merge_plate2 = mag_module2.load_labware(
        sp_type,
        label='Consolidation plate for 2A + 2B')

    pooling_plate = ctx.load_labware(
        dp_type,
        '10',
        'Pooling plate')

    tips = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in ['8', '9']]

    # define pipette
    pipette = ctx.load_instrument(
        'p20_multi_gen2',
        m20_mount,
        tip_racks=tips)

    # reservoir slot for Tris
    reservoir = ctx.load_labware(
        'nest_12_reservoir_15ml',
        '7',
        label='Reservoir')
    tris = reservoir['A1']

    # 4 library plates with only the right-half part
    # of each plate contains libraries
    s_slots = ['5', '6', '2', '3']
    source_list = [
        ctx.load_labware(
            sp_type,
            s_slot,
            'Source plates')
        for s_slot in s_slots]

    ###############################
    # warn user about input plates
    ###############################

    ctx.pause(
        '\n\n' + '#'*75 +
        '\nPut library plates in deck positions : [' +
        ' ,'.join(str(e) for e in s_slots) + '] (in that plate order!)' +
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

    # set speed for all pipette operations
    pspeed = 7.56
    set_speeds(pipette, pspeed)

    #########################################
    # fill pool tube ini_tris volume of Tris
    #########################################

    ctx.comment(
        "\n    #############################################" +
        "\n    ## pre-filling pooling column with Tris" +
        "\n    #############################################\n")

    # prefill A1 column with ini_tris uL to receive small volumes
    # return tips to be reused for the first column of plate#1A
    pipette.pick_up_tip()
    pipette.transfer(
        ini_tris,
        tris,
        pooling_plate['A1'],
        new_tip='never'
        )
    # return tips for the first column of 1A and reset counter
    pipette.return_tip()
    pipette.reset_tipracks()

    ##############################################
    # transfer half-plates to full plates
    # then take sp_vol to the pool with same tips
    ##############################################

    pltidx = 0
    col_rg1 = []
    [col_rg1.append('A' + str(col)) for col in range(1, 7, 1)]
    col_rg2 = []
    [col_rg2.append('A' + str(col)) for col in range(7, 13, 1)]

    # start in loop with value 1 for plate in position #5
    pltidx = 0

    for sample_plate in source_list:
        pltidx += 1
        # which plate to merge to
        m_pl = merge_plate1 if pltidx < 3 else merge_plate2
        # which columns to merge to
        col_rg = col_rg2 if pltidx % 2 == 0 else col_rg1

        ctx.comment(
            "\n    #############################################" +
            "\n    ## transferring and pooling plate " + str(pltidx) +
            "\n    #############################################\n")

        # transfer all to merging pate
        for i, (scol, dcol) in enumerate(zip(col_rg2, col_rg)):
            # transfer all to merging plate .bottom()
            pipette.pick_up_tip()
            pipette.transfer(
                tot_vol,
                sample_plate[scol].bottom(),
                m_pl[dcol].bottom(),
                new_tip='never'
            )
            # mix in place before taking small volume to pool
            # !! theoretically, the third parameter (location)
            # could be omitted here
            mix_iter = 5
            mix_vol = 10
            pipette.mix(
                mix_iter,
                mix_vol,
                m_pl[dcol].bottom()
            )
            # transfer some further to the pool with same tip
            pipette.transfer(
                sp_vol,
                m_pl[dcol].bottom(),
                pooling_plate['A1'].bottom(),
                new_tip='never'
            )
            pipette.drop_tip()

    ctx.comment(
        "\n    ##############################" +
        "\n    ## All done!" +
        "\n    ## you can now mix the pools" +
        "\n    ## located in the A1 column" +
        "\n    ## to a single tube" +
        "\n    ##############################")
