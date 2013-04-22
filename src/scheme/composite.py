#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from blockbase import BlockBase
from utils import split_by_comma, pure_block_states

import connection
import fa
from fa import FA
from fa import TrivialFA

from sets import ImmutableSet as iset
import networkx as nx
import os.path as osp

from utils import ports_set


class Composite(BlockBase):
  _block_type = 'composite'
  _is_composite = True
  _nfa_graph = None

  def _load_connection_graph(self, path):
    self._connection_graph = connection.ConnectionGraph(path)
    self._name = self._connection_graph.name
    self._inputs = self._connection_graph.inputs
    self._outputs = self._connection_graph.outputs
    if "block_groups" in self._connection_graph.properties:
      self._block_groups = set(split_by_comma(self._connection_graph.properties["block_groups"]))
    else:
      self._block_groups = set()

  def _load_fa(self, path):
    path_fa = (path if path else self.file_path) + ".fa"
    path_nfa = (path if path else self.file_path) + ".nfa"
    if osp.isfile(path_fa) and osp.isfile(path_nfa):
      self._fa_graph = FA(path_fa)
      self._nfa_graph = FA(path_nfa)
    else:
      self._fa_graph = TrivialFA("initial", self.inputs, self.outputs)
      self._nfa_graph = TrivialFA("initial", self.inputs, self.outputs)

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

  def _set_data_from_graphs(self):
     self._name = self.connection_graph.name
     self._inputs = self.connection_graph.inputs
     self._outputs = self.connection_graph.outputs
     if "block_groups" in self._connection_graph.properties:
        self._block_groups = split_by_comma(self._connection_graph.properties["block_groups"])

     self._initial_state = str(dict((x, fa.INITIAL) for x in self._connection_graph.node))

     self._fa_graph = TrivialFA(pure_block_states(self.initial_state), self.inputs, self.outputs)
     self._nfa_graph = TrivialFA(self.initial_state, self.inputs, self.outputs)


  def _calc_fa(self):
    raise Exception, "Virtual!"

  def show(self):
    self.show_connection_graph()

  def __repr__(self):
    return "{%s}" % self.name

  @property
  def blocks(self):
    return self._connection_graph.node


  def has_path(self, src_block, dst_block):
    return nx.has_path(self._connection_graph, src_block, dst_block)

  def connected_inputs(self, block):
    G = self._connection_graph
    result = []
    in_edges = G.in_edges(block, data=True)
    for e in in_edges:
      result.append(ports_set(e[2])[1])
    return iset(result)

  def connected_outputs(self, block):
    G = self._connection_graph
    result = []
    out_edges = G.out_edges(block, data=True)
    for e in out_edges:
      result.append(ports_set(e[2])[0])
    return iset(result)

  def edges_from_block(self, block):
    G = self._connection_graph
    result = []
    out_edges = G.out_edges(block, data=True)
    for e in out_edges:
      result.append((e[0], e[1], ports_set(e[2])))
    return result

  def edges_to_block(self, block):
    G = self._connection_graph
    result = []
    in_edges = G.in_edges(block, data=True)
    for e in in_edges:
      result.append((e[0], e[1], ports_set(e[2])))
    return result

  def edges_from_port(self, block, port):
    G = self._connection_graph
    result = []
    out_edges = G.out_edges(block, data=True)
    for e in out_edges:
      if e[2]['from_port'] == port:
        result.append((e[0], e[1], ports_set(e[2])))
    return result

  def edges_to_port(self, block, port):
    G = self._connection_graph
    result = []
    in_edges = G.in_edges(block, data=True)
    for e in in_edges:
      if e[2]['to_port'] == port:
        result.append((e[0], e[1], ports_set(e[2])))
    return result
