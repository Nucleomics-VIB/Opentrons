from opentrons.types import Point
import json

metadata = {
    'protocolName': 'NC_Illumina_DNA_ptA',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>, \
        Stefaan Derveaux <stefaan.derveaux@vib.be>',
    'description': 'Illumina DNA part-A (8-48 samples) \
        - Tagment DNA + Post Tagmentation Cleanup',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
    }

# script version 2.0; 2021_09_29 (SD)


def get_values(*names):
    _all_values = json.loads(
        """
        {
            "spl_nbr":48,
            "tip300_s_col":1,
            "asp_height":1.0,
            "mm_from_s":2.0,
            "idx_s_col":1,
            "tip_park_s_col":1,
            "m20_mount":"left",
            "m300_mount":"right"
        }
        """)
    return [_all_values[n] for n in names]


def run(ctx):

    # get user inputs
    [spl_nbr,
        tip300_s_col,
        idx_s_col,
        tip_park_s_col,
        asp_height,
        mm_from_s,
        m20_mount,
        m300_mount] = get_values(  # noqa: F821
            "spl_nbr",
            "tip300_s_col",
            "idx_s_col",
            "tip_park_s_col",
            "asp_height",
            "mm_from_s",
            "m20_mount",
            "m300_mount")

    ##############
    # DEFINE DECK
    ##############

    # define deck labware
    mag_module = ctx.load_module(
        'magnetic module gen2',
        '1')
    final_plate = mag_module.load_labware(
        'biorad_96_wellplate_200ul_pcr',
        label='NO plate at beginning')
    reagent_plate = ctx.load_labware(
        'biorad_96_wellplate_200ul_pcr',
        '5',
        label='Reagent Plate')
    tagm_plate = ctx.load_labware(
        'biorad_96_wellplate_200ul_pcr',
        '2',
        label='Tagmentation Plate')
    index_plate = ctx.load_labware(
        'illumina_96_wellplate_200ul',
        '3',
        label='Index Plate NotAtStart')
    reservoir = ctx.load_labware(
        'nest_12_reservoir_15ml',
        '4',
        label='Reservoir')
    tiprack20 = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in ['8', '11']]
    park_tips_20 = ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        '6',
        label='Park tip_20')
    tiprack300 = ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        '9',
        label='tip_200')
    park_tips_300 = ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        '7',
        label='Park tip_200')
    park2_tips_300 = ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        '10',
        label='Park tip_200 2')

    # define pipettes
    m20 = ctx.load_instrument(
        'p20_multi_gen2',
        m20_mount,
        tip_racks=tiprack20)
    m300 = ctx.load_instrument(
        'p300_multi_gen2',
        m300_mount,
        tip_racks=[tiprack300])

    # turn lights ON (comment out to turn OFF)
    ctx.set_rail_lights(True)

    # globally change instrument values
    magnet_height = 8

    # globally change magnetic capture duration (1 for testing)
    capture_duration = 3

    # reagent plate
    mastermix = reagent_plate.rows()[0][0]
    tsb = reagent_plate.rows()[0][1]
    epm = reagent_plate.rows()[0][2]

    # reservoir
    water = reservoir.wells()[0]
    twb = reservoir.wells()[1]

    # selective waste sorting
    waste = reservoir.wells()[5]
    waste_by_index = reservoir.wells()[6:12]

    ####################
    # CHECK USER INPUTS
    ####################

    # check tip300_s_col, idx_s_col
    #   & tip_park_s_col in valid range
    if not 1 <= tip300_s_col <= 12:
        raise Exception("Enter a 200ul tip start column 1-12")
    if not 1 <= idx_s_col <= 12:
        raise Exception("Enter an index start column 1-12")
    if not 1 <= tip_park_s_col <= 12:
        raise Exception("Enter a tip_park start column 1-12")

    spl_nbr = int(spl_nbr)
    num_col = int(spl_nbr/8)
    if num_col - tip_park_s_col < 0:
        raise Exception("Not enough tips on slot 11. Refill tip rack on 11.")

    ####################
    # CUSTOM FUNCTIONS
    ####################

    def xcomment(text, funcprot=ctx, bchar='#'):
        import io
        width = len(max(io.StringIO(text), key=len).rstrip())+4
        # leave one empty line above
        funcprot.comment('\n' + bchar*width)
        for line in io.StringIO(text):
            # omit empty lines
            if not line.isspace():
                # remove trail spaces and LF
                funcprot.comment(bchar*3 + line.rstrip())
        # leave one empty line below
        funcprot.comment(bchar*width + '\n')

    def xpause(text, funcprot=ctx):
        xcomment(text)
        funcprot.pause("==> press continue when ready!")

    # set all three flow_rates for a pipet
    def set_speeds(pip, aspeed, dspeed=None, bspeed=None):
        pip.flow_rate.aspirate = aspeed
        pip.flow_rate.dispense = dspeed if dspeed is not None else aspeed
        pip.flow_rate.blow_out = bspeed if bspeed is not None else aspeed

    # reset all three flow_rates for a pipet
    def reset_speeds(pip):
        pip.flow_rate.set_defaults(ctx.api_version)

    # universal removal with defaults:
    # d_asp_height=-0.5
    # (0.5mm below the top, in other steps set to 4mm above)
    # pip=m300 # (tip_200 multi-chanel)
    # extra_vol=0 # dispense an extra 60microL to empty tips in one step)
    def remove_sn(
            vol,
            index,
            loc,
            trash=None,
            d_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m300):
        # at which well side is the magnet (-1:left; 1:right)
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height+d_asp_height).move(
            Point(x=(loc.diameter/2-mm_from_s)*side))
        # aspirate supernatant
        pip.aspirate(vol, aspirate_loc)
        # empty to Trash if True
        if trash == 'waste':
            vol2 = vol + extra_vol
            pip.dispense(vol2, waste.top(z=-5), rate=disp_rate)
            pip.blow_out()
        if trash == 'waste_by_index':
            vol2 = vol + extra_vol
            pip.dispense(vol2, waste_by_index[index].top(z=-5), rate=disp_rate)
            pip.blow_out()

    def mix_at_beads(vol, index, loc, iter, pip):
        side = 1 if index % 2 == 0 else -1
        aspirate_loc = loc.bottom(z=asp_height).move(
            Point(x=(loc.diameter/2-mm_from_s)*side))
        dispense_loc = loc.bottom(z=asp_height).move(
            Point(x=(loc.diameter/2-mm_from_s)*side))
        for _ in range(iter):
            pip.aspirate(vol, aspirate_loc)
            pip.dispense(vol, dispense_loc)

    #######################
    # PROTOCOL STARTS HERE
    #######################

    mag_module.disengage()

    # add water to empty biorad plate
    ctx.comment(
        '#'*3 +
        ' adding water to tagmentation plate in position #2 ' +
        '#'*3)
    m20.pick_up_tip()
    for col in tagm_plate.rows()[0][:num_col]:
        m20.aspirate(10, water)
        m20.dispense(10, col)
    m20.drop_tip()

    # add dna manually to plate
    xpause('''
    * remove tagmentation plate from position #2
    * add 5µl DNA manually to wells A1-H6
    * return the plate to the deck in postion #2
    * empty the trash if needed
    ''')

    # add mastermix to plate
    ctx.comment(
        '#'*3 +
        ' adding mastermix to tagmentation plate in position #2 ' +
        '#'*3)
    set_speeds(m20, 4)

    for i, col in enumerate(tagm_plate.rows()[0][:num_col]):
        if i % 3 == 0:
            m300.pick_up_tip(tiprack300.rows()[0][tip300_s_col])
            totalvolmastermix = 10*num_col+5-i*10
            mixvolume = 0.8*totalvolmastermix
            m300.mix(9, mixvolume, mastermix, rate=0.25)
            m300.mix(1, mixvolume, mastermix, rate=0.1)
        if num_col-i <= 3 and m300.has_tip:
            m300.drop_tip()
        elif m300.has_tip:
            m300.return_tip()
        m20.pick_up_tip()
        m20.aspirate(10, mastermix)
        ctx.delay(seconds=1.5)
        m20.dispense(10, col)
        m20.mix(14, 18, col, rate=6.0)
        m20.mix(1, 18, col)
        m20.drop_tip()

    xpause('''
    * seal the plate with microseal-B
    * place it on the thermocycler and run the TAG program
    * when done, return the plate to position #2
    ''')

    # transfer TSB from mastermix plate to tagmentation plate
    ctx.comment(
        '#'*3 +
        ' adding TSB to tagmentation plate in position #2 ' +
        '#'*3)
    for col in tagm_plate.rows()[0][:num_col]:
        m20.pick_up_tip()
        m20.aspirate(5, tsb)
        m20.dispense(5, col)
        m20.mix(9, 20, col, rate=8.0)
        m20.mix(1, 20, col, rate=0.5)
        m20.drop_tip()

    xpause('''
    * seal tagmentation plate with Microseal B
    * transfer the plate to the thermocycler and run the PTC program
    * place the plate on the magnetic module on position #1
        (position 1, left top corner) (! NOT position 2 !)
    * empty the trash if needed
    ''')

    # engage magnet, remove supernatant, add TWB 1
    ctx.comment(
        '#'*3 +
        ' capturing, removing SN, adding TWB wash#1 ' +
        '#'*3)
    mag_module.engage(height=magnet_height)
    ctx.delay(minutes=capture_duration)

    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        set_speeds(m300, 15)
        # remove supernatant and drop tips
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_s_col+6])
        remove_sn(
            vol=35,
            index=i,
            loc=col,
            trash='waste',
            d_asp_height=-1.0,
            extra_vol=0,
            disp_rate=1,
            pip=m300)
        m300.drop_tip()
        # add 50ul of twb over beads and park tips
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_s_col])
        m300.aspirate(50, twb)
        m300.dispense(50, col)
        m300.return_tip()

    # disengage magnet, mix at bead location, and park tips
    mag_module.disengage()
    set_speeds(m300, 150)
    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        # mix beads and park tips
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_s_col])
        mix_at_beads(
            vol=40,
            index=i,
            loc=col,
            iter=25,
            pip=m300)
        m300.return_tip()

    # engage magnet, remove supernatant (with parked tips),
    #   add TWB 2 (new tips)
    ctx.comment(
        '#'*3 +
        ' capturing, removing TWB wash#1, adding TWB wash#2 ' +
        '#'*3)
    mag_module.engage(height=magnet_height)
    ctx.delay(minutes=capture_duration)
    set_speeds(m300, 15)

    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        # remove supernatant and drop tips
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_s_col])
        remove_sn(
            vol=55,
            index=i,
            loc=col,
            trash='waste_by_index',
            d_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m300)
        m300.drop_tip()
        # add 50ul of twb over beads and park tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_s_col])
        m300.aspirate(50, twb)
        m300.dispense(50, col)
        m300.return_tip()

    mag_module.disengage()
    set_speeds(m300, 150)

    # mix at bead location and park tips
    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        # mix beads and park tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_s_col])
        mix_at_beads(
            vol=40,
            index=i,
            loc=col,
            iter=25,
            pip=m300)
        m300.return_tip()

    # engage magnet, remove supernatant (with parked tips),
    #  add TWB 3 (new tips)
    ctx.comment(
        '#'*3 +
        ' capturing, removing TWB wash#2, adding TWB wash#3 ' +
        '#'*3)
    mag_module.engage(height=magnet_height)
    ctx.delay(minutes=capture_duration)
    set_speeds(m300, 15)

    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        # remove supernatant and drop tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_s_col])
        remove_sn(
            vol=55,
            index=i,
            loc=col,
            trash='waste_by_index',
            d_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m300)
        m300.drop_tip()
        # add 50ul of twb over beads and park tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_s_col+6])
        m300.aspirate(50, twb)
        m300.dispense(50, col)
        m300.return_tip()

    mag_module.disengage()
    set_speeds(m300, 150)

    # mix at bead location with parked tips
    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        # mix beads and park tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_s_col+6])
        mix_at_beads(
            vol=40,
            index=i,
            loc=col,
            iter=25,
            pip=m300)
        m300.return_tip()

    # prepare EPM Mastermix
    xpause('''
    * put EPM Mastermix onto column 3 of the reagent plate
    * add Illumina index plate to the deck in position #3
    * empty trash if needed
    ''')

    # engage magnet, remove supernatant with parked tips, add EPM Mastermix
    ctx.comment(
        '#'*3 +
        ' capturing, removing TWB wash#3, adding EPM Mastermix ' +
        '#'*3)

    mag_module.engage(height=magnet_height)
    ctx.delay(minutes=capture_duration)
    set_speeds(m300, 15)

    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        # remove supernatant and drop tips
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_s_col+6])
        remove_sn(
            vol=55,
            index=i,
            loc=col,
            trash='waste_by_index',
            d_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m300)
        m300.drop_tip()

    ctx.comment(
        '#'*3 +
        ' removing residual supernatant TWB wash#3 (P20)' +
        '#'*3)

    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        # remove supernatant and drop tips
        m20.pick_up_tip()
        remove_sn(
            vol=10,
            index=i,
            loc=col,
            trash='waste_by_index',
            d_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m20)
        m20.drop_tip()

    ctx.comment(
        '#'*3 +
        ' adding EPM (parked tips) and mixing ' +
        '#'*3)

    # add EPM
    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        # add 20ul of epm over beads and park tips
        m20.pick_up_tip(park_tips_20.rows()[0][i+tip_park_s_col])
        m20.aspirate(20, epm, rate=0.75)
        m20.dispense(20, col, rate=0.75)
        m20.drop_tip()

    # add indexes
    ctx.comment(
        '#'*3 +
        ' adding Illumina indexes ' +
        '#'*3)

    for i, (source_col, dest_col) in enumerate(  # noqa: F501
            zip(index_plate.rows()[0][idx_s_col: idx_s_col + num_col],
                final_plate.rows()[0])):
        m20.pick_up_tip(park_tips_20.rows()[0][i+tip_park_s_col+6])
        # add indexes
        m20.mix(5, 5, source_col, rate=1.5)
        m20.aspirate(5, source_col, rate=0.75)
        m20.dispense(5, dest_col, rate=0.75)
        m20.drop_tip()

    # put plate back on position 2 and mix with m300
    mag_module.disengage()

    xpause('''
    * take the plate from the magnetic module to deck position #2
    * empty trash if needed.
    ''')

    # wait 1min for good measure
    ctx.delay(minutes=1)
    set_speeds(m300, 150)

    for i, col in enumerate(tagm_plate.rows()[0][:num_col]):
        # mix beads and park tips
        m300.pick_up_tip()
        mix_at_beads(
            vol=20,
            index=i,
            loc=col,
            iter=25,
            pip=m300)
        m300.drop_tip()

    xcomment('''
    * seal the plate with microseal-B
    * centrifuge the plate at 280g for ~30sec
    * place on the thermocycler and run the BLT PCR program
    After completion, the plate can be safely stored at +2°C to +8°C
    ''')
