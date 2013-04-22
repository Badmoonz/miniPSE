#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from ..scheme import Composite
from implicitconnection import ImplicitConnection



class Pattern(Composite):
  PATTERN = 'pattern'
  _block_type = Pattern.PATTERN
  _is_composite = False
  _block_group = Pattern.PATTERN

  def _load_connection_graph(self, path):
    self._connection_graph = ImplicitConnection(path)
    self._name = self._connection_graph.name
    self._inputs = self._connection_graph.inputs
    self._outputs = self._connection_graph.outputs
    if "block_groups" in self._connection_graph.properties:
      self._block_groups = set(split_by_comma(self._connection_graph.properties["block_groups"]))

  def _load_fa(self, path):
    pass

  def work(self, state, inputs):
    pass
