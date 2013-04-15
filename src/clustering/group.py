#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from ..scheme import GenericComposite
from ..scheme import ConnectionGraph

# Dirty hack
__name_index = 0
def _get_name_index():
  global __name_index
  __name_index += 1
  return __name_index

class Group(object):
  _composite = None
  _nodes = set()
  _name = ""

  def __init__(self, composite, name=None):
    self._composite = composite
    self._nodes = set()
    self._name = name if name else ("group" + str(_get_name_index()))

  def add_node(self, node):
    if not node in self._composite.connection_graph.nodes:
      raise Exception, "There is not block %s in composite %s!" % (node, self._composite)
    else:
      self._nodes.add(node)

  def add_nodes(self, nodes):
    map(lambda n: self.add_node(n), nodes)

  def remove_node(self, node):
    self._nodes.remove(node)

  @property
  def name(self):
    return self._name

  @property
  def nodes(self):
    return self._nodes

  def get_group_port_name(self, block, port, direction):
    return "_".join([direction, block, port])

  def convert_to_composite(self, composite_name = None):
    in_edges = list()
    out_edges = list()
    composite = GenericComposite(name=(composite_name if composite_name else self.name))
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
            G.add_edge(s, edge["from_port"], e, edge["to_port"])
          elif s_in_group and not e_in_group:
            out_edges.append((s, e, v, edge))
          elif not s_in_group and e_in_group:
            in_edges.append((s, e, v, edge))

    # Process outs
    outs = map(lambda (s, e, v, edge): "_".join(["to", e, edge["to_port"]]), out_edges)
    for s, e, v, edge in out_edges:
      G.add_edge(s, edge["from_port"],
                 ConnectionGraph.STOCK,"_".join(["to", e, edge["to_port"]]))
    # add_stock in the end, because otherwise networkx rewrite stock node
    G.add_stock(outs)

    # Process ins
    ins = map(lambda (s, e, v, edge): "_".join(["from", s, edge["from_port"]]), in_edges)
    for s, e, v, edge in in_edges:
      G.add_edge(ConnectionGraph.SOURCE, "_".join(["from", s, edge["from_port"]]),
                 e, edge["to_port"])    
    G.add_source(ins)
    return composite