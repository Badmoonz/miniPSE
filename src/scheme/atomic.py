#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from blockbase import BlockBase
from utils import split_by_comma
import connection
import fa


class Atomic(BlockBase):
  _block_type = "atomic"

  def load(self, path):
    self._load_fa(path)
    self._set_data_from_graphs()
    self._load_connection_graph(path)

  def _load_fa(self, path):
    self._fa_graph = fa.FA(path)

  def _load_connection_graph(self, path):
    self._connection_graph = connection.TrivialConnectionGraph(self.inputs, self.outputs)

  def _set_data_from_graphs(self):
    self._name = self.fa_graph.name
    self._inputs = self.fa_graph.inputs
    self._outputs = self.fa_graph.outputs
    if "block_groups" in self._fa_graph.properties:
      self._block_groups = set(split_by_comma(self._fa_graph.properties["block_groups"]))
    else:
      self._block_groups = set()

  def __repr__(self):
    return "[%s]" % self.name
