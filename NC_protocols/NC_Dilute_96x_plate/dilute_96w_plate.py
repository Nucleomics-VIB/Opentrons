from opentrons import protocol_api
import math
import csv

metadata = {
        'protocolName': 'dilute_96w_plate',
        'author': 'nucleomics@vib.be',
        'description': 'dilute wells from 96w_plate to new plate from CSV \
            (+ intermediate dilution for > 20x concentrated samples)',
        'source': 'VIB Nucleomics',
        'apiLevel': '2.10'
        }

# template version 1.0b; 2022_12_02 (SP)
# edit date 

def get_values(*names):
    import json
    _all_values = json.loads("""{
        "sp_type":"biorad_96_wellplate_200ul_pcr",
        "tp_type":"biorad_96_wellplate_200ul_pcr",
        "dp_type":"biorad_96_wellplate_200ul_pcr",
        "tube_rack":"opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap",
        "buf_vol":"1000.0",
        "min_vol":"2.5",
        "max_dil":"20.0",
        "min_fin":"20.0",
        "pspeed":"24.0",
        "mix_times":"4",
        "uploaded_csv":"Position,Dilution\\nA1,1.0\\nB1,5.0\\nC1,25.0\\nD1,80.0\\nE1,15.0\\nF1,10.0\\nG1,200.0"
        }""")
    return [_all_values[n] for n in names]

def run(ctx: protocol_api.ProtocolContext):
    [sp_type,
        tp_type,
        dp_type,
        tube_rack,
        buf_vol,
        min_vol,
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
        'max_dil',
        'min_fin',
        'pspeed',
        'mix_times',
        'uploaded_csv')

    # set variable types
    buf_vol = float(buf_vol)         # max usable per eppendorf tube
    min_vol = float(min_vol)         # min pipettable volume
    max_dil = float(max_dil)         # max direct dilution (one step)
    min_fin = float(min_fin)         # min volume in dest well
    pspeed = float(pspeed)           # pipette speed (standard 7.56)
    mix_times = int(mix_times)       # mix sample and buffer after dispensing

    ###########
    # OT-2 deck
    ###########

    # light be
    ctx.set_rail_lights(True)
    # ctx.delay(seconds=10)

    # source 96w plate on pos #1
    source_plate = ctx.load_labware(
        sp_type,
        '1',
        'source_plate')

    # empty dilution 96w plate on pos #2
    dilution_plate = ctx.load_labware(
        dp_type,
        '2',
        'dilution_plate')

    # empty 96w plate on pos #3
    target_plate = ctx.load_labware(
        tp_type,
        '3',
        'target_plate')

    # tube rack on pos #4
    tuberack = ctx.load_labware(tube_rack, '4')

    # buffer tubes on top row [A1 A2 A3 A4 A5 A6]
    buffer_wells = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6']
    bufferidx = 1
    buffer = tuberack.wells_by_name()[buffer_wells[bufferidx-1]]

    # provision enough p20 tips for 2 plates
    slots20 = ['7', '8']
    tips20 = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in slots20]

    # provision enough p200 tips for 2 plates
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

    ###########
    # routines
    ###########

    # dilution occurs in the same dilution plate well address as the sample came from
    # this allows keeping the dilution plate in case more is needed for redo

    # volume of used buffer
    buffer_counter = float(0.0)

    def set_speeds(pip, aspeed, dspeed=None, bspeed=None):
        pip.flow_rate.aspirate = aspeed
        pip.flow_rate.dispense = dspeed if dspeed is not None else aspeed
        pip.flow_rate.blow_out = bspeed if bspeed is not None else aspeed

    def set_clearance(pip, asp_clr, dis_clr):
        # increase clearance to avoid touching the tube/plate bottom
        pip.well_bottom_clearance.aspirate = asp_clr
        pip.well_bottom_clearance.dispense = dis_clr

    def reset_speeds(pip):
        pip.flow_rate.set_defaults(ctx.api_version)

    ##################################
    # get min two_vol volume to dilute
    # and get at least min_fin uL final
    ###################################
    # max(min_vol, x)
    def get_two_vol(min_vol, x):
        if x >= min_vol:
            return x
        else:
            return get_two_vol(x+0.1)

    #########################################################################
    #  a min_fin volume of sample is directly transferred to the target plate
    #########################################################################
    def direct_transfer_no_dilution(one_pos, one_vol):

        # debug
        # print("undiluted", one_pos, "vol:", str(one_vol), "dil:", "undiluted", "buffer:", "none")

        # choose pipet
        if min_fin <= 20.0:
            usedpip = "p20"
            s_pipette = pipette20s
        else:
            usedpip = "p300"
            s_pipette = pipette300s

        # is tip present?
        if not s_pipette.has_tip:
            s_pipette.pick_up_tip()

        s_pipette.transfer(
            volume=one_vol,
            source=source_plate.wells_by_name()[one_pos],
            dest=target_plate.wells_by_name()[one_pos],
            new_tip='never'
            )

        # the tip has seen sample
        s_pipette.drop_tip()

    ######################################################################
    # enough sample is diluted in-place in the target plate to get min_fin
    ######################################################################
    def direct_transfer_one_dilution(one_pos, one_dil, min_vol, min_fin, mix_times):

        nonlocal buffer_counter
        nonlocal buffer
        nonlocal bufferidx

        # calculate sample volume needed to get >= min_fin AND be more than min_vol
        req_vol = round(max(min_vol, min_fin / one_dil), 1)

        # calculate buffer volume needed
        buffer_vol = round((one_dil - 1) * req_vol, 1)

        # debug
        # print("one-step-dil", one_pos, "vol:", str(req_vol), "dil:", str(one_dil), "buffer:", str(buffer_vol))

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

        # is tip present?
        if not s_pipette.has_tip:
            s_pipette.pick_up_tip()

        s_pipette.transfer(
            volume=buffer_vol,
            source=buffer,
            dest=target_plate.wells_by_name()[one_pos],
            new_tip='never'
            )

        # transfer sample to same well and mix_after
        # choose pipet
        if float(req_vol) <= 20.0:
            usedpip = "p20"
            s_pipette = pipette20s
        else:
            usedpip = "p300"
            s_pipette = pipette300s

        # is tip present?
        if not s_pipette.has_tip:
            s_pipette.pick_up_tip()

        # transfer sample in buffer and mix using the same tip
        # mix with the smallest of [20, buffer_vol+one_vol] -2 for safety
        mix_vol = round(min(20.0, buffer_vol + req_vol) - 2.0, 1)

        s_pipette.transfer(
            volume=req_vol,
            source=source_plate.wells_by_name()[one_pos],
            dest=target_plate.wells_by_name()[one_pos],
            mix_after=(mix_times,mix_vol),
            new_tip='never'
            )

        # the tip has seen sample
        s_pipette.drop_tip()

    #######################################################
    # for larger than 20x dilutions
    # dilute a volume of sample sqrt(one_dil) times
    #   at same plate location in the dilution plate
    # then dilute the dilution sqrt(one_dil) times 
    #   at same location in the target plate to get min_fin
    #######################################################
    def step_transfer_two_dilutions(one_pos, one_dil, min_vol, max_dil, min_fin, mix_times):

        nonlocal buffer_counter
        nonlocal buffer
        nonlocal bufferidx

        # pre-dilute math.sqrt(one_dil) times (20x -> 4.47x)
        #   will be repeated a second time to come to one_dil final dilution
        ser_dil = round(math.sqrt(one_dil), 1)
        one_vol = min_vol
        buffer_vol = round((ser_dil - 1) * one_vol, 1)

        # debug
        # print("two-step-dil.1", one_pos, "vol:", str(one_vol), "dil:", str(ser_dil), "buffer:", str(buffer_vol))

        # test if enough buffer in current tube_rack else take next tube
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

        # is tip present?
        if not s_pipette.has_tip:
            s_pipette.pick_up_tip()

        s_pipette.transfer(
            volume=buffer_vol,
            source=buffer,
            dest=dilution_plate.wells_by_name()[one_pos],
            new_tip='never'
            )

        # then add sample to it and mix
        # choose pipet
        if float(min_vol) <= 20.0:
            usedpip = "p20"
            s_pipette = pipette20s
        else:
            usedpip = "p300"
            s_pipette = pipette300s   

        # is tip present?
        if not s_pipette.has_tip:
            s_pipette.pick_up_tip()

        # transfer sample in buffer and mix using the same tip
        # mix with the smallest of [20, buffer_vol+one_vol] -2 for safety
        mix_vol = round(min(20, buffer_vol + min_vol) - 2, 1)

        s_pipette.transfer(
            volume=min_vol,
            source=source_plate.wells_by_name()[one_pos],
            dest=dilution_plate.wells_by_name()[one_pos],
            mix_after=(mix_times,mix_vol),
            new_tip='never'
            )

        # the tip has seen sample
        s_pipette.drop_tip()

        # then add buffer to target plate for a second time math.sqrt(one_dil)
        # with a minimal final volume of min_fin uL
        # and a minimal volume of min_vol
        two_vol = round(max(min_vol, min_fin / ser_dil), 1)
        
        # compute the required buffer volume to achieve this
        buffer_vol = round(two_vol * (ser_dil - 1), 1)

        # debug
        # print("two-step-dil.2", one_pos, "vol:", str(two_vol), "dil:", str(ser_dil), "buffer:", str(buffer_vol))

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

        # is tip present?
        if not s_pipette.has_tip:
            s_pipette.pick_up_tip()

        s_pipette.transfer(
            volume=buffer_vol,
            source=buffer,
            dest=target_plate.wells_by_name()[one_pos],
            new_tip='never'
            )

        # add two_vol of diluted sample to reach min_vol in the target well
        # mix with the smallest of [20, buffer_vol+one_vol] -2 for safety
        mix_vol = min(20, buffer_vol + two_vol) - 2
        s_pipette = pipette20s

        # is tip present?
        if not s_pipette.has_tip:
            s_pipette.pick_up_tip()

        s_pipette.transfer(
            volume=two_vol,
            source=dilution_plate.wells_by_name()[one_pos],
            dest=target_plate.wells_by_name()[one_pos],
            mix_after=(mix_times,mix_vol),
            new_tip='never'
            )

        s_pipette.drop_tip()

    ############################
    # PROTOCOL STARTS HERE
    ############################

    # set/reset pipettes speeds
    set_speeds(pipette20s, pspeed)
    set_speeds(pipette300s, pspeed)

    # set clearances to avoid touching bottom
    set_clearance(pipette20s, 3, 1)
    set_clearance(pipette300s, 3, 1)

    # csv as list of dictionaries
    tfers = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    # warn about the current expected volume taken from the sample plate
    ctx.comment("## make sure samples that will NOT be diluted have more than " + 
        str(min_fin) + 
        " microL in the sample plate or abort here and adapt 'min_fin' in the yaml config")

    pos_list = [tfer['Position'] for tfer in tfers if tfer['Position']]
    dil_list = [round(float(tfer['Dilution']),1) for tfer in tfers if tfer['Dilution']]

    # check if all dilution factors are in accepted range [1:400]
    if min(dil_list) < 1 or max(dil_list) > 400:
        usrmsg = (
            'some dilution factor(s) in the csv are not in range of 1.0 - 400.0'
            )
        raise Exception(usrmsg)

    # calculate buffer needs for direct dilution
    req_list = [max(min_vol, min_fin / b) for b in dil_list]
    direct_buffer_vol = round(sum([a*(b-1) for a,b in zip(req_list, dil_list) if (b > 1 and b < max_dil)]), 1)

    # debug
    # print("direct dilution volumes:", [a*(b-1) for a,b in zip(req_list, dil_list) if (b > 1 and b < max_dil)])
    
    # calculate buffer needs for 2-step dilution (same conditions in both steps)
    first_buffer_vol = round(sum([min_vol*(math.sqrt(b) - 1) for b in dil_list if (b >= max_dil)]), 1)
    second_dil_vol = [max(min_vol, min_fin / round(math.sqrt(b),1)) for b in dil_list if (b >= max_dil)]
    second_dil_list = [b for b in dil_list if (b >= max_dil)]
    second_buffer_vol = round(sum([a*(math.sqrt(b) - 1) for a,b in zip(second_dil_vol, second_dil_list)]), 1)

    # debug
    # print("first 2-dilution volumes:", [min_vol*(math.sqrt(b) - 1) for b in dil_list if (b >= max_dil)])
    # print("first 2-dilution sample volumes:", [max(min_vol, min_fin / round(math.sqrt(b),1)) for b in dil_list if (b >= max_dil)])
    # print("second 2-dilution volumes:", [a*(math.sqrt(b) - 1) for a,b in zip(second_dil_vol, second_dil_list)])

    # estimate total buffer volume (mL) based on sum of all imported volumes
    buffer_needed = direct_buffer_vol + first_buffer_vol + second_buffer_vol

    # how many buffer slots are needed?
    bufferslots = math.ceil(float(buffer_needed)/float(buf_vol))

    # inform about the volume of buffer needed
    ctx.comment("## the run will use " + str(round(buffer_needed/1000,3)) + "mL dilution buffer")

    ctx.pause("## Insert '" + str(bufferslots) + "' 1.5ml tubes with " + str(float(buf_vol)*1.2) + 
        "ml buffer in the tube rack (" + str(buffer_wells[0:bufferslots]) + ")")

    # loop in the CSV data and process 
    for tfer in tfers:
        one_pos, one_dil = tfer.values()

        # make one_dil float for good
        one_dil = float(one_dil)

        # pick the right routine depending on dilution
        if one_dil == 1.0:
            direct_transfer_no_dilution(one_pos, min_fin)
        elif one_dil > max_dil:
            # scale down input to min_vol
            step_transfer_two_dilutions(one_pos, one_dil, min_vol, max_dil, min_fin, mix_times)
        else:
            direct_transfer_one_dilution(one_pos, one_dil, min_vol, min_fin, mix_times)

    # eject tips where present
    for pipette in [pipette20s, pipette300s]:
        if pipette.has_tip:
            pipette.drop_tip()  

    ctx.comment(
      "\n    #############################################" +
      "\n    ## All done!" +
      "\n    #############################################")
