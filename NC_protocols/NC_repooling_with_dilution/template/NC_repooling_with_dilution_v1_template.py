from opentrons import protocol_api

metadata = {
        'protocolName': 'NC_repooling_with_dilution',
        'author': 'nucleomics@vib.be',
        'description': 'Cherrypicking from 1..4 plates and CSV \
            (+ intermediate dilution for concentrated samples)',
        'source': 'VIB Nucleomics',
        'apiLevel': '2.10'
        }

# template version 1.2; 2021_09_16 (SP)
# edit date <edit_date>


def get_values(*names):
    import json
    _all_values = json.loads("""{
        "uploaded_csv":"<uploaded_csv>",
        "min_vol":"<min_vol>",
        "sp_type":"<sp_type>",
        "dp_type":"<dp_type>"
        }""")
    return [_all_values[n] for n in names]


def run(ctx: protocol_api.ProtocolContext):
    [uploaded_csv,
        min_vol,
        sp_type,
        dp_type] = get_values(    # noqa: F821
        'uploaded_csv',
        'min_vol',
        'sp_type',
        'dp_type')

    # define tip racks and pipette
    tips = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in range(7, 9)]

    pipette = ctx.load_instrument(
        'p20_single_gen2',
        'left',
        tip_racks=tips)

    tube_rack = ctx.load_labware(
        'opentrons_24_tuberack_nest_1.5ml_snapcap',
        '1')

    # water in all 6 first row rack tubes (1ml per tube)
    water_tubes = tube_rack.rows_by_name()['A']
    global water_counter, wt_idx
    water_counter = 1000
    wt_idx = 0

    # pool in last rack tube
    pool_tube = tube_rack.wells_by_name()["D6"]

    max_dil_fact = 80.0     # since 2.5x80=200uL

    dilution_plate = ctx.load_labware(
        dp_type,
        '4',
        'Dilution plate')
    # define *global value for next dilution well
    next_dil_well = 0

    # load csv data into memory
    data = [[val.strip() for val in line.split(',')]
            for line in uploaded_csv.splitlines()
            if line.split(',')[0].strip()][1:]

    ###################################
    # do some testing on the user data
    ###################################

    # fail if too many samples in csv
    if len(data) > 96:
        usrmsg = (
            'max 96 samples can be repooled!' +
            '(csv has ' + str(len(data)) + ')')
        raise Exception(usrmsg)

    # fail if too many samples plates (sp_number)
    plates = [int(row[0]) for row in data]
    sp_number = max(plates)
    if not int(sp_number) in range(1, 5, 1):
        usrmsg = (
            'sample plate number in csv should be' +
            ' an integer between 1 and 4')
        raise Exception(usrmsg)

    # fail if volumes less than min_vol in csv
    vols = [float(row[2]) for row in data]
    if min(vols) < float(min_vol):
        usrmsg = (
            'sample volume(s) in csv are smaller than' +
            'the minimal volume !' +
            '(' + str(min_vol) + ')')
        raise Exception(usrmsg)

    # warn if dilution factors larger than max_dil_fact in csv
    dils = [float(row[3]) for row in data]
    if max(dils) > max_dil_fact:
        usrmsg = (
            'dilution factor(s) in csv are larger' +
            ' than the max possible !' +
            ' (' + str(max_dil_fact) + ')')
        raise Exception(usrmsg)

    # up top 4 customer plates to pick CSV-selected samples from
    slots = ['5', '6', '2', '3'][:sp_number]    # slots[0:sp_number]
    source_list = [
        ctx.load_labware(sp_type, slot, 'Source plates')
        for slot in slots]

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

    def dilute_and_pool(s_pl, s_well, s_vol, d_fact, dil_well):

        # pipet s_vol from dilution plate next_dil_well to pool
        ctx.comment(
            '\n' + '#'*3 + ' diluting ' + str(s_vol) + 'ul from plate' +
            str(s_pl) + " " + s_well + " " + str(d_fact) +
            ' times, and adding ' + str(s_vol) + 'ul to the pool')

        pipette.pick_up_tip()

        # add water to dil_fact to dilution plate in well next_dil_well
        water_vol = (d_fact-1) * s_vol

        # enough for next dilution or increment water tube index
        global water_counter, wt_idx
        water_counter -= water_vol
        if water_counter < 0:
            water_counter = 1000
            wt_idx += 1
        # TBD, check if the 6 water tubes have been used and ask a refill

        ctx.comment(
            '\n' + '#'*2 + ' taking ' + str(water_vol) +
            'ul water from tube index: ' + str(wt_idx) +
            '\n')

        pipette.transfer(
            water_vol,
            water_tubes[wt_idx],
            dilution_plate.wells()[dil_well],
            new_tip='never'
            )

        # pipet s_vol to dilution plate next_dil_well and mix with at most 20ul
        mix_vol = min(20, 0.8 * water_vol)
        pltidx = s_pl-1
        pipette.transfer(
            s_vol,
            source_list[pltidx][s_well],
            dilution_plate.wells()[dil_well],
            mix_after=(10, mix_vol),
            new_tip='never'
            )

        # transfer s_vol (diluted) to pool
        pipette.transfer(
            s_vol,
            dilution_plate.wells()[dil_well],
            pool_tube,
            blow_out=True,
            blowout_location='destination well',
            new_tip='never'
            )

        pipette.drop_tip()

    def add_to_pool(s_pl, s_well, s_vol, d_fact):

        # pipet s_vol to pool
        ctx.comment(
            '\n\n' + '#'*3 + ' adding ' + str(s_vol) +
            'ul from plate' + str(s_pl) + " " +
            s_well + ' to the pool')

        pipette.pick_up_tip()

        # transfer s_vol (undiluted) to pool
        pltidx = s_pl-1
        pipette.transfer(
            s_vol,
            source_list[pltidx][s_well],
            pool_tube,
            blow_out=True,
            blowout_location='destination well',
            new_tip='never'
            )

        pipette.drop_tip()

    ############################
    # fill pool tube 50 uL Tris
    ############################

    pipette.pick_up_tip()
    pipette.transfer(
        50,
        water_tubes[wt_idx],
        pool_tube,
        new_tip='never'
        )
    pipette.drop_tip()
    water_counter -= 50

    ###################
    # process csv data
    ###################

    # reset type
    min_vol = float(min_vol)

    for line in data:
        s_pl, s_well, s_vol, d_fact = line[0:4]

        # change types
        s_pl = int(s_pl)
        s_well = str(s_well)
        s_vol = float(s_vol)
        d_fact = float(d_fact)

        # debug
        # print(line," - ", s_well)

        if d_fact > 1:
            # max dilution is 80x due to well size
            if d_fact > max_dil_fact:
                d_fact = max_dil_fact
            # set s_vol to min_vol if larger
            if s_vol > min_vol:
                s_vol = min_vol
            dilute_and_pool(s_pl, s_well, s_vol, d_fact, int(next_dil_well))
            # increment for next dilution
            next_dil_well = next_dil_well+1
        else:
            add_to_pool(s_pl, s_well, s_vol, d_fact)

    ctx.comment('''
    ###########################################################
    # All done!                                              ##
    ## the new Pool is ready in the tube rack last position  ##
    ###########################################################
    ''')
