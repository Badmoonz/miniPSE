#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from blockbase import BlockBase
from blockbase import split_by_comma

import connection
from fa import FA
from fa import TrivialFA

from sets import ImmutableSet as iset
import networkx as nx
import os.path as osp

from utils import ports_set, edge_str

class Composite(BlockBase):
  _block_type = 'composite'
  _is_composite = True
  _nfa_graph = None

  def load(self, path):
    self._load_connection_graph(path)
    self._load_fa(path)

  def _load_connection_graph(self, path):
    self._connection_graph = connection.ConnectionGraph(path)
    self._name = self._connection_graph.name
    self._inputs = self._connection_graph.inputs
    self._outputs = self._connection_graph.outputs
    if "block_groups" in self._connection_graph.properties:
      self._block_groups = split_by_comma(self._connection_graph.properties["block_groups"])

  def _load_fa(self, path):
    path_fa = (path if path else self.file_path) + ".fa"
    path_nfa = (path if path else self.file_path) + ".nfa"
    if osp.isfile(path_fa) and osp.isfile(path_nfa):
      self._fa_graph = FA(path_fa)
      self._nfa_graph = FA(path_nfa)
    else:
      self._fa_graph = TrivialFA(self.inputs, self.outputs)
      self._nfa_graph = TrivialFA(self.inputs, self.outputs)

  def work(self, state, inputs):
    if not state in self._fa_graph.nodes:
      raise Exception, "Bad state %s for FA %s!" % (state, self.name)
    elif len(self._fa_graph.G.out_edges(state)):
      variants = set()
      for neig in self._fa_graph.G.neighbors(state):
        for v in self._fa_graph.edges[state][neig]:
          edge = self._fa_graph.edges[state][neig][v]
          if edge["inputs"].issubset(inputs):
            variants.add(edge["inputs"], edge["outputs"], neig)
    else:
      return self._calc_fa(state, inputs)

  def _calc_fa(self, state, inputs):
    return iset()

  def show(self):
    self.show_connection_graph()

  def __repr__(self):
    return "{%s}" % self.name

  @property
  def blocks(self):
    return self._connection_graph.node

  @property
  def connection_graph(self):
    return self._connection_graph

  def has_path(self, src_block, dst_block):
    return nx.has_path(self._connection_graph,  src_block, dst_block)

  def connected_ports(self, block):
    G = self._connection_graph
    result = []
    in_edges = G.in_edges(block, data = True)
    for e in in_edges:
      result.append(ports_set(e[2]))
    return iset(result)

  def edges_from_block(self, block):
    G = self._connection_graph
    result = []
    out_edges = G.out_edges(block, data = True)
    for e in out_edges:
      result.append((e[0], e[1], ports_set(e[2])))
    return result

  def edges_to_block(self, block):
    G = self._connection_graph
    result = []
    in_edges = G.in_edges(block, data = True)
    for e in in_edges:
      result.append((e[0], e[1], ports_set(e[2])))
    return result

  def edges_from_port(self, block, port):
    G = self._connection_graph
    result = []
    out_edges = G.out_edges(block, data = True)
    for e in out_edges:
      if e[2]['to_port'] == port:
        result.append((e[0], e[1], ports_set(e[2])))
    return result

  def edges_to_port(self, block, port):
    G = self._connection_graph
    result = []
    in_edges = G.in_edges(block, data = True)
    for e in in_edges:
      if e[2]['from_port'] == port:
        result.append((e[0], e[1], ports_set(e[2])))
    return result
