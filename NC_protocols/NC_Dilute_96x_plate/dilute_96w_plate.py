from opentrons import protocol_api
import math
import csv

metadata = {
        'protocolName': 'dilute_96w_plate',
        'author': 'nucleomics@vib.be',
        'description': 'dilute wells from 96w_plate to new plate from CSV \
            (+ optional intermediate dilution for concentrated samples)',
        'source': 'VIB Nucleomics',
        'apiLevel': '2.10'
        }

# template version 1.0b; 2022_11_29 (SP)
# edit date 

def get_values(*names):
    import json
    _all_values = json.loads("""{
        "sp_type":"biorad_96_wellplate_200ul_pcr",
        "tp_type":"biorad_96_wellplate_200ul_pcr",
        "dp_type":"biorad_96_wellplate_200ul_pcr",
        "tube_rack":"opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap",
        "buf_vol":"1000.0",
        "min_vol":"2",
        "max_vol":"100.0",
        "max_dil":"20.0",
        "min_fin":"10.0",
        "pspeed":"7.56",
        "mix_times":"4",
        "uploaded_csv":"Position,Value,Dilution\\nA1,2.5,1\\nB1,5,1.0\\nC1,2.5,10.0\\nD1,2.5,80.0\\nE1,20,50.0\\nF1,2.5,10.0\\nG1,2.5,80.0\\nH1,20,50.0"
        }""")
    return [_all_values[n] for n in names]

def run(ctx: protocol_api.ProtocolContext):
    [sp_type,
        tp_type,
        dp_type,
        tube_rack,
        buf_vol,
        min_vol,
        max_vol,
        max_dil,
        min_fin,
        pspeed,
        mix_times,
        uploaded_csv
        ] = get_values(    # noqa: F821
        'sp_type',
        'tp_type',
        'dp_type',
        'tube_rack',
        'buf_vol',
        'min_vol',
        'max_vol',
        'max_dil',
        'min_fin',
        'pspeed',
        'mix_times',
        'uploaded_csv')

    # light be
    ctx.set_rail_lights(True)
    # ctx.delay(seconds=10)

    # source 96w plate on pos 1
    source_plate = ctx.load_labware(
        sp_type,
        '1',
        'source_plate')

    # empty dilution 96w plate on pos 5
    dilution_plate = ctx.load_labware(
        dp_type,
        '4',
        'dilution_plate')

    # empty 96w plate on pos 2
    target_plate = ctx.load_labware(
        tp_type,
        '2',
        'target_plate')

    # tube rack on pos #4
    tuberack = ctx.load_labware(tube_rack, '4')
    
    # buffer tubes on top row [A1 A2 A3 A4 A5 A6]
    buffer_wells = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6']
    bufferidx = 1
    buffer = tuberack.wells_by_name()[buffer_wells[bufferidx-1]]

    # provision enough p20 tips for 2 plate
    slots20 = ['7', '8']
    tips20 = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in slots20]

    # provision enough p200 tips for 2 plate
    slots200 = ['10', '11']
    tips300 = [ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        slot,
        label='tip_300')
            for slot in slots200]

    # define pipettes
    pipette20s = ctx.load_instrument(
        'p20_single_gen2',
        'left',
        tip_racks=tips20)

    pipette300s = ctx.load_instrument(
        'p300_single_gen2',
        'right',
        tip_racks=tips300)

    # volume of used buffer
    global buffer_counter
    buffer_counter = float(0.0)

    # number of buffer tubes required for this experiment
    bufferslots = 1 

    # define *global value for next dilution well
    # to be incremented after each two-step dilution
    global next_dil_well
    next_dil_well = 0

    ###########
    # routines
    ###########

    def set_speeds(pip, aspeed, dspeed=None, bspeed=None):
        pip.flow_rate.aspirate = aspeed
        pip.flow_rate.dispense = dspeed if dspeed is not None else aspeed
        pip.flow_rate.blow_out = bspeed if bspeed is not None else aspeed

    def reset_speeds(pip):
        pip.flow_rate.set_defaults(ctx.api_version)

    #################################################################
    #  a volume of sample is directly transferred to the target plate
    #################################################################
    def direct_transfer_no_dilution(one_pos, one_vol, one_dil):

        # pipet one_vol to target plate
        ctx.comment(
            '\n\n' + '#'*3 + ' transferring ' + str(one_vol) +
            'ul from ' + one_well + ' to the target plate')

        # choose pipet
        if one_vol <= 20.0:
            usedpip = "p20"
            s_pipette = pipette20s
        else:
            usedpip = "p300"
            s_pipette = pipette300s

        # transfer one_vol (undiluted) to target plate
        s_pipette.pick_up_tip()
        s_pipette.transfer(
            one_vol,
            source_plate.wells_by_name()[one_pos],
            target_plate.wells_by_name()[one_pos],
            blow_out=True,
            blowout_location='destination well'
            )
        s_pipette.drop_tip()

    ###################################################
    # a volume of sample is diluted in the target plate
    ###################################################
    def direct_transfer_one_dilution(one_pos, one_vol, one_dil):
    
        # calculate buffer volume needed
        buffer_vol = (one_volume*one_dil)-one_vol
        
        # test if enough buffer in current tube_rack else take next
        buffer_counter += buffer_vol
        if buffer_counter > buf_vol:
            # use next buffer tube
            bufferidx += 1
            buffer = tuberack.wells_by_name()[buffer_wells[bufferidx-1]]
            # deduct from new tube
            buffer_counter = buffer_vol
        
        # choose pipet
        if buffer_vol <= 20.0:
            usedpip = "p20"
            s_pipette = pipette20s
        else:
            usedpip = "p300"
            s_pipette = pipette300s

        # transfer buffer_vol to target plate
        s_pipette.pick_up_tip()
        s_pipette.transfer(
            buffer_vol,
            buffer,
            target_plate.wells_by_name()[one_pos],
            blow_out=True,
            blowout_location='destination well'
            )
        s_pipette.drop_tip()
        
        # transfer sample in same well and mix_after
        # choose pipet
        if one_vol <= 20.0:
            usedpip = "p20"
            s_pipette = pipette20s
        else:
            usedpip = "p300"
            s_pipette = pipette300s
    
        s_pipette.pick_up_tip()
        s_pipette.transfer(
            one_vol,
            source_plate.wells_by_name()[one_pos],
            target_plate.wells_by_name()[one_pos],
            blow_out=False
            )
        s_pipette.mix(
            mix_times, 
            one_vol, 
            target_plate.wells_by_name()[one_pos])
        s_pipette.drop_tip()    
    
    ################################################################
    # dilute a volume of sample max_dil times in the dilution plate 
    # then further diluted the dilution in the target plate
    ################################################################
    def step_transfer_two_dilutions(one_pos, one_vol, one_dil, max_dil, min_fin):
    
        # pre-dilute max_dil times
        buffer_vol = (max_dil - 1) * one_vol
        
        # test if enough buffer in current tube_rack else take next
        buffer_counter += buffer_vol
        if buffer_counter > buf_vol:
            # use next buffer tube
            bufferidx += 1
            buffer = tuberack.wells_by_name()[buffer_wells[bufferidx-1]]
            # deduct from new tube
            buffer_counter = buffer_vol
        
        # first add buffer to dilution well
        # choose pipet
        if buffer_vol <= 20.0:
            usedpip = "p20"
            s_pipette = pipette20s
        else:
            usedpip = "p300"
            s_pipette = pipette300s
        
        s_pipette.pick_up_tip()
        s_pipette.transfer(
            buffer_vol,
            buffer,
            dilution_plate.wells()[dil_well],
            blow_out=True,
            blowout_location='destination well'
            )
        s_pipette.drop_tip() 
        
        # then add sample to it and mix
        # choose pipet
        if one_vol <= 20.0:
            usedpip = "p20"
            s_pipette = pipette20s
        else:
            usedpip = "p300"
            s_pipette = pipette300s       
        
        s_pipette.pick_up_tip()
        s_pipette.transfer(
            one_vol,
            source_plate.wells_by_name()[one_pos],
            dilution_plate.wells()[dil_well],
            blow_out=False
            )
        s_pipette.mix(
            mix_times, 
            one_vol, 
            dilution_plate.wells()[dil_well],
        s_pipette.drop_tip()
        
        # then add buffer to target plate for remaining dilution (one_dil / max_dil)
        # with a minimal volume of min_fin uL
        sec_dil = float(one_dil/max_dil)
        buffer_vol = float(min_fin - (min_fin / sec_dil))
        
        # test if enough buffer in current tube_rack else take next
        buffer_counter += buffer_vol
        if buffer_counter > buf_vol:
            # use next buffer tube
            bufferidx += 1
            buffer = tuberack.wells_by_name()[buffer_wells[bufferidx-1]]
            # deduct from new tube
            buffer_counter = buffer_vol

        # choose pipet
        if two_vol <= 20.0:
            usedpip = "p20"
            s_pipette = pipette20s
        else:
            usedpip = "p300"
            s_pipette = pipette300s   
            
        s_pipette.pick_up_tip()
        s_pipette.transfer(
            buffer_vol,
            buffer,
            target_plate.wells_by_name()[one_pos]),
            blow_out=True,
            blowout_location='destination well'
            )
        s_pipette.drop_tip() 
        
        # finally add 10uL diluted volume to target wells
        dil_vol = 10.0
        s_pipette = pipette20s
        
        s_pipette.pick_up_tip()
        s_pipette.transfer(
            dil_vol,
            dilution_plate.wells()[dil_well],
            target_plate.wells_by_name()[one_pos]),
            blow_out=False
            )
        s_pipette.mix(
            mix_times, 
            dil_vol, 
            target_plate.wells_by_name()[one_pos]),
        s_pipette.drop_tip()        

        # increment next_dil_well
        next_dil_well +=1    


    ############################
    # PROTOCOL STARTS HERE
    ############################

    # set/reset pipettes speeds
    set_speeds(pipette20s, pspeed)
    set_speeds(pipette300s, pspeed)

    # initialize variables
    
    # csv as list of dictionaries
    tfers = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    # create a separate list of each column
    # Position,Volume,Dilution
    pos_list = [tfer['Position'] for tfer in tfers if tfer['Position']]
    vol_list = [round(float(tfer['Volume']),2) for tfer in tfers if tfer['Volume']]
    dil_list = [round(float(tfer['Dilution']),2) for tfer in tfers if tfer['Dilution']]
    
    # check if all sample volumes are in accepted range [min_vol:max_vol]
    if min(vol_list) < float(min_vol) or max(vol_list) > float(max_vol):
        usrmsg = (
            'some sample volume(s) in the csv are not in range of ' +
            str(min_vol) + ' - ' + str(max_vol)
            )
        raise Exception(usrmsg)

    # calculate real buffer needs for direct dilution
    direct_buffer_vol = round(sum[(a*b)-a for a,b in zip(vol_list, dil_list) if (dil_list>1 and dil_list<10)], 2)
    
    # calculate real buffer needs for 2-step dilution
    first_buffer_vol = round(sum[(a*b/10)-a for a,b in zip(vol_list, dil_list) if (dil_list>=10)], 2)
    second_buffer_vol = round(sum(dil_list/10*4.0) if (dil_list>=10)], 2)
    
    # estimate total buffer volume (mL) based on sum of all imported volumes
    buffer_needed = direct_buffer_vol + first_buffer_vol + second_buffer_vol

    # how many buffer slots are needed?
    bufferslots = math.ceil(float(buffer_needed)*1000/float(res_vol))

    # inform about the volume of buffer needed
    ctx.comment("## the run will use " + str(buffer_needed) + "mL dilution buffer")

    ctx.pause("## Insert '" + str(bufferslots) + "' 1.5ml tubes with " + str(float(res_vol)*1.2) + 
        "ml buffer in the tube rack (" + str(buffer_wells[0:bufferslots]) + ")")
    
    # loop in the CSV data and process 
    for tfer in tfers:
        one_pos, one_vol, one_dil = tfer[0:3]

        # pick the right routine depending on dilution
        if one_dil==1:
            direct_transfer_no_dilution(one_pos, one_vol, one_dil)
        elif one_dil > max_dil:
            step_transfer_two_dilutions(one_pos, one_vol, one_dil, max_dil, min_fin)
        else:
            direct_transfer_one_dilution(one_pos, one_vol, one_dil)

    # eject tips where present
    for pipette in [pipette20s, pipette300s]:
        if pipette.has_tip:
            pipette.drop_tip()  

    ctx.comment(
      "\n    #############################################" +
      "\n    ## All done!" +
      "\n    #############################################")
