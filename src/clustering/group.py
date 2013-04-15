#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from ..scheme import GenericComposite
from ..scheme import ConnectionGraph

class Group(object):
  _composite = None
  _nodes = set()

  def __init__(self, composite):
    self._composite = composite
    self._nodes = set()

  def add_node(self, node):
    if not node in self._composite.connection_graph.nodes:
      raise Exception, "There is not block %s in composite %s!" % (node, self._composite)
    else:
      self._nodes.add(node)

  def remove_node(self, node):
    self._nodes.remove(node)

  @property
  def nodes(self):
    return self._nodes

  def convert_to_composite(self):
    in_edges = list()
    out_edges = list()
    composite = GenericComposite()
    G = composite.connection_graph
    fromG = self._composite.connection_graph

    for n in fromG.node:
      print fromG.node[n].connection_graph

    for s in fromG.edges:
      for e in fromG.edges[s]:
        for v in fromG.edges[s][e]:
          edge = fromG.edges[s][e][v]
          s_in_group = s in self._nodes
          e_in_group = e in self._nodes

          if s_in_group:
            G.node[s] = fromG.node[s]
          if e_in_group:
            G.node[e] = fromG.node[e]

          if s_in_group and e_in_group:
            G.add_edge(s, e, v, edge)
          elif s_in_group and not e_in_group:
            out_edges.append((s, e, v, edge))
          elif not s_in_group and e_in_group:
            in_edges.append((s, e, v, edge))

    # Process outs
    outs = map(lambda (s, e, v, edge): "_".join(["to", e, edge["to_port"]]), out_edges)
    for out_edge in out_edges:
      s, e, v, edge = out_edge
      G.add_edge(s, ConnectionGraph.STOCK,
                 attr_dict = {"from_port" : edge["from_port"],
                              "to_port" : "_".join(["to", e, edge["to_port"]])})
    G.add_stock(outs)

    # Process ins
    ins = map(lambda (s, e, v, edge): "_".join(["from", s, edge["from_port"]]), in_edges)
    for in_edge in in_edges:
      s, e, v, edge = in_edge
      G.add_edge(ConnectionGraph.SOURCE, e,
                 attr_dict = {"from_port" : "_".join(["from", s, edge["from_port"]]),
                              "to_port" : edge["to_port"]})
    G.add_source(ins)
    return composite