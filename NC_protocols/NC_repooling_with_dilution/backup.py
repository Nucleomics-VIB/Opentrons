def get_values(*names):
    import json
    _all_values = json.loads("""{
      "uploaded_csv":"source_plate,source_well,source_volume,dil_factor\\n1,A1,2.5,1\\n1,A8,5,1\\n1,B4,2.5,10\\n1,F6,2.5,90",
      "min_vol":"2.5",
      "sp_type":"biorad_96_wellplate_200ul_pcr",
      "sp_number":"1",
      "dp_type":"biorad_96_wellplate_200ul_pcr"
    }""")
    return [_all_values[n] for n in names]

metadata = {
    'protocolName': 'NC_repooling_with_dilution',
    'author': 'nucleomics@vib.be',
    'description': 'Cherrypicking from 1..4 plates and CSV (+ intermediate dilution for concentrated samples)',
    'source': 'VIB Nucleomics',
    'apiLevel': '2.10'
    }

# script version 1.0; 2021_08_30 (SP)

def run(ctx):
  [uploaded_csv,
  min_vol,
  sp_type,
  sp_number,
  dp_type] = get_values(  # noqa: F821
    'uploaded_csv',
    'min_vol', 
    'sp_type', 
    'sp_number',
    'dp_type')

  # define tip racks and pipette 
  tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', 
    slot, 
    label='tip_20')
      for slot in range(7,9)]

  pipette = ctx.load_instrument(
    'p20_single_gen2', 
    'left', 
    tip_racks=tips)

  tube_rack = ctx.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', '1')

  # water in first rack tubes (1ml per tube)
  water_tube = tube_rack.wells_by_name()["A1"]

  # pool in last rack tube
  pool_tube = tube_rack.wells_by_name()["D6"]

  max_dil_fact = 80.0   # since 2.5x80=200uL

  dilution_plate = ctx.load_labware(dp_type, '4', 'Dilution plate')
  # define *global value for next dilution well
  next_dil_well = 0

  # up top 4 customer plates to pick CSV-selected samples from
  #sp_number = int(sp_number)
  #source_positions = ['5', '6', '2', '3']
  source_plate = ctx.load_labware(sp_type, '5', 'Source plates')
  #  for plt in source_positions[0:sp_number] 
  # dilution plate for samples with high concentration (from CSV)
  
  ###########
  # routines
  ###########

  def dilute_and_pool(s_pl, s_well, s_vol, d_fact, dil_well):

    # pipet s_vol from dilution plate next_dil_well to pool
    ctx.comment('\n' + '#'*3 + ' diluting ' + str(s_vol) + 'ul from plate' + str(s_pl) + " " + s_well + " " + str(d_fact) + ' times, and adding ' + str(s_vol) + 'ul to the pool')

    pipette.pick_up_tip()

    # add water to dil_fact to dilution plate in well next_dil_well
    water_vol =  (d_fact-1) * s_vol
    pipette.transfer(water_vol, 
      water_tube, 
      dilution_plate.wells()[dil_well],
      new_tip='never'
      )

    # pipet s_vol to dilution plate next_dil_well and mix
    mix_vol = min(20, 0.8 * water_vol)
    pipette.transfer(s_vol, 
      source_plate.wells_by_name()[s_well], 
      dilution_plate.wells()[dil_well],
      mix_after=(10, mix_vol),
      new_tip='never'
      )

    # transfer s_vol (diluted) to pool
    pipette.transfer(s_vol, 
      dilution_plate.wells()[dil_well],
      pool_tube,
      blow_out=True,
      blowout_location='destination well',
      new_tip='never'
      )

    pipette.drop_tip()
    
  def add_to_pool(s_pl, s_well, s_vol, d_fact):
 
    # pipet s_vol to pool
    ctx.comment('\n' + '#'*3 + ' adding ' + str(s_vol) + 'ul from plate' + str(s_pl) + " " + s_well + ' to the pool')
    
    pipette.pick_up_tip()

    # transfer s_vol (undiluted) to pool
    pipette.transfer(s_vol, 
      source_plate.wells_by_name()[s_well],
      pool_tube,
      blow_out=True,
      blowout_location='destination well',
      new_tip='never'
      )

    pipette.drop_tip()

  #########
  # method
  #########

  # parse data and act
  data = [[val.strip() for val in line.split(',')]
    for line in uploaded_csv.splitlines()
      if line.split(',')[0].strip()][1:]

  # warn if too many samples in csv
  if len(data) > 96:
    usrmsg = 'max 96 samples can be repooled! (csv has ' + str(len(data)) + ')'
    raise Exception(usrmsg)

  # process csv data
  for line in data:
    s_pl, s_well, s_vol, d_fact = line[0:4]
    
    # change types
    s_pl = int(s_pl)
    s_well = str(s_well)
    s_vol = float(s_vol)
    d_fact = float(d_fact)

    # debug
    #print(line," - ", s_well)

    # choose action based on need for dilution
    if d_fact > 1:
      # max dilution is 40x due to well size
      if d_fact > max_dil_fact:
          d_fact = max_dil_fact
      dilute_and_pool(s_pl, s_well, s_vol, d_fact, int(next_dil_well))  
      # increment for next dilution
      next_dil_well = next_dil_well+1
    else:
      add_to_pool(s_pl, s_well, s_vol, d_fact)
