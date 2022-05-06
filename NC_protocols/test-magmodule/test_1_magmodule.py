from opentrons.types import Point
from opentrons import protocol_api

metadata = {
    'protocolName': 'test-magmodules',
    'author': 'Stephane Plaisance <stephane.plaisance@vib.be>',
    'description': 'endurance test for a single magmodules on OT-2_Post_1',
    'source': 'maintenance',
    'apiLevel': '2.10'
    }

# script version 1.0; 2022_03_01 (SP)


def get_values(*names):
    import json
    _all_values = json.loads(
        """
        {
        "magmodule_pos":4,
        "magnet_height":18,
        "magnet_height_mid":9,
        "hold_time_sec":1,
        "repeat_num":10
        }
        """
    )
    return [_all_values[n] for n in names]


def run(ctx):

    [magmodule_pos,
        magnet_height,
        magnet_height_mid,
        hold_time_sec,
        repeat_num] = get_values(  # noqa: F821
          "magmodule_pos",
          "magnet_height",
          "magnet_height_mid",
          "hold_time_sec",
          "repeat_num")
          
    # load labware
    mag_module = ctx.load_module('magnetic module gen2', int(magmodule_pos))

    # turn lights ON (comment out to turn OFF)
    ctx.set_rail_lights(True)

    ctx.comment(
        '#'*3 +
        ' repeat disengage and engage at different heights for 1 magmodule' +
        ' (endurance test)' +
        '#'*3)

    # disengage both
    mag_module.disengage()

    for repeat in range(repeat_num):

        ctx.comment("## iteration: {}".format(repeat+1))
        
        # engage on top
        ctx.comment('## engaging on top')
        mag_module.engage(height=magnet_height)
        # hold
        ctx.delay(seconds=hold_time_sec)
        # disengage
        mag_module.disengage()            

        # engage at half height
        ctx.comment('## engaging on half-height')
        mag_module.engage(height=magnet_height_mid)
        # hold
        ctx.delay(seconds=hold_time_sec)
        # disengage
        mag_module.disengage()
        
        ctx.comment('\n')

    ctx.comment(
        '\n All done'
        )
