
import opentrons
import types

print([getattr(opentrons, a) for a in dir(opentrons)
  if isinstance(getattr(opentrons, a), types.FunctionType)])


#numcol=6
#for i in range(numcol):
#    print(i)
