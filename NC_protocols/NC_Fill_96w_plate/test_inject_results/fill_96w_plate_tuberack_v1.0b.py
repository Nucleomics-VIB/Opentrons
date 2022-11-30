from opentrons import protocol_api
import math
import csv

metadata = {
        'protocolName': 'NC_fill_96w_plate',
        'author': 'nucleomics@vib.be',
        'description': 'fill each well of an empty 96w plate with custom volume buffer from imported CSV',
        'source': 'VIB Nucleomics',
        'apiLevel': '2.10'
        }

# version 1.0b; 2022_11_24 (SP)
# edit date ....

### example config.yaml ###

## params:
##  plate_type: "biorad_96_wellplate_200ul_pcr"
##  tube_rack: "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap"
##  res_vol: 1000.0
##  min_vol: 2.0
##  max_vol: 100.0
##  pspeed: 7.56
##csv:
##  uploaded_csv: "data.csv"

# imported csv is made of up to 96 rows of 2 columns (Position,Value)

def get_values(*names):
    import json
    _all_values = json.loads("""{
        "plate_type":"biorad_96_wellplate_200ul_pcr",
        "tube_rack":"opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap",
        "res_vol":"1000.0",
        "min_vol":"2.0",
        "max_vol":"100.0",
        "pspeed":"7.56",
        "uploaded_csv":"Position,Value\\nA1,15.7\\nA2,2.5\\nA3,13.5\\nA4,7.1\\nA5,8.0\\nA6,13.4\\nA7,5.6\\nA8,2.8\\nA9,2.7\\nA10,17.7\\nA11,15.1\\nA12,8.2\\nB1,18.1\\nB2,9.4\\nB3,5.5\\nB4,13.8\\nB5,7.2\\nB6,10.0\\nB7,14.8\\nB8,7.3\\nB9,10.3\\nB10,2.4\\nB11,3.3\\nB12,13.8\\nC1,14.0\\nC2,6.5\\nC3,4.4\\nC4,3.2\\nC5,8.1\\nC6,6.7\\nC7,15.6\\nC8,15.5\\nC9,6.7\\nC10,7.6\\nC11,2.1\\nC12,11.7\\nD1,3.4\\nD2,50.0\\nD3,17.5\\nD4,10.5\\nD5,11.6\\nD6,80.0\\nD7,17.5\\nD8,3.5\\nD9,2.9\\nD10,99.0\\nD11,18.9\\nD12,9.1\\nE1,19.5\\nE2,7.8\\nE3,11.2\\nE4,17.3\\nE5,18.3\\nE6,7.9\\nE7,9.9\\nE8,15.3\\nE9,8.2\\nE10,12.2\\nE11,6.6\\nE12,5.6\\nF1,13.8\\nF2,2.9\\nF3,11.7\\nF4,70.0\\nF5,10.1\\nF6,9.7\\nF7,19.2\\nF8,90.0\\nF9,10.8\\nF10,16.9\\nF11,5.5\\nF12,13.1\\nG1,19.6\\nG2,14.9\\nG3,11.1\\nG4,14.6\\nG5,12.8\\nG6,6.9\\nG7,17.5\\nG8,3.7\\nG9,3.0\\nG10,8.0\\nG11,6.3\\nG12,7.1\\nH1,2.9\\nH2,16.1\\nH3,4.0\\nH4,17.6\\nH5,9.3\\nH6,16.2\\nH7,6.6\\nH8,17.5\\nH9,9.7\\nH10,20.0\\nH11,11.2\\nH12,3.5"        
        }""")
    return [_all_values[n] for n in names]

def run(ctx: protocol_api.ProtocolContext):

    # load variables via get_values
    [plate_type, tube_rack, res_vol, min_vol, max_vol, pspeed, uploaded_csv] = get_values(  # noqa: F821
            "plate_type", "tube_rack", "res_vol", "min_vol", "max_vol", "pspeed", "uploaded_csv")

    # light be
    ctx.set_rail_lights(True)
    # ctx.delay(seconds=10)

    # empty 96w plate on pos 1
    dilution_plate = ctx.load_labware(
        plate_type,
        '1',
        'destination_plate')

    # tube rack on pos 4 with buffer slots [A1:A4] and waste in last (A6)
    tuberack = ctx.load_labware(tube_rack, '4')
    
    # current buffer slots position 4 tubes on the top [A1 A2 A3 A4]
    buffer_wells = ['A1', 'A2', 'A3', 'A4']
    bufferidx = 1
    buffer = tuberack.wells_by_name()[buffer_wells[bufferidx-1]]

    # volume of used buffer
    buffer_counter = float(0.0)

    # number of buffer slots required for this experiment
    bufferslots = 1
    
    # provision enough tips for 2 plates
    slots = ['7']
    tips20 = [ctx.load_labware(
        'opentrons_96_filtertiprack_20ul',
        slot,
        label='tip_20')
            for slot in slots]

    # provision enough tips for 2 plates
    slots = ['8']
    tips300 = [ctx.load_labware(
        'opentrons_96_filtertiprack_200ul',
        slot,
        label='tip_300')
            for slot in slots]

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

    def set_speeds(pip, aspeed, dspeed=None, bspeed=None):
        pip.flow_rate.aspirate = aspeed
        pip.flow_rate.dispense = dspeed if dspeed is not None else aspeed
        pip.flow_rate.blow_out = bspeed if bspeed is not None else aspeed

    def reset_speeds(pip):
        pip.flow_rate.set_defaults(ctx.api_version)

    # do the pipetting
    def process_data(tfers, buffer, buffer_counter, bufferidx):

        # process well by well from uploaded_csv
        for line in tfers:
            s_well = line['Position']
            s_vol = line['Value']
            # change types
            s_well = str(s_well)
            s_vol = float(s_vol)
            
            # choose right pipet
            if s_vol <= 20.0:
                usedpip = "p20"
                s_pipette = pipette20s
            else:
                usedpip = "p300"
                s_pipette = pipette300s

            buffer_counter += s_vol
            if float(buffer_counter) > float(res_vol):

                bufferidx += 1
                buffer_counter = float(s_vol)
                buffer = tuberack.wells_by_name()[buffer_wells[bufferidx-1]]

            # is tip present?
            if not s_pipette.has_tip:
                s_pipette.pick_up_tip()

            # transfer
            s_pipette.transfer(
                s_vol,
                buffer,
                dilution_plate.wells_by_name()[s_well],
                blow_out=False,
                new_tip='never'
                )
    
    ############################
    # PROTOCOL STARTS HERE
    ############################

    # set/reset pipettes speeds
    set_speeds(pipette20s, pspeed)
    set_speeds(pipette300s, pspeed)

    # initialize variables
    
    # csv as list of dictionaries
    tfers = [line for line in csv.DictReader(uploaded_csv.splitlines())]

    # create list of all volumes
    pos_list = [tfer['Position'] for tfer in tfers if tfer['Position']]
    vol_list = [round(float(tfer['Value']),2) for tfer in tfers if tfer['Value']]

    # fail if tfers is longer than max 96 wells
    if len(vol_list) > 96
        usrmsg = (
            'this protocol can handle onlyuyp to '96' wells and you gave in ' +
            str(len(vol_list)) + ' data rows'
            )
        raise Exception(usrmsg)

    # fail if some requested volumes are outside of accepted range [min_vol:max_vol]
    if min(vol_list) < float(min_vol) or max(vol_list) > float(max_vol):
        usrmsg = (
            'some buffer volume(s) in csv are not in range of ' +
            str(min_vol) + ' - ' + str(max_vol)
            )
        raise Exception(usrmsg)

    # estimate total buffer volume (mL) based on sum of all imported volumes
    buffer_needed = round(sum([float(tfer['Value']) for tfer in tfers if tfer['Value']])/1000.0,2)

    # how many buffer slots are needed?
    bufferslots = math.ceil(float(buffer_needed)*1000/float(res_vol))

    # inform about the volume of buffer needed
    ctx.comment("## the run will use " + str(buffer_needed) + "mL dilution buffer")

    ctx.pause("## Insert '" + str(bufferslots) + "' 1.5ml tubes with " + 
        str(float(res_vol)*1.2) + "ml buffer in the tube rack (" + str(buffer_wells[0:bufferslots]) + ")")
        
    ctx.pause(
        '\n\n' + '#'*75 +
        '\nInsert an empty 96w plate in deck positions : 1' +
        '\nThen select "Resume" in the Opentrons App\n' +
        '#'*75
        )

    process_data(tfers, buffer, buffer_counter, bufferidx)

    # eject tips where present
    for pipette in [pipette20s, pipette300s]:
        if pipette.has_tip:
            pipette.drop_tip()  

    ctx.comment(
      "\n    #############################################" +
      "\n    ## All done!" +
      "\n    #############################################")
