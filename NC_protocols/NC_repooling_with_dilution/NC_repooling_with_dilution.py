from opentrons import protocol_api
import math


metadata = {
        'protocolName': 'NC_repooling_with_dilution',
        'author': 'nucleomics@vib.be',
        'description': 'Cherrypicking from 1..4 plates and CSV \
            (+ optional intermediate dilution for concentrated samples)',
        'source': 'VIB Nucleomics',
        'apiLevel': '2.10'
        }

# template version 2.0; 2021_09_24 (SP)
# edit date 2021-09-24


def get_values(*names):
    import json
    _all_values = json.loads("""{
        "uploaded_csv":"source_plate,source_well,source_volume,dil_factor\\n1,A1,2.5,1\\n1,A8,5,1\\n2,B4,2.5,10\\n3,F6,2.5,80\\n4,H8,20,50",
        "min_vol":"2.0",
        "sp_type":"biorad_96_wellplate_200ul_pcr",
        "dp_type":"biorad_96_wellplate_200ul_pcr"
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

    # reference for custom functions
    jakadi = ctx

    tube_rack = ctx.load_labware(
        'opentrons_15_tuberack_falcon_15ml_conical',
        '1')

    # tris in top-left 15ml tube
    tris_tube = tube_rack.wells_by_name()['A1']
    global tris_counter
    tris_counter = 5000.0
    # initial volume in pool tube
    ini_tris = 50.0

    # pool in bottom-right 15ml tube
    pool_tube = tube_rack.wells_by_name()["C5"]
    max_pool_vol = 8000.0    # to fit in one tube

    # reset type
    min_vol = float(min_vol)

    # must dilute in a 200uL well
    max_dil_fact = 200.0/min_vol   # eg 200.0/2.5 = 80x

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

    # provision enough tips
    total_tips = len(data) + 1
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
    pspeed = 10

    # fail if too many samples to be diluted in csv
    dilcnt = len([row[3] for row in data if (row[3] != '1')])
    ctx.comment(
        '## ' + str(dilcnt) +
        ' of the ' + str(len(data)) +
        ' samples will be diluted')

    if dilcnt > 96:
        usrmsg = (
            'max 96 samples can be diluted!' +
            '(csv has ' + str(dilcnt) + ')')
        raise Exception(usrmsg)

    # estimate volumes based on CSV data
    trisdil = ini_tris + sum([
        float(min_vol)*float(row[3]) for row in data if (row[3] != '1')
        ])
    dilsmplvol = sum([float(min_vol) for row in data if (row[3] != '1')])
    nondilsmplvol = sum([float(row[2]) for row in data if (row[3] == '1')])

    # inform about the volume of Tris needed
    ctx.comment("## the run will use " + str(trisdil) + "uL Tris buffer")
    ctx.pause("## check there is enough Tris in the tube on position #1:A1")

    # fail if pool is too large
    pool_vol = round(trisdil+dilsmplvol+nondilsmplvol, 1)
    if pool_vol > max_pool_vol:
        usrmsg = (
            '## Pool estimated at ' + str(pool_vol) + 'uL)' +
            '\n## the pool would be too large for the tube, stopping!')
        raise Exception(usrmsg)

    ctx.comment("## the pool will contain " + str(pool_vol) + "uL")

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

    def set_speeds(pip, aspeed, dspeed=None, bspeed=None):
        pip.flow_rate.aspirate = aspeed
        pip.flow_rate.dispense = dspeed if dspeed is not None else aspeed
        pip.flow_rate.blow_out = bspeed if bspeed is not None else aspeed

    def reset_speeds(pip):
        # req: jakadi reference created on top of the code
        pip.flow_rate.set_defaults(jakadi.api_version)

    def dilute_and_pool(s_pl, s_well, s_vol, d_fact, dil_well):

        # pipet s_vol from dilution plate next_dil_well to pool
        ctx.comment(
            '\n' + '#'*3 + ' diluting ' + str(s_vol) + 'ul from plate' +
            str(s_pl) + " " + s_well + " " + str(d_fact) +
            ' times, and adding ' + str(s_vol) + 'ul to the pool')

        # pipette.pick_up_tip()

        # add tris to dil_fact to dilution plate in well next_dil_well
        tris_vol = (d_fact-1) * s_vol

        # enough for next dilution or increment tris tube index
        global tris_counter
        tris_counter -= tris_vol

        ctx.comment(
            '\n' + '#'*2 + ' taking ' + str(tris_vol) +
            'ul tris for dilution' +
            '\n')

        # pipet tris_vol to dilution plate next_dil_well
        pipette.transfer(
            tris_vol,
            tris_tube,
            dilution_plate.wells()[dil_well],
            new_tip='never'
            )

        # pipet s_vol to dilution plate next_dil_well and mix with at most 20ul
        mix_vol = min(20, 0.8 * tris_vol)
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

        # pipette.pick_up_tip()

        # transfer s_vol (undiluted) to pool
        pltidx = s_pl-1
        pipette.pick_up_tip()
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
    # PROTOCOL STARTS HERE
    ############################

    ############################
    # fill pool tube 50 uL Tris
    ############################

    set_speeds(pipette, pspeed)

    # prefill pool tube with ini_tris uL to receive small volumes
    # keep tip for first sample
    pipette.pick_up_tip()
    pipette.transfer(
        ini_tris,
        tris_tube,
        pool_tube,
        new_tip='never'
        )
    pipette.drop_tip()
    tris_counter -= ini_tris

    ###################
    # process csv data
    ###################

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

    ctx.comment(
      "\n    #############################################" +
      "\n    ## All done!" +
      "\n    ## the pool in the tube rack (last position)" +
      "\n    ## and contains " + str(pool_vol) + "uL"
      "\n    #############################################")
