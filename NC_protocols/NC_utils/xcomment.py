from opentrons import protocol_api

metadata = {'apiLevel': '2.10'}

# define and test xcomment and xpause
# to display multiline output in the App log screen
# SP 2021-09-29, v1.0


def run(ctx: protocol_api.ProtocolContext):
    # Labware defining tip racks
    tr1 = ctx.load_labware(
        'opentrons_96_tiprack_20ul',
        '10')

    # Defining Pipette
    p20_single = ctx.load_instrument(
        'p20_single_gen2',
        'left',
        tip_racks=[tr1])

    # Block Command picking up tip
    p20_single.pick_up_tip()

    def xcomment(text, funcprot=ctx):
        import io
        width = len(max(io.StringIO(text), key=len).rstrip())+6
        funcprot.comment('\n' + '#'*width)
        for line in io.StringIO(text):
            if not line.isspace():  # omit empty lines
                # remove trailing spaces and line feeds
                funcprot.comment('#'*2 + line.rstrip())
        # leave one empty line below
        funcprot.comment('#'*width + '\n')

    def xpause(text, funcprot=ctx):
        xcomment(text)
        funcprot.pause("==> press continue when ready!")

    my_text = '''
    this is line number 1
    * line 2 is here
    * and this is line 3
      - with some more indent
      1) or some numbered list
    '''

    ctx.comment('\n## comment\n')

    ctx.comment(my_text)

    ctx.comment('## xcomment\n')

    xcomment(my_text)

    ctx.comment('## pause\n')

    ctx.pause(my_text)

    ctx.comment('## xpause\n')

    xpause(my_text)
