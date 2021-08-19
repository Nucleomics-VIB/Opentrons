def get_values(*names):
    import json
    _all_values = json.loads(
        """
        {
        "num_samp":16,
        "plate_A_start_col":1,
        "plate_C_start_col":1,
        "tip_park_start_col":1,
        "asp_height":1,
        "length_from_side":2.0,
        "m20_mount":"left",
        "m300_mount":"right"
        }
        """
    )
    return [_all_values[n] for n in names]


from opentrons.types import Point
from opentrons import protocol_api


metadata = {
    'protocolName': 'NC_Illumina_DNA_pt3',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>, \
        Stefaan Derveaux <stefaan.derveaux@vib.be>',
    'description': 'Illumina DNA part3 (16 samples) - Clean up Libraries',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
    }

# script version 1.1; 2021_08_18 (SD)

def run(ctx):

    [num_samp, 
    plate_A_start_col, 
    plate_C_start_col,
    tip_park_start_col, 
    asp_height,
    length_from_side, 
    m20_mount, 
    m300_mount] = get_values(  # noqa: F821
      "num_samp", 
      "plate_A_start_col", 
      "plate_C_start_col", 
      "tip_park_start_col", 
      "asp_height",
      "length_from_side", 
      "m20_mount", 
      "m300_mount")

    # test user inputs
    if not 1 <= plate_A_start_col <= 12:
        raise Exception("Enter a plate_A_start_col 1-12")
    #if not 1 <= plate_B_start_col <= 12:
    #    raise Exception("Enter a plate_B_start_col 1-12")
    if not 1 <= plate_C_start_col <= 12:
        raise Exception("Enter a plate_C_start_col 1-12")
    if not 1 <= tip_park_start_col <= 12:
        raise Exception("Enter a tip_park_start_col 1-12")
        
    num_samp = int(num_samp)
    if num_samp > 48:
        raise Exception("this protocol was made for up to 48 samples")
    num_col = int(num_samp/8)
    # shift index to 0-based
    plate_A_start_col = int(plate_A_start_col) - 1
    plate_C_start_col = int(plate_C_start_col) - 1
    tip_park_start_col = int(tip_park_start_col) - 1

    # load labware
    mag_module = ctx.load_module('magnetic module gen2', 
        '1')
    mag_plate = mag_module.load_labware('biorad_96_wellplate_200ul_pcr', 
        label='Plate from part#2')
    plate_B = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 
        '2', 
        label='Plate B')
    plate_C = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 
        '3', 
        label='Plate C')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 
        '4', 
        label='Reservoir')
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', 
        slot, 
        label='tip_20')
            for slot in ['6']]
    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', 
        slot, 
        label='tip_200')
            for slot in ['5', '7', '8', '9']]
    park_rack = ctx.load_labware('opentrons_96_filtertiprack_200ul', 
        '10', 
        label='Park tip_200')

    # load instrument
    m300 = ctx.load_instrument('p300_multi_gen2', 
        m300_mount,
        tip_racks=tiprack200)
    m20 = ctx.load_instrument('p20_multi_gen2', 
        m20_mount, 
        tip_racks=tiprack20)

    # turn lights ON (comment out to turn OFF)
    ctx.set_rail_lights(True)
    
    # globally change instrument values
    magnet_height = 11

    # globally change magnetic capture duration (1 for testing)
    capture_duration = 1
    
    def change_speeds(pip, speed):
        pip.flow_rate.aspirate = speed
        pip.flow_rate.dispense = speed

    def pick_up300():
        try:
            m300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace all 200ul tip racks, then click Resume")
            m300.reset_tipracks()
            m300.pick_up_tip()

    # universal removal with defaults: 
    #   delta_asp_height=-0.5 # (0.5mm below the top, in other steps set to 4mm above)
    #   pip=m300 # (tip_200 multi-chanel)
    #   extra_vol=0 # dispense an extra 60microL to empty tips in one step)
    def remove_supernatant_uni(vol, index, loc, trash=False, delta_asp_height=-0.5, extra_vol=0, disp_rate=1, pip=m300):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height+delta_asp_height).move(
            Point(x=(loc.diameter/2-length_from_side)*side))
        pip.aspirate(vol, aspirate_loc)
        if trash:
            #vol2=vol+extra_vol
            #pip.dispense(vol2, waste_by_index[index].top(z=-5), rate=disp_rate)
            pip.blow_out(waste_by_index[index].top(z=-5), rate=disp_rate)

    # standard removal from aspiration height -0.5mm
    def remove_supernatant(vol, index, loc, trash=False, pip=m300):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height-0.5).move(
            Point(x=(loc.diameter/2-length_from_side)*side))
        pip.aspirate(vol, aspirate_loc)
        if trash:
            pip.dispense(vol, waste2.top(z=-5))
            pip.blow_out()

    # removal from aspiration height + 4mm
    def remove_supernatantTOP(vol, index, loc, trash=False, pip=m300):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height+4).move(
            Point(x=(loc.diameter/2-length_from_side)*side))
        pip.aspirate(vol, aspirate_loc)
        if trash:
            pip.dispense(vol, waste.top(z=-5))
            pip.blow_out()
    
    # removal from the aspiration height -0.5mm
    def remove_supernatantBOT(vol, index, loc, trash=False, pip=m300):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height-0.5).move(
            Point(x=(loc.diameter/2-length_from_side)*side))
        pip.aspirate(vol, aspirate_loc)
        if trash:
            vol2=vol+60
            pip.dispense(vol2, waste.top(z=-5), rate=5)
            pip.blow_out()

    # remove residual ethanol with p20 tips
    def remove_supernatantp20(vol, index, loc, trash=False, pip=m20):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height-0.5).move(
            Point(x=(loc.diameter/2-length_from_side)*side))
        pip.aspirate(vol, aspirate_loc)
        if trash:
            pip.dispense(vol, waste2.top(z=-5))
            pip.blow_out()
    
    def mix_at_beads(vol, index, loc):
        side = 1 if index % 2 == 0 else -1
        aspirate_loc = loc.bottom(z=asp_height).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        dispense_loc = loc.bottom(z=asp_height).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        for _ in range(15):
            m300.aspirate(vol, aspirate_loc)
            m300.dispense(vol, dispense_loc)

    # reagents
    rsb_buffer = reservoir.wells()[3]
    ethanol = reservoir.wells()[4:6]
    diluted_magbeads = reservoir.wells()[7]
    waste = reservoir.wells()[11]
    waste2 = reservoir.wells()[10]
    # waste_by_index = reservoir.wells()[6:11]

    # engage, incubate, and transfer the supernatant to the right half of the same plate (col1 => col7, col2 => col8, etc)
    ctx.comment('#'*3 
        + ' capture, incubate, transfer supernatant the left half to the right half of the BLT-PCR plate ' 
        + '#'*3)
    mag_module.engage(height=magnet_height)
    ctx.delay(minutes=capture_duration)
    for i, (s_col, d_col) in enumerate(
        zip(
            mag_plate.rows()[0][plate_A_start_col: 
                plate_A_start_col+ num_col],
            mag_plate.rows()[0][plate_A_start_col + 6: 
                plate_A_start_col + 6 + num_col]
            )
        ):
        change_speeds(m300, 15)
        pick_up300()
        remove_supernatant(22.5, i, s_col)
        m300.dispense(22.5, d_col)
        m300.drop_tip()

    ctx.pause(
        '''
        Seal the left half-plate on the magnetic module (position #1)? 
        Ensure Plate B is on the deck in position #2 and filled with magnetic beads. 
        Empty the trash if needed. 
        Select "Resume" in the Opentrons App. 
        '''
        )

    # pre-mix diluted beads, add to 'right side' of the sample plate (A7, A8 ...)
    ctx.comment('#'*3 
        + ' pre-mix diluted beads in the reservoir, add beads to the right side of the plate on the magnetic module (position #1) ' 
        + '#'*3)
    mag_module.disengage()  
    change_speeds(m300, 70)
    pick_up300()
    m300.mix(10, 50*num_col, diluted_magbeads)
    m300.drop_tip()

    for col in mag_plate.rows()[0][plate_A_start_col+6: plate_A_start_col+6+num_col]:
        pick_up300()
        m300.aspirate(42.5, diluted_magbeads)
        m300.dispense(42.5, col)
        m300.mix(10, 50, col)
        m300.drop_tip()

    # bind DNA to beads (gives 1mn to the last column)
    ctx.delay(minutes=1)

    # capture, transfer supernatant to plate B (left side)
    ctx.comment('#'*3 
        + ' capture, transfer supernatant to plate B (on position #2) ' 
        + '#'*3)
    mag_module.engage(height=magnet_height)
    ctx.delay(minutes=capture_duration)
    for i, (s_col, d_col) in enumerate(zip(
            mag_plate.rows()[0][plate_A_start_col+6:
                plate_A_start_col+6+num_col],
            plate_B.rows()[0][plate_A_start_col:
                plate_A_start_col+num_col]
            )
        ):
        change_speeds(m300, 15)
        pick_up300()
        remove_supernatant(62.5, i, s_col)
        m300.dispense(62.5, d_col)
        change_speeds(m300, 70)
        m300.mix(10, 55, d_col)
        m300.drop_tip()
    ctx.delay(minutes=1)
    ctx.pause(
        ''' 
        Seal the right half of the plate on the magnetic module (position #1). 
        Select "Resume" in the Opentrons App. 
        '''
        )
    mag_module.disengage()

    ctx.pause(
        '''
        Remove the plate from the magnetic module in position #1. 
        Replace with the plate from position #2. 
        Add at least 5ml 70% ethanol to reservoir (columns 4, 5, and 6). 
        Add at least 2ml RSB to reservoir (column 3). 
        Empty the trash if needed. 
        Select "Resume" in the Opentrons App. 
        '''
        )

    # engage magnet, remove supernatant
    ctx.comment('#'*3 + ' capture, remove supernatant ' + '#'*3)
    mag_module.engage(height=magnet_height)
    ctx.delay(minutes=capture_duration)
    for i, s_col in enumerate(
            mag_plate.rows()[0][plate_A_start_col:
                plate_A_start_col + num_col]
            ):
        change_speeds(m300, 15)
        pick_up300()
        remove_supernatant(65, i, s_col, trash=True)
        m300.drop_tip()

    # two ethanol washes
    ctx.comment('#'*3 + ' wash twice with Ethanol ' + '#'*3)
    for wash in range(2):
        change_speeds(m300, 35)
        pick_up300()
        for eth, sample in zip(
            ethanol*num_col,
            mag_plate.rows()[0][plate_A_start_col:
                plate_A_start_col + num_col]
            ):
            m300.aspirate(185, eth)
            ctx.delay(seconds=1.5)
            m300.dispense(185, sample.top())
            ctx.delay(seconds=2.5)
        m300.drop_tip()
        ctx.delay(seconds=10)
        for i, sample in enumerate(
            mag_plate.rows()[0][plate_A_start_col:
                plate_A_start_col+num_col]
            ):
            m300.pick_up_tip(park_rack.rows()[0][i+tip_park_start_col])
            change_speeds(m300, 15)
            remove_supernatantTOP(60, i, sample)
            remove_supernatantBOT(140, i, sample, trash=True)
            if wash == 0:
                m300.return_tip()
            else:
                m300.drop_tip()

    # remove excess with p20
    ctx.comment('#'*3 + ' remove leftover Ethanol with p20 ' + '#'*3)
    for i, sample in enumerate(
        mag_plate.rows()[0][plate_A_start_col:
            plate_A_start_col + num_col]
        ):
        m20.pick_up_tip()
        remove_supernatantp20(20, i, sample, pip=m20)
        m20.drop_tip()

    # evaporate residual Ethanol then add RSB
    ctx.delay(minutes=5)

    # add RSB (temporary 33µl; maybe 32µl would be feasible too)
    ctx.comment('#'*3 + ' add RSB to plate B in position #1 ' + '#'*3)
    for i, sample in enumerate(
        mag_plate.rows()[0][plate_A_start_col:
            plate_A_start_col+num_col]
        ):
        change_speeds(m300, 15)
        m300.pick_up_tip(park_rack.rows()[0][i+tip_park_start_col+6])
        m300.aspirate(33, rsb_buffer)
        m300.dispense(33, sample)
        m300.return_tip()

    ctx.pause('''
        Empty the trash if needed. 
        Select "Resume" in the Opentrons App. 
        '''
        )

    # resuspend beads
    ctx.comment('#'*3 + ' resuspend beads ' + '#'*3)
    mag_module.disengage()
    for i, sample in enumerate(
        mag_plate.rows()[0][plate_A_start_col:
            plate_A_start_col + num_col]
        ):
        change_speeds(m300, 70)
        m300.pick_up_tip(park_rack.rows()[0][i+tip_park_start_col+6])
        mix_at_beads(25, i, sample)
        m300.drop_tip()

    # give one more minute to last column
    ctx.delay(minutes=1)

    # capture, transfer elutate to plate C
    ctx.comment('#'*3
        + 'capture, transfer supernatant (library) to plate C in position #3 ' 
        + '#'*3)
    mag_module.engage(height=magnet_height)
    ctx.delay(minutes=capture_duration)

    for i, (s_col, d_col) in enumerate(
            zip(
                mag_plate.rows()[0][plate_A_start_col:
                    plate_A_start_col + num_col],
                plate_C.rows()[0][plate_C_start_col:
                    plate_C_start_col + num_col]
                )
            ):
        change_speeds(m20, 5)
        m20.pick_up_tip()
        remove_supernatant(15, i, s_col, pip=m20)
        m20.dispense(15, d_col)
        remove_supernatant(15, i, s_col, pip=m20)
        m20.dispense(15, d_col)
        m20.drop_tip()

    ctx.comment('\n All done, plate C in position #3 is ready for sequencing \n')
