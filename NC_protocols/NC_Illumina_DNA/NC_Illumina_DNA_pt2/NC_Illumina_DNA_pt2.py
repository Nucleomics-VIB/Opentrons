def get_values(*names):
    import json
    _all_values = json.loads("""{"num_samp":16,"asp_height":1,"length_from_side":3,"index_start_col":1,"tip_park_start_col":1,"m20_mount":"left","m300_mount":"right"}""")
    return [_all_values[n] for n in names]


from opentrons.types import Point

metadata = {
    'protocolName': 'NC_Illumina_DNA_pt2',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>, Stefaan Derveaux <stefaan.derveaux@vib.be>',
    'description': 'Illumina DNA part2 (16 samples) - Post Tagmentation Cleanup',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}

# script version 1.0; 2021_08_11 (SD)

def run(ctx):

    [num_samp, index_start_col, tip_park_start_col,
        asp_height, length_from_side,
        m20_mount, m300_mount] = get_values(  # noqa: F821
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
    mag_module = ctx.load_module('magnetic module gen2', '1')
    sample_plate = mag_module.load_labware('biorad_96_wellplate_200ul_pcr', label='Sample Plate')
    reagent_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '2', label='Reagent Plate')
    index_plate = ctx.load_labware('illumina_96_wellplate_200ul', '3', label='Index Plate')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '4')
    tiprack_20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in ['5', '6']]
    park_tips_300 = ctx.load_labware('opentrons_96_filtertiprack_200ul', '7',  label='Park Tips')
    park_tips_20 = ctx.load_labware('opentrons_96_filtertiprack_20ul', '9', label='Park Tips')
    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                for slot in ['8', '11']]
    park2_tips_300 = ctx.load_labware('opentrons_96_filtertiprack_200ul', '10', label='Park2 Tips')

    # load instrument (remove_supernatant20 toegevoegd)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, 
                               tip_racks=tiprack_20)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tiprack300)

    # turn lights ON (comment out to turn OFF)
    ctx.set_rail_lights(True)

    # define custom routines
    def change_speeds(pip, speed):
        pip.flow_rate.aspirate = speed
        pip.flow_rate.dispense = speed

    def remove_supernatant(vol, index, loc):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height-1).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        m300.aspirate(vol, aspirate_loc)
        m300.dispense(vol, waste)
        m300.blow_out()

    def remove_supernatantp20(vol, index, loc):
        side = -1 if index % 2 == 0 else 1
        aspirate_loc = loc.bottom(z=asp_height-1).move(
                Point(x=(loc.diameter/2-length_from_side)*side))
        m20.aspirate(vol, aspirate_loc)
        m20.dispense(vol, waste)
        m20.blow_out()

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
    twb = reservoir.wells()[1]
    tsb = reagent_plate.rows()[0][1]
    epm = reagent_plate.rows()[0][2]
    waste = reservoir.wells()[5]
    waste_2 = reservoir.wells()[4]
    waste_3 = reservoir.wells()[3]

    # transfer TSB from mastermix plate to sample plate
    ctx.comment('#'*80,'\n# transfer TSB from mastermix plate to sample plate in position \n', '#'*80, '\n')
    for col in sample_plate.rows()[0][:num_col]:
        m20.pick_up_tip()
        m20.aspirate(5, tsb)
        m20.dispense(5, col)
        m20.mix(9, 17, col, rate=2.0)
        m20.mix(1, 17, col, rate=0.5)
        m20.drop_tip()

    ctx.pause(
        '''
        seal plate B with Microseal
        transfer the plate to the thermocycler and run the PTC program. 
        return the PCR plate to the magnetic module.
        empty the trash if needed.
        select "Resume" in the Opentrons App.
        '''
        )

    # engage magnet, remove supernatant, add TWB 1
    ctx.comment('#'*80,'\n# capture, remove SN, add TWB wash#1 \n', '#'*80, '\n')
    mag_module.engage()
    ctx.delay(minutes=1)

    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 15)
        m300.pick_up_tip()
        remove_supernatant(35, i, col)
        m300.drop_tip()

        # add 50ul of twb over beads
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col])
        m300.aspirate(50, twb)
        m300.dispense(50, col)
        m300.return_tip()

    # disengage magnet, and mix at bead location
    mag_module.disengage()
    for i, col in enumerate(sample_plate.rows()[0][:num_col]): 
        change_speeds(m300, 35)
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col])
        mix_at_beads(20, i, col)
        m300.drop_tip()

    # engage magnet, remove supernatant, add TWB 2
    ctx.comment('#'*80,'\n# capture, remove SN, add TWB wash#2 \n', '#'*80, '\n')
    mag_module.engage()
    ctx.delay(minutes=1)


    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 15)
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col+6])
        remove_supernatant(55, i, col)
        m300.return_tip()
        # add 50ul of twb over beads
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col])
        m300.aspirate(50, twb)
        m300.dispense(50, col)
        m300.return_tip()
            
    mag_module.disengage()
    # mix at bead location
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 35)
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col])
        mix_at_beads(20, i, col)
        m300.drop_tip()

    # engage magnet, remove supernatant, add TWB 3
    ctx.comment('#'*80,'\n# capture, remove SN, add TWB wash#3 \n', '#'*80, '\n')
    mag_module.engage()
    ctx.delay(minutes=1)

    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 15)
        m300.pick_up_tip(park_tips_300.rows()[0][i+tip_park_start_col+6])
        remove_supernatant(55, i, col)
        m300.drop_tip()
        # add 50ul of twb over beads
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col+6])
        m300.aspirate(50, twb)
        m300.dispense(50, col)
        m300.return_tip()
            
    mag_module.disengage()
    # mix at bead location
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 35)
        m300.pick_up_tip(park2_tips_300.rows()[0][i+tip_park_start_col+6])
        mix_at_beads(20, i, col)
        m300.drop_tip()

    # prepare EPM Mastermix
    ctx.pause(
        '''
        Put EPM Mastermix onto columns 3 and 4 of the reagent plate.
        Add Illumina index plate to the deck.
        Empty trash if needed.
        Click on "Resume" in the Opentrons App.
        '''
        )

    # engage magnet, remove supernatant, add EPM Mastermix
    ctx.comment('#'*80,'\n# capture, remove SN, add EPM Mastermix \n', '#'*80, '\n')
    mag_module.engage()
    ctx.delay(minutes=1)

    ctx.comment('\n remove supernatant TWB wash#3 (P300)\n')
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m300, 15)
        m300.pick_up_tip()
        remove_supernatant(55, i, col)
        m300.drop_tip()

    ctx.comment('\n remove residual supernatant TWB wash#3 (P20)\n')
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        m20.pick_up_tip()
        remove_supernatantp20(10, i, col)
        m20.drop_tip()

    ctx.comment('#'*80,'\n# add EPM (parke tips), mix EPM \n', '#'*80, '\n')
    # add EPM
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        m20.pick_up_tip(park_tips_20.rows()[0][i+tip_park_start_col])
        m20.aspirate(20, epm, rate=0.75)
        m20.dispense(20, col, rate=0.75)
        m20.return_tip()

    # mix epm
    mag_module.disengage()
    for i, col in enumerate(sample_plate.rows()[0][:num_col]):
        change_speeds(m20, 20)
        m20.pick_up_tip(park_tips_20.rows()[0][i+tip_park_start_col])
        m20.mix(10, 18, col)
        m20.drop_tip()
        
    # add indexes
    ctx.comment('#'*80,'\n# add Illumina indexes \n', '#'*80, '\n')
    for source_col, dest_col in zip(index_plate.rows()[0][
                                                          index_start_col:
                                                          index_start_col
                                                          + num_col],
                                    sample_plate.rows()[0]):
        m20.pick_up_tip()
        m20.aspirate(5, source_col, rate=0.75)
        m20.dispense(5, dest_col, rate=0.75)
        change_speeds(m20, 20)
        m20.mix(10, 18, dest_col)
        m20.drop_tip()
    
    ctx.comment('\n All done, sample plate in position #1 is ready for protocol part-3 \n')
