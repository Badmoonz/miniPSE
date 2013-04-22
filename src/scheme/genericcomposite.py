#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from composite import Composite
from connection import ConnectionGraph
from workflow import Workflow

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
      self._connection_graph.graph["name"] = self.name
      self._block_group = group if group else GenericComposite.GENERIC

  def load(self, path):
    raise NotImplementedError, "This method does not impliment yet!"

  def __repr__(self):
    return "<%s>" % self.name

  def _calc_fa(self):
    w = Workflow(self)
    G = self.fa_graph.G
    states_queue = set(G.nodes())
    while states_queue:
      state = states_queue.pop()
      for n in range(len(self.inputs)):
        for inputs in combinations(self.inputs, n + 1):
          variants = []
          try:
            variants = w.work(state, set(inputs))
            print variants
          except SurplusWave:
            print "SurplusWave detected! Skip this inputs!"
            continue
          finally:
            for v in variants:
              new_state = pure_block_states(v.state)
              if not new_state in G.node:
                states_queue.add(new_state)
              G.add_edge(state, new_state, inputs=v.inputs, outputs=v.outputs)