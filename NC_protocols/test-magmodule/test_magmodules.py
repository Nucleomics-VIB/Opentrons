from opentrons.types import Point
from opentrons import protocol_api

metadata = {
    'protocolName': 'test-magmodules',
    'author': 'Stephane Plaisance <stephane.plaisance@vib.be>',
    'description': 'endurance test for two magmodules on OT-2_Post_1',
    'source': 'maintenance',
    'apiLevel': '2.10'
    }

# script version 1.0; 2022_03_01 (SP)


def get_values(*names):
    import json
    _all_values = json.loads(
        """
        {
        "magmodule1_pos":4,
        "magmodule2_pos":1,
        "magnet_height":18,
        "magnet_height_mid":9,
        "hold_time_sec":5,
        "repeat_num":10
        }
        """
    )
    return [_all_values[n] for n in names]


def run(ctx):

    [magmodule1_pos,
        magmodule2_pos,
        magnet_height,
        magnet_height_mid,
        hold_time_sec,
        repeat_num] = get_values(  # noqa: F821
          "magmodule1_pos",
          "magmodule2_pos",
          "magnet_height",
          "magnet_height_mid",
          "hold_time_sec",
          "repeat_num")
          
    # load labware
    mag_module1 = ctx.load_module('magnetic module gen2', int(magmodule1_pos))
    mag_module2 = ctx.load_module('magnetic module gen2', int(magmodule2_pos))

    # turn lights ON (comment out to turn OFF)
    ctx.set_rail_lights(True)

    ctx.comment(
        '#'*3 +
        ' repeat disengage and engage at different heights for both magmodules' +
        ' (endurance test)' +
        '#'*3)

    # disengage both
    mag_module1.disengage()
    mag_module2.disengage()

    for repeat in range(repeat_num):

        ctx.comment("## iteration: {}".format(repeat+1))
        
        # engage on top
        ctx.comment('## engaging on top')
        mag_module1.engage(height=magnet_height)
        mag_module2.engage(height=magnet_height)
        # hold
        ctx.delay(seconds=hold_time_sec)
        # disengage
        mag_module1.disengage()            
        mag_module2.disengage()            

        # engage at half height
        ctx.comment('## engaging on half-height')
        mag_module1.engage(height=magnet_height_mid)
        mag_module2.engage(height=magnet_height_mid)
        # hold
        ctx.delay(seconds=hold_time_sec)
        # disengage
        mag_module1.disengage()
        mag_module2.disengage()
        
        ctx.comment('\n')

    ctx.comment(
        '\n All done'
        )
