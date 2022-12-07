from opentrons import protocol_api
import math


metadata = {
        'protocolName': 'simple_dilution_96w',
        'author': 'nucleomics@vib.be',
        'description': 'applying a fixed dilution factor to a whole 96w plate \
            (+ optional intermediate dilution if dilution factor >20)',
        'source': 'VIB Nucleomics',
        'apiLevel': '2.10'
        }

# template version 1.0b; 2022_09_06 (SP)
# edit date ....


def get_values(*names):
    import json
    _all_values = json.loads("""{
        "dil_fact":"<dil_fact>",
        }""")
    return [_all_values[n] for n in names]


def run(ctx: protocol_api.ProtocolContext):
    [dil_fact] = get_values(    # noqa: F821
        'dil_fact')

    # reference for custom functions
    jakadi = ctx

    # 96-well plate type
    96w_plate = "biorad_96_wellplate_200ul_pcr"

    # three plates on deck, the input plate and two dilution plates
    mag_deck = ctx.load_module("magnetic module gen2",
                               '1')

    sample_plate = mag_deck.load_labware(
        96w_plate,
        'input plate')

    dilution_plate1 = ctx.load_labware(
        96w_plate,
        '2',
        'dilution_plate1')

    # only required when dil_fact > 20
    dilution_plate2 = ctx.load_labware(
        96w_plate,
        '3',
        'dilution_plate2')

    reagent_container = ctx.load_labware(
            'nest_12_reservoir_15ml',
            '5')

    # dilution buffer in first two slots and waste in last
    buffer = reagent_container.wells_by_name()[1]
    liquid_waste = reagent_container.wells_by_name()[12]

    # provision enough tips for 2 dilutions
    slots = ['6', '10']
    tips20 = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in slots]

    tips300 = [ctx.load_labware(
        'opentrons_96_filtertiprack_300ul',
        9,
        label='tip_300')]


    # define pipettes
    pipette20 = ctx.load_instrument(
        'p20_multi_gen2',
        'left',
        tip_racks=tips20)

    pipette300 = ctx.load_instrument(
        'p300_multi_gen2',
        'right',
        tip_racks=tips300)

    # reset type
    min_vol = float(2.0)

    # max single-step dilution_plate
    max_dil_1 = 40.0/min_vol   # eg 40.0/2.0 = 20.0

    # set speed for all pipette operations
    pspeed = 7.56

    # estimate volumes based on dil_fact x 96 wells
    buffer_needed = 0.0
    if dil_fact > max_dil_1:
    	# two-step dilution mode, 1:10 then 1:(dil_fact/10)
    	first_dil = 96 * 18.0
    	buffer_needed = first_dil + 96 * 2 * (dil_fact/10)
    else:
    	buffer_needed = 96 * dil_fact * 2
    
    # increase by 20% for safety
    buffer_needed = buffer_needed * 1.2

    # inform about the volume of Tris needed
    ctx.comment("## the run will use " + str(buffer_needed) + "uL dilution buffer")
    ctx.pause("## check there is enough buffer in the container on position #1")

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
    # fill dilution plate#1 with 18 uL Tris
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
