#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from blockbase import BlockBase
import connection
import fa

import networkx as nx
import os
from tempfile import NamedTemporaryFile

class Atomic(BlockBase):
  _block_type = "atomic"

  def _load_fa(self, path):
    self._fa_graph = fa.FA(path)
    self._name = self._fa_graph.name
    self._inputs = self._fa_graph.inputs
    self._outputs = self._fa_graph.outputs

  def _load_connection_graph(self, path):
    self._connection_graph = connection.TrivialConnectionGraph(self.inputs, self.outputs)

  def work(self, state, inputs):
    return self._fa_graph.variants(state, inputs)
  
  def __repr__(self):
    return "[%s]" % self.name