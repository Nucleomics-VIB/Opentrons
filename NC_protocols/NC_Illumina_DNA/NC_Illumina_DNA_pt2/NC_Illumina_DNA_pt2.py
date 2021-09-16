from opentrons.types import Point
import json

metadata = {
    'protocolName': 'NC_Illumina_DNA_pt2',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>, \
        Stefaan Derveaux <stefaan.derveaux@vib.be>',
    'description': 'Illumina DNA part2 (8-48 samples) \
        - Post Tagmentation Cleanup',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
    }

# script version 1.2; 2021_08_20 (SD)


def get_values(*names):

    _all_values = json.loads(
        """
        {
        "num_samp":48,
        "asp_height":1,
        "length_from_side":3,
        "index_start_col":1,
        "tip_park_start_col":1,
        "m20_mount":"left",
        "m300_mount":"right"
        }
        """
    )
    return [_all_values[n] for n in names]


def run(ctx):

    [num_samp,
    index_start_col,
    tip_park_start_col,
    asp_height,
    length_from_side,
    m20_mount,
    m300_mount] = get_values(  # noqa: F821
            "num_samp",
            "index_start_col",
            "tip_park_start_col",
            "asp_height",
            "length_from_side",
            "m20_mount",
            "m300_mount"
            )

    # check index_start_col & tip_park_start_col in valid range
    if not 1 <= index_start_col <= 12:
        raise Exception("Enter an index start column 1-12")
    if not 1 <= tip_park_start_col <= 12:
        raise Exception("Enter a tip_park start column 1-12")

    num_samp = int(num_samp)
    num_col = int(num_samp/8)
    if num_col - tip_park_start_col < 0:
        raise Exception("Not enough tips on slot 11. Refill tip rack on 11.")

    # shift index to 0-based
    index_start_col = int(index_start_col)-1
    tip_park_start_col = int(tip_park_start_col)-1

    # load labware
    mag_module = ctx.load_module(
        'magnetic module gen2',
        '1')
    sample_plate = mag_module.load_labware(
        'biorad_96_wellplate_200ul_pcr',
        label='Sample Plate')
    reagent_plate = ctx.load_labware(
        'biorad_96_wellplate_200ul_pcr',
        '2',
        label='Reagent Plate')
    index_plate = ctx.load_labware(
        'illumina_96_wellplate_200ul',
        '3',
        label='Index Plate')
    reservoir = ctx.load_labware(
        'nest_12_reservoir_15ml',
        '4',
        label='Reservoir')
    tiprack_20 = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in ['5']]
    park_tips_300 = ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        '7',
        label='Park tip_200')
    park_tips_20 = ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        '6',
        label='Park tip_20')
    tiprack300 = [ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        slot,
        label='tip_200')
            for slot in ['8', '11']]
    park2_tips_300 = ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        '10',
        label='Park tip_200 2')

    # load instrument (remove_supernatant20 toegevoegd)
    m20 = ctx.load_instrument(
        'p20_multi_gen2',
        m20_mount,
        tip_racks=tiprack_20)
    m300 = ctx.load_instrument(
        'p300_multi_gen2',
        m300_mount,
        tip_racks=tiprack300)

    # turn lights ON (comment out to turn OFF)
    ctx.set_rail_lights(True)

    # globally change instrument values
    magnet_height = 10

    # globally change magnetic capture duration (1 for testing)
    capture_duration = 1

    # define custom routines
    def change_speeds(pip, speed):
        pip.flow_rate.aspirate = speed
        pip.flow_rate.dispense = speed

    def remove_supernatant(vol, index, loc, delta_asp_height=-1.0):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height+delta_asp_height).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        m300.aspirate(vol, aspirate_loc)
        m300.dispense(vol, waste)
        m300.blow_out()

    # universal removal with defaults:
    # delta_asp_height=-0.5
    # (0.5mm below the top, in other steps set to 4mm above)
    # pip=m300 # (tip_200 multi-chanel)
    # extra_vol=0 # dispense an extra 60microL to empty tips in one step)
    def remove_supernatant_uni(
            vol,
            index,
            loc,
            trash=False,
            delta_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m300):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height+delta_asp_height).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        pip.aspirate(vol, aspirate_loc)
        if trash:
            vol2 = vol + extra_vol
            pip.dispense(vol2, waste_by_index[index].top(z=-5), rate=disp_rate)
            pip.blow_out()

    def mix_at_beads(vol, index, loc):
        side = 1 if index % 2 == 0 else -1
        aspirate_loc = loc.bottom(z=asp_height).move(
            Point(x=(loc.diameter/2-length_from_side)*side))
        dispense_loc = loc.bottom(z=asp_height+4).move(
            Point(x=(loc.diameter/2-length_from_side)*side))
        for _ in range(15):
            m300.aspirate(vol, aspirate_loc)
            m300.dispense(vol, dispense_loc)

    # reagents
    tsb = reagent_plate.rows()[0][1]
    epm = reagent_plate.rows()[0][2]
    twb = reservoir.wells()[1]
    waste = reservoir.wells()[5]
    waste_by_index = reservoir.wells()[6:12]

    # transfer TSB from mastermix plate to sample plate
    ctx.comment(
        '#'*3 +
        ' transfer TSB from mastermix plate to sample plate in position ' +
        '#'*3)
    for col in sample_plate.rows()[0][:num_col]:
        m20.pick_up_tip()
        m20.aspirate(5, tsb)
        m20.dispense(5, col)
        m20.mix(9, 17, col, rate=2.0)
        m20.mix(1, 17, col, rate=0.5)
        m20.drop_tip()

    ctx.pause('''
        Seal sample plate with Microseal B.
        Transfer the plate to the thermocycler and run the PTC program.
        At completion, return the PCR plate to the magnetic module.
        Empty the trash if needed.
        Select "Resume" in the Opentrons App.
        ''')

    # engage magnet, remove supernatant, add TWB 1
    ctx.comment('#'*3 + ' capture, remove SN, add TWB wash#1 ' + '#'*3)
    mag_module.engage()
    ctx.delay(minutes=capture_duration)

    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 15)
        # remove supernatant and drop tips
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col+6])
        remove_supernatant(35, i, col, delta_asp_height=-1.0)
        m300.drop_tip()
        # add 50ul of twb over beads and park tips
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col])
        m300.aspirate(50, twb)
        m300.dispense(50, col)
        m300.return_tip()

    # disengage magnet, mix at bead location, and park tips
    mag_module.disengage()
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 35)
        # mix beads and park tips
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col])
        mix_at_beads(20, i, col)
        m300.return_tip()

    # engage magnet, remove supernatant (with parked tips),
    #   add TWB 2 (new tips)
    ctx.comment('#'*3 + ' capture, remove SN, add TWB wash#2 ' + '#'*3)
    mag_module.engage()
    ctx.delay(minutes=capture_duration)

    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 15)
        # remove supernatant and drop tips
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col])
        remove_supernatant_uni(
            vol=55,
            index=i,
            loc=col,
            trash=True,
            delta_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m300)
        m300.drop_tip()
        # add 50ul of twb over beads and park tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col])
        m300.aspirate(50, twb)
        m300.dispense(50, col)
        m300.return_tip()

    mag_module.disengage()
    # mix at bead location and park tips
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 35)
        # mix beads and park tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col])
        mix_at_beads(20, i, col)
        m300.return_tip()

    # engage magnet, remove supernatant (with parked tips),
    #  add TWB 3 (new tips)
    ctx.comment('#'*3 + ' capture, remove SN, add TWB wash#3 ' + '#'*3)
    mag_module.engage()
    ctx.delay(minutes=capture_duration)

    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 15)
        # remove supernatant and drop tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col])
        remove_supernatant_uni(
            vol=55,
            index=i,
            loc=col,
            trash=True,
            delta_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m300)
        m300.drop_tip()
        # add 50ul of twb over beads and park tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col+6])
        m300.aspirate(50, twb)
        m300.dispense(50, col)
        m300.return_tip()

    mag_module.disengage()
    # mix at bead location with parked tips
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 35)
        # mix beads and park tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col+6])
        mix_at_beads(20, i, col)
        m300.return_tip()

    # prepare EPM Mastermix
    ctx.pause(
        '''
        Put EPM Mastermix onto columns 3 and 4 of the reagent plate.
        Add Illumina index plate to the deck.
        Empty trash if needed.
        Click on "Resume" in the Opentrons App.
        '''
        )

    # engage magnet, remove supernatant with parked tips, add EPM Mastermix
    ctx.comment('#'*3 + ' capture, remove SN, add EPM Mastermix ' + '#'*3)
    mag_module.engage()
    ctx.delay(minutes=capture_duration)

    ctx.comment('\n remove supernatant TWB wash#3 (P300)\n')
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 15)
        # remove supernatant and drop tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col+6])
        remove_supernatant_uni(
            vol=55,
            index=i,
            loc=col,
            trash=True,
            delta_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m300)
        m300.drop_tip()

    ctx.comment('\n remove residual supernatant TWB wash#3 (P20)\n')
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        # remove supernatant and drop tips
        m20.pick_up_tip()
        remove_supernatant_uni(
            vol=10,
            index=i,
            loc=col,
            trash=True,
            delta_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m20)
        m20.drop_tip()

    ctx.comment('#'*3 + ' add EPM (parked tips), mix EPM ' + '#'*3)
    # add EPM
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        # add 20ul of epm over beads and park tips
        m20.pick_up_tip(park_tips_20.rows()[0][i+tip_park_start_col])
        m20.aspirate(20, epm, rate=0.75)
        m20.dispense(20, col, rate=0.75)
        m20.return_tip()

    # mix epm
    mag_module.disengage()
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m20, 20)
        # mix beads and drop tips
        m20.pick_up_tip(park_tips_20.rows()[0][i+tip_park_start_col])
        m20.mix(10, 18, col)
        m20.drop_tip()

    # add indexes
    ctx.comment('#'*3 + ' add Illumina indexes ' + '#'*3)
    for i, (source_col, dest_col) in enumerate(
            zip(index_plate.rows()[0][index_start_col: index_start_col + num_col],  # noqa: F501
            sample_plate.rows()[0])):
        m20.pick_up_tip(park_tips_20.rows()[0][i+tip_park_start_col+6])
        # add indexes
        m20.aspirate(5, source_col, rate=0.75)
        m20.dispense(5, dest_col, rate=0.75)
        change_speeds(m20, 20)
        # mix and drop tips
        m20.mix(10, 18, dest_col)
        m20.drop_tip()

    ctx.comment('''
        Seal the plate with microseal-B
        (centrifuge the plate at 280g for 30sec)
        Place on the thermocycler and run the BLT PCR program
        After completion, the plate can be safely stored at +2°C to +8°C.
        ''')
