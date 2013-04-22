#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from composite import Composite
from connection import ConnectionGraph, TrivialConnectionGraph
from workflow import Workflow
from utils import pure_block_states
from utils import SurplusWave

from itertools import combinations

GENERIC = "generic"

class GComposite(Composite):
  _index = 0

  def _get_new_id(self):
    self._index += 1
    return self._index

  _block_type = GENERIC
  _block_group = GENERIC

  def __init__(self, path=None, name=None):
      super(GComposite, self).load(path)
      self._name = name or "%s_%s"%(GENERIC, self._get_new_id())

  def __repr__(self):
    return "<%s>" % self.name


  def _calc_fa(self):
    w = Workflow(self)
    G = self.fa_graph.G
    states_queue = set(G.nodes())
    while(states_queue):
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

