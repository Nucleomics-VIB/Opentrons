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
        "uploaded_csv":"source_plate,source_well,source_volume,dil_factor\\n1,A1,2.9,1\\n1,A2,4.7,1\\n1,A3,4.9,1\\n1,A4,3.6,1\\n1,A5,3.6,1\\n1,A6,3.7,1\\n1,A7,4,1\\n1,A8,2.1,1\\n1,A9,3.2,1\\n1,A10,5.7,1\\n1,A11,2.1,1\\n1,A12,3.3,1\\n1,B1,4.6,1\\n1,B2,4.9,1\\n1,B3,3.5,1\\n1,B4,2.9,1\\n1,B5,2.3,1\\n1,B6,2.5,1\\n1,B7,2.8,1\\n1,B8,2.5,1\\n1,B9,4.3,1\\n1,B10,2.2,1\\n1,B11,4.4,1\\n1,B12,3.1,1\\n1,C1,2.9,1\\n1,C2,5,1\\n1,C3,6,1\\n1,C4,2.9,1\\n1,C5,5.1,1\\n1,C6,5.6,1\\n1,C7,2.9,1\\n1,C8,4.6,1\\n1,C9,3.4,1\\n1,C10,5.6,1\\n1,C11,5.2,1\\n1,C12,5.9,1\\n1,D1,2.9,1\\n1,D2,2.2,1\\n1,D3,5.7,1\\n1,D4,2,1\\n1,D5,4.7,1\\n1,D6,3.9,1\\n1,D7,3.7,1\\n1,D8,2.2,1\\n1,D9,2,1\\n1,D10,3,1\\n1,D11,3.1,1\\n1,D12,4.9,1\\n1,E1,6,1\\n1,E2,5.7,1\\n1,E3,5.2,1\\n1,E4,6,1\\n1,E5,6,1\\n1,E6,5.7,1\\n1,E7,6,1\\n1,E8,4.2,1\\n1,E9,5.3,1\\n1,E10,3.2,1\\n1,E11,5,1\\n1,E12,5.4,1\\n1,F1,3.5,1\\n1,F2,5.4,1\\n1,F3,3.8,1\\n1,F4,4.7,1\\n1,F5,6,1\\n1,F6,4.3,1\\n1,F7,4.6,1\\n1,F8,4,1\\n1,F9,5.9,1\\n1,F10,3.7,1\\n1,F11,3.6,1\\n1,F12,2,1\\n1,G1,5.8,1\\n1,G2,2.4,1\\n1,G3,4.4,1\\n1,G4,2.4,1\\n1,G5,6,1\\n1,G6,3.9,1\\n1,G7,2.1,1\\n1,G8,2.1,1\\n1,G9,2.4,1\\n1,G10,5.9,1\\n1,G11,5.4,1\\n1,G12,5.9,1\\n1,H1,4.2,1\\n1,H2,2.7,1\\n1,H3,3.3,1\\n1,H4,5.9,1\\n1,H5,2,1\\n1,H6,4.3,1\\n1,H7,4.2,1\\n1,H8,2.4,1\\n1,H9,4.9,1\\n1,H10,4.3,1\\n1,H11,4,1\\n1,H12,5,1\\n2,A1,3.3,1\\n2,A2,4.4,1\\n2,A3,5,1\\n2,A4,5.6,1\\n2,A5,3,1\\n2,A6,5.2,1\\n2,A7,3.2,1\\n2,A8,3.5,1\\n2,A9,5.9,1\\n2,A10,2.4,1\\n2,A11,5.6,1\\n2,A12,4.9,1\\n2,B1,4.9,1\\n2,B2,2.8,1\\n2,B3,2.1,1\\n2,B4,4.3,1\\n2,B5,3.4,1\\n2,B6,2,1\\n2,B7,3.5,1\\n2,B8,3.9,1\\n2,B9,3.2,1\\n2,B10,3.9,1\\n2,B11,3.9,1\\n2,B12,4,1\\n2,C1,3.1,1\\n2,C2,5.4,1\\n2,C3,5.6,1\\n2,C4,2.9,1\\n2,C5,5.8,1\\n2,C6,3.3,1\\n2,C7,4.3,1\\n2,C8,5.8,1\\n2,C9,2.8,1\\n2,C10,5.7,1\\n2,C11,4.1,1\\n2,C12,5.4,1\\n2,D1,5.3,1\\n2,D2,4.9,1\\n2,D3,3.7,1\\n2,D4,2.2,1\\n2,D5,2.8,1\\n2,D6,3.6,1\\n2,D7,3,1\\n2,D8,3,1\\n2,D9,3.7,1\\n2,D10,3.4,1\\n2,D11,4.3,1\\n2,D12,3.9,1\\n2,E1,2.1,1\\n2,E2,2.3,1\\n2,E3,5.1,1\\n2,E4,2.9,1\\n2,E5,4.6,1\\n2,E6,3,1\\n2,E7,2.9,1\\n2,E8,2.9,1\\n2,E9,5.4,1\\n2,E10,5.7,1\\n2,E11,2.7,1\\n2,E12,2.8,1\\n2,F1,4.1,1\\n2,F2,5.5,1\\n2,F3,4.3,1\\n2,F4,2.1,1\\n2,F5,4.8,1\\n2,F6,2.2,1\\n2,F7,4.8,1\\n2,F8,5.6,1\\n2,F9,2.3,1\\n2,F10,4.3,1\\n2,F11,5.8,1\\n2,F12,3.4,1\\n2,G1,2.6,1\\n2,G2,4.8,1\\n2,G3,4,1\\n2,G4,5,1\\n2,G5,4.4,1\\n2,G6,5.3,1\\n2,G7,2,1\\n2,G8,2.5,1\\n2,G9,2,1\\n2,G10,5.8,1\\n2,G11,4.8,1\\n2,G12,5.6,1\\n2,H1,4.1,1\\n2,H2,3.8,1\\n2,H3,5,1\\n2,H4,3.4,1\\n2,H5,4.4,1\\n2,H6,3.3,1\\n2,H7,2.5,1\\n2,H8,3.8,1\\n2,H9,5.3,1\\n2,H10,5.6,1\\n2,H11,3.9,1\\n2,H12,2.1,1\\n3,A1,5.4,1\\n3,A2,3.9,1\\n3,A3,2.6,1\\n3,A4,5.7,1\\n3,A5,5.5,1\\n3,A6,4.5,1\\n3,A7,4.3,1\\n3,A8,4.1,1\\n3,A9,4.3,1\\n3,A10,4.5,1\\n3,A11,2.2,1\\n3,A12,2.7,1\\n3,B1,2.6,1\\n3,B2,2.9,1\\n3,B3,5.1,1\\n3,B4,5.8,1\\n3,B5,4.7,1\\n3,B6,2.4,1\\n3,B7,3.6,1\\n3,B8,5,1\\n3,B9,2.7,1\\n3,B10,5.2,1\\n3,B11,2.3,1\\n3,B12,5.2,1\\n3,C1,2.8,1\\n3,C2,3.1,1\\n3,C3,4,1\\n3,C4,4.3,1\\n3,C5,4.8,1\\n3,C6,4.6,1\\n3,C7,5.6,1\\n3,C8,4.9,1\\n3,C9,2.8,1\\n3,C10,2.5,1\\n3,C11,4.6,1\\n3,C12,2.5,1\\n3,D1,5.6,1\\n3,D2,2.5,1\\n3,D3,2.6,1\\n3,D4,5.4,1\\n3,D5,3.8,1\\n3,D6,3.8,1\\n3,D7,2.7,1\\n3,D8,2.6,1\\n3,D9,5.3,1\\n3,D10,3.8,1\\n3,D11,5.5,1\\n3,D12,4.3,1\\n3,E1,2.7,1\\n3,E2,3.8,1\\n3,E3,3.3,1\\n3,E4,5.2,1\\n3,E5,3.6,1\\n3,E6,6,1\\n3,E7,3.7,1\\n3,E8,5.8,1\\n3,E9,2.7,1\\n3,E10,5.7,1\\n3,E11,5.2,1\\n3,E12,4.2,1\\n3,F1,4.5,1\\n3,F2,2.6,1\\n3,F3,3.2,1\\n3,F4,3.2,1\\n3,F5,2.7,1\\n3,F6,5,1\\n3,F7,3.2,1\\n3,F8,2.9,1\\n3,F9,5.1,1\\n3,F10,4.3,1\\n3,F11,3.3,1\\n3,F12,5.4,1\\n3,G1,4.8,1\\n3,G2,4.7,1\\n3,G3,2.4,1\\n3,G4,3.5,1\\n3,G5,3.2,1\\n3,G6,3.8,1\\n3,G7,2.2,1\\n3,G8,2.8,1\\n3,G9,5.3,1\\n3,G10,3.2,1\\n3,G11,2.4,1\\n3,G12,5,1\\n3,H1,3.3,1\\n3,H2,6,1\\n3,H3,2.4,1\\n3,H4,3.4,1\\n3,H5,3,1\\n3,H6,4.3,1\\n3,H7,5.3,1\\n3,H8,5.7,1\\n3,H9,3.7,1\\n3,H10,4.7,1\\n3,H11,4,1\\n3,H12,5.2,1\\n4,A1,2,1\\n4,A2,4.8,1\\n4,A3,2.1,1\\n4,A4,5.1,1\\n4,A5,3,1\\n4,A6,5.9,1\\n4,A7,4.8,1\\n4,A8,5.8,1\\n4,A9,3.6,1\\n4,A10,3.7,1\\n4,A11,4.8,1\\n4,A12,5.2,1\\n4,B1,2,1\\n4,B2,5.5,1\\n4,B3,5.9,1\\n4,B4,5.9,1\\n4,B5,5.9,1\\n4,B6,4.1,1\\n4,B7,2.3,1\\n4,B8,4.9,1\\n4,B9,4,1\\n4,B10,5.9,1\\n4,B11,3.9,1\\n4,B12,2.2,1\\n4,C1,3.3,1\\n4,C2,4.5,1\\n4,C3,5.2,1\\n4,C4,5.4,1\\n4,C5,5,1\\n4,C6,5.9,1\\n4,C7,5.4,1\\n4,C8,3.8,1\\n4,C9,4.6,1\\n4,C10,2.9,1\\n4,C11,3.5,1\\n4,C12,3.6,1\\n4,D1,3.9,1\\n4,D2,3.7,1\\n4,D3,4.9,1\\n4,D4,3,1\\n4,D5,3.3,1\\n4,D6,5,1\\n4,D7,2.4,1\\n4,D8,2.8,1\\n4,D9,2.2,1\\n4,D10,5.6,1\\n4,D11,2.4,1\\n4,D12,6,1\\n4,E1,5.4,1\\n4,E2,5.6,1\\n4,E3,5.3,1\\n4,E4,2.2,1\\n4,E5,2.4,1\\n4,E6,5.6,1\\n4,E7,3.6,1\\n4,E8,3.5,1\\n4,E9,5.1,1\\n4,E10,4.4,1\\n4,E11,4.1,1\\n4,E12,2.6,1\\n4,F1,2.5,1\\n4,F2,4.9,1\\n4,F3,5.8,1\\n4,F4,5.2,1\\n4,F5,3.4,1\\n4,F6,5.3,1\\n4,F7,2.5,1\\n4,F8,3.9,1\\n4,F9,5.8,1\\n4,F10,5.8,1\\n4,F11,2.1,1\\n4,F12,2.1,1\\n4,G1,4.9,1\\n4,G2,2.3,1\\n4,G3,4.7,1\\n4,G4,3.4,1\\n4,G5,4.8,1\\n4,G6,5.5,1\\n4,G7,3.5,1\\n4,G8,2.4,1\\n4,G9,5.5,1\\n4,G10,3.5,1\\n4,G11,4.6,1\\n4,G12,2.4,1\\n4,H1,4.8,1\\n4,H2,3.4,1\\n4,H3,5.6,1\\n4,H4,3.2,1\\n4,H5,5.1,1\\n4,H6,5.8,1\\n4,H7,3.8,1\\n4,H8,4.3,1\\n4,H9,2.8,1\\n4,H10,5.6,1\\n4,H11,3.1,1\\n4,H12,5.2,1",
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
    pspeed = 7.56

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
