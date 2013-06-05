import snakes.plugins
nets = snakes.plugins.load(['gv', 'ops', 'synchro'], 'snakes.nets', 'nets')
from nets import *

pn = PetriNet("mynet")
pn.add_transition(Transition('t1'))
pn.add_place(Place('i'), status = entry)
pn.add_place(Place('o'), status = exit)
pn.add_input('i', 't1', Value('x'))
pn.add_output('o', 't1', Value('x'))



