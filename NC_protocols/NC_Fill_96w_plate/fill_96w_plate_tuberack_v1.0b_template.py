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
        "plate_type":"<plate_type>",
        "tube_rack":"<tube_rack>",
        "res_vol":"<res_vol>",
        "min_vol":"<min_vol>",
        "max_vol":"<max_vol>",
        "pspeed":"<pspeed>",
        "uploaded_csv":"<uploaded_csv>"        
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
                
            # increase clearance to avoid touching the tube/plate bottom
            s_pipette.well_bottom_clearance.aspirate = 3
            s_pipette.well_bottom_clearance.dispense = 1

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
    if len(vol_list) > 96:
        usrmsg = (
            'this protocol can handle only up to 96 wells and you gave in ' + str(len(vol_list)) + ' data rows'
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
