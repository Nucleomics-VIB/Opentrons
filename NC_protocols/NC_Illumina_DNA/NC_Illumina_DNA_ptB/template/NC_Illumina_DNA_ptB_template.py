from opentrons.types import Point
from opentrons import protocol_api

metadata = {
    'protocolName': 'NC_Illumina_DNA_ptB',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>, \
         Stefaan Derveaux <stefaan.derveaux@vib.be>',
    'description': 'Illumina DNA part-B (8-48 samples)\
         - Clean up Libraries',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
    }

# script version 2.0; 2021_09_29 (SD)


def get_values(*names):
    import json
    _all_values = json.loads(
        """
        {
            "spl_nbr":<spl_nbr>,
            "plate_s_col":<plate_s_col>,
            "tip_park_s_col":<tip_park_s_col>,
            "asp_height":<asp_height>,
            "mm_from_s":<mm_from_s>,
            "m20_mount":"<m20_mount>",
            "m300_mount":"<m300_mount>"
        }
        """
    )
    return [_all_values[n] for n in names]


def run(ctx):

    [spl_nbr,
        plate_s_col,
        tip_park_s_col,
        asp_height,
        mm_from_s,
        m20_mount,
        m300_mount] = get_values(  # noqa: F821
            "spl_nbr",
            "plate_s_col",
            "tip_park_s_col",
            "asp_height",
            "mm_from_s",
            "m20_mount",
            "m300_mount")

    ##############
    # DEFINE DECK
    ##############

    mag_module1 = ctx.load_module(
        'magnetic module gen2',
        '4')
    mag_plate = mag_module1.load_labware(
        'biorad_96_wellplate_200ul_pcr',
        label='Plate from part#2')
    mag_module2 = ctx.load_module(
        'magnetic module gen2',
        '1')
    plate_B = mag_module2.load_labware(
        'biorad_96_wellplate_200ul_pcr',
        label='Plate B')
    reservoir = ctx.load_labware(
        'nest_12_reservoir_15ml',
        '7',
        label='Reservoir')
    tiprack20 = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in ['2']]
    tiprack200 = [ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        slot,
        label='tip_200')
            for slot in ['5', '6', '8', '9']]
    park_rack = ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        '10',
        label='Park tip_200')

    # load instrument
    m20 = ctx.load_instrument(
        'p20_multi_gen2',
        m20_mount,
        tip_racks=tiprack20)
    m300 = ctx.load_instrument(
        'p300_multi_gen2',
        m300_mount,
        tip_racks=tiprack200)

    # turn lights ON (comment out to turn OFF)
    ctx.set_rail_lights(True)

    # globally change instrument values
    magnet1_height = 8
    magnet2_height = 8

    # globally change magnetic capture duration
    #   (1 for testing, 5 for real protocol) and incubation duration
    capture_duration = 3
    incubation_duration = 5

    # reservoir
    rsb_buffer = reservoir.wells()[0]
    ethanol = reservoir.wells()[1:3]
    diluted_magbeads = reservoir.wells()[3]
    waste = reservoir.wells()[5]
    waste_by_index = reservoir.wells()[6:12]

    ####################
    # CHECK USER INPUTS
    ####################

    if not 1 <= plate_s_col <= 12:
        raise Exception("plate start column should be in range 1-12")
    if not 1 <= tip_park_s_col <= 12:
        raise Exception("tip park start column should be in range 1-12")

    spl_nbr = int(spl_nbr)
    if spl_nbr > 48:
        raise Exception("this protocol was made for up to 48 samples")
    num_col = int(spl_nbr/8)

    # shift indices to 0-based
    plate_s_col = int(plate_s_col) - 1
    tip_park_s_col = int(tip_park_s_col) - 1

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
        # empty to 'waste', 'waste_by_index', OR keep in tip
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

    def pick_up300():
        try:
            m300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace all 200ul tip racks, then click Resume")
            m300.reset_tipracks()
            m300.pick_up_tip()

    #######################
    # PROTOCOL STARTS HERE
    #######################

    # disengage both modules
    mag_module1.disengage()
    mag_module2.disengage()

    # engage, incubate, and transfer the supernatant
    #   to the right half of the same plate (col1 => col7, col2 => col8, etc)
    ctx.comment(
        '#'*3 +
        ' capturing, incubating, transfering supernatant' +
        ' from left to right half of the BLT-PCR plate ' +
        '#'*3)

    mag_module1.engage(height=magnet1_height)
    ctx.delay(minutes=5)
    set_speeds(m300, 7.5)

    for i, (s_col, d_col) in enumerate(
            zip(
                mag_plate.rows()[0][plate_s_col:plate_s_col + num_col],  # noqa: E501
                mag_plate.rows()[0][plate_s_col + 6:plate_s_col + 6 + num_col]  # noqa: E501
                )
            ):
        pick_up300()
        remove_sn(
            vol=22.5,
            index=i,
            loc=s_col,
            trash=None,
            d_asp_height=-0.5,
            extra_vol=0,
            disp_rate=0.25,
            pip=m300)
        m300.dispense(22.5, d_col)
        m300.drop_tip()

    xpause('''
    * seal the left half-plate on the magnetic module #1 (position #4)
    * empty the trash if needed.
    ''')

    # pre-mix diluted beads, add to 'right half' of the plate (A7, A8 ...)
    ctx.comment(
        '#'*3 +
        ' pre-mixing diluted beads in the reservoir (column 4),')
    ctx.comment(
        '#'*3 +
        ' adding beads to the plate right half (magnetic module #4) ')
    mag_module1.disengage()
    set_speeds(m300, 70)
    pick_up300()
    m300.mix(10, 50, diluted_magbeads)
    m300.drop_tip()

    for col in mag_plate.rows()[0][plate_s_col+6: plate_s_col+6+num_col]:  # noqa: E501
        pick_up300()
        m300.aspirate(42.5, diluted_magbeads)
        m300.dispense(42.5, col)
        m300.mix(10, 50, col)
        m300.drop_tip()

    # bind DNA to beads (gives 1mn to the last column; should be 5' in the end)
    ctx.delay(minutes=incubation_duration)

    # capture, transfer supernatant to plate B (left side)
    ctx.comment(
        '#'*3 +
        ' capturing and transfering supernatant to plate B')
    ctx.comment(
        '#'*3 +
        ' (on position #1 = magnetic module 2)')

    mag_module1.engage(height=magnet1_height)
    ctx.delay(minutes=5)

    xpause('''
    * put Plate B on the deck on mag module2 in position #1
      (wells pre-filled with 7,5µl magnetic beads)
    * please make sure that the trash is completely emptied!!!
    ''')

    set_speeds(m300, 7.5)
    for i, (s_col, d_col) in enumerate(
            zip(  # noqa: E5011
                mag_plate.rows()[0][plate_s_col+6:plate_s_col+6+num_col],
                plate_B.rows()[0][plate_s_col:plate_s_col+num_col]
                )
            ):
        pick_up300()
        remove_sn(
            vol=62.5,
            index=i,
            loc=s_col,
            trash=None,
            d_asp_height=-0.5,
            extra_vol=0,
            disp_rate=0.25,
            pip=m300)
        m300.dispense(62.5, d_col)
        set_speeds(m300, 150)
        m300.mix(20, 62, d_col)
        m300.drop_tip()

    ctx.delay(minutes=incubation_duration)
    xpause('''
    Seal the right half of the plate on the magnetic module #1 (position #4)
    ''')
    mag_module1.disengage()

    # engage magnet, remove supernatant
    ctx.comment('#'*3 + ' capturing and removing supernatant ' + '#'*3)

    mag_module2.engage(height=magnet2_height)
    ctx.delay(minutes=capture_duration)
    set_speeds(m300, 15)

    for i, s_col in enumerate(
            plate_B.rows()[0][plate_s_col:plate_s_col + num_col]  # noqa: E501
            ):
        pick_up300()
        remove_sn(
            vol=65,
            index=i,
            loc=s_col,
            trash='waste',
            d_asp_height=-0.5,
            extra_vol=0,
            disp_rate=1,
            pip=m300)
        m300.drop_tip()

    # two ethanol washes
    ctx.comment('#'*3 + ' washing twice with Ethanol ' + '#'*3)
    for wash in range(2):
        set_speeds(m300, 35)
        pick_up300()
        # alternate ethanol aspirate between two reservoirs
        for eth, sample in zip(
                ethanol*num_col,
                plate_B.rows()[0][plate_s_col:plate_s_col + num_col]  # noqa: E501
                ):
            m300.aspirate(185, eth)
            ctx.delay(seconds=1.5)
            m300.dispense(185, sample.top())
            ctx.delay(seconds=2.5)
        m300.drop_tip()
        ctx.delay(seconds=1)
        set_speeds(m300, 15)

        for i, sample in enumerate(
                plate_B.rows()[0][plate_s_col:plate_s_col+num_col]  # noqa: E501
                ):
            pick_up300()
            remove_sn(
                vol=60,
                index=i,
                loc=sample,
                trash=None,
                d_asp_height=4.0,
                extra_vol=0,
                disp_rate=2.0,
                pip=m300)
            # aspirate remaining 140uL and drop the tip with ethanol in it
            remove_sn(
                vol=140,
                index=i,
                loc=sample,
                trash=None,
                d_asp_height=-0.5,
                extra_vol=60,
                disp_rate=2.0,
                pip=m300)
            m300.drop_tip()

    xpause('''
    Please empty the trash !!!
    ''')

    # remove excess with p20
    ctx.comment('#'*3 + ' removing  Ethanol leftover with m20 ' + '#'*3)
    for i, sample in enumerate(
            plate_B.rows()[0][plate_s_col:plate_s_col + num_col]  # noqa: E501
            ):
        m20.pick_up_tip()
        remove_sn(
            vol=20,
            index=i,
            loc=sample,
            trash='waste',
            d_asp_height=-1.0,
            extra_vol=0,
            disp_rate=1.0,
            pip=m20)
        m20.drop_tip()

    # evaporate residual Ethanol then add RSB
    ctx.delay(minutes=5)

    # add RSB (temporary 33µl; maybe 32µl would be feasible too)
    ctx.comment('#'*3 + ' adding RSB to plate B in position #1 ' + '#'*3)
    for i, sample in enumerate(
            plate_B.rows()[0][plate_s_col:plate_s_col+num_col]  # noqa: E501
            ):
        set_speeds(m300, 15)
        m300.pick_up_tip(park_rack.rows()[0][i+tip_park_s_col+6])
        m300.aspirate(33, rsb_buffer)
        m300.dispense(33, sample)
        m300.return_tip()

    # resuspend beads
    ctx.comment('#'*3 + ' resuspend beads ' + '#'*3)
    mag_module2.disengage()

    # give one more minute to first column
    ctx.delay(minutes=1)
    set_speeds(m300, 100)

    for i, sample in enumerate(
            plate_B.rows()[0][plate_s_col:plate_s_col + num_col]  # noqa: E501
            ):
        m300.pick_up_tip(park_rack.rows()[0][i+tip_park_s_col+6])
        mix_at_beads(
            vol=28,
            index=i,
            loc=sample,
            iter=15,
            pip=m300)
        m300.drop_tip()

    # give one more minute to last column
    ctx.delay(minutes=2)

    # capture, transfer eluate to plate B (right side !!)
    ctx.comment(
        '#'*3 +
        ' capturing and transferring library ')
    ctx.comment(
        '#'*3 +
        ' to right side of plate B in position #1 ')

    mag_module2.engage(height=magnet2_height)
    ctx.delay(minutes=capture_duration)
    set_speeds(m20, 10)

    for i, (s_col, d_col) in enumerate(
            zip(
                plate_B.rows()[0][plate_s_col:plate_s_col + num_col],  # noqa: E501
                plate_B.rows()[0][plate_s_col + 6:plate_s_col + 6 + num_col]  # noqa: E501
                )
            ):
        m20.pick_up_tip()
        # transfer twice 15uL with m20 (same tips)
        for _ in range(2):
            remove_sn(
                vol=15,
                index=i,
                loc=s_col,
                trash=None,
                d_asp_height=-0.5,
                extra_vol=0,
                disp_rate=1.0,
                pip=m20)
            m20.dispense(15, d_col)
        m20.drop_tip()

    xcomment('''
    All done!
    The library is now in the right half of plate B in position #1
    ''')
