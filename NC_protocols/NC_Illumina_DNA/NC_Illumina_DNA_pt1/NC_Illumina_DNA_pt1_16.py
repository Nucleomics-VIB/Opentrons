def get_values(*names):
    import json
    _all_values = json.loads("""{"num_samp":16,"p300_tip_start_col":1,"m20_mount":"left","m300_mount":"right"}""")
    return [_all_values[n] for n in names]


metadata = {
    'protocolName': 'NC_Illumina_DNA_pt1_16',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>, Stefaan Derveaux <stefaan.derveaux@vib.be>',
    'description': 'Illumina DNA part1 for 16 samples - Tagment DNA',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}

# script version 1.0; 2021_08_11 (SD)

def run(ctx):

    # get user inputs
    [num_samp, p300_tip_start_col,
        m20_mount, m300_mount] = get_values(  # noqa: F821
      "num_samp", "p300_tip_start_col", "m20_mount", "m300_mount")

    # check p300_tip_start_col in valid range
    if not 1 <= p300_tip_start_col <= 12:
        raise Exception("Enter a 200ul tip start column 1-12")

    num_samp = int(num_samp)
    num_col = int(num_samp/8)
    p300_tip_start_col = p300_tip_start_col

    # load labware
    # magnetic module gen2: 1, biorad_96_wellplate_200ul_pcr
    # biorad_96_wellplate_200ul_pcr: 2
    # biorad_96_wellplate_200ul_pcr: 3
    # nest_12_reservoir_15ml: 4
    # opentrons_96_filtertiprack_20ul 5, 6, 7
    # opentrons_96_filtertiprack_200ul: 8
    mag_module = ctx.load_module('magnetic module gen2', '1')
    reagent_plate = mag_module.load_labware('biorad_96_wellplate_200ul_pcr', label='Mastermix Plate')
    samples = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '2',  label='Sample Plate')
    final_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '3', label='Final Plate')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '4')
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
               for slot in ['5', '6', '7']]
    tiprack300 = ctx.load_labware('opentrons_96_filtertiprack_200ul', '8')

    # load instrument
    # p20_multi_gen2: left, tiprack20 (3)
    # p300_multi_gen2: right, tiprack300 (1)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, 
                                tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=[tiprack300])

    # turn lights ON (comment out to turn OFF)
    ctx.set_rail_lights(True)

    # reagents
    mastermix = reagent_plate.rows()[0][0]
    water = reservoir.wells()[0]
    waste = reservoir.wells()[5]

    # add water to empty biorad plate
    ctx.comment('#'*80,'\n# add water to empty plate \n', '#'*80, '\n')
    m20.pick_up_tip()
    for col in final_plate.rows()[0][:num_col]:
        m20.aspirate(10, water)
        m20.dispense(10, col)
    m20.drop_tip()
    ctx.comment('\n    done     \n')

    # add dna to plate
    ctx.comment('#'*80,'\n# add DNA to empty final plate \n', '#'*80, '\n')
    for i, (dna, dest) in enumerate(zip(samples.rows()[0],
                                    final_plate.rows()[0][:num_col])):
        m20.pick_up_tip()
        m20.mix(10, 15, dna, rate=2.0)
        m20.aspirate(5, dna)
        m20.dispense(5, dest)
        m20.mix(5, 10, dest, rate=2.0)
        m20.drop_tip()
    ctx.comment('\n    done     \n')

    # add mastermix to plate
    ctx.comment('#'*80,'\n# add mastermix to final plate \n', '#'*80, '\n')
    m20.flow_rate.aspirate = 4
    m20.flow_rate.dispense = 4

    for i, col in enumerate(final_plate.rows()[0][:num_col]):
        if i % 3 == 0:
            m300.pick_up_tip(tiprack300.rows()[0][p300_tip_start_col-1])
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
    
    ctx.comment('\n All done, plate ready for protocol part-2 \n')
