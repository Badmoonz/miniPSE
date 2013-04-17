#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from composite import Composite
# from connection import ConnectionGraph
from workflow import Workflow
import keys
from utils import composite_state
from utils import SurplusWave


from itertools import combinations
# Dirty hack
__name_index = 0
def _get_name_index():
  global __name_index
  __name_index += 1
  return __name_index

class GenericComposite(Composite):
  GENERIC = "generic"
  _block_type = GENERIC
  _block_group = GENERIC

  def __init__(self, path=None, connection_graph=None, name=None, group=None):
    if path:
      self.load(path)
    else:
      self._connection_graph = ConnectionGraph()
      self._name = name if name else ("generic" + str(_get_name_index()))
      self._block_group = group if group else GenericComposite.GENERIC


       
  def load(self, path):
    raise NotImplementedError, "This method does not impliment yet!"

  def __repr__(self):
    return "<%s>" % self.name


class GComposite(Composite):
  def _full_calc_fa(self):
    w = Workflow(self)
    G = self._fa_graph.G
    G.add_node(composite_state(self.initial_state))
    states_queue = set(G.nodes())
    try: 
      while(states_queue):
        state = states_queue.pop()
        for n in range(len(self.inputs)):
          for inputs in combinations(self.inputs, n + 1):
            variants = []
            try:
              variants = w.work(state, set(inputs))
              print variants
            except SurplusWave, e:
              print "SurplusWave detected! Skip this inputs!"
              continue
            finally:
              for v in variants:
                if not v.state in G.node:
                  states_queue.add(v.state)
                G.add_edge(state, v.state, inputs = v.inputs, outputs = v.outputs)
    except RaceCondition, e:
      raise e