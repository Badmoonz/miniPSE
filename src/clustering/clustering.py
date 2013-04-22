#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from ..scheme import Composite
from group import Group
from copy import deepcopy

class Clustering(Composite):

  def __init__(self, workflow):
    if not workflow.is_composite:
      raise Exception, "Clustering is trivial over non-composite blocks"
    self._connection_graph = deepcopy(workflow.connection_graph)
    self._name = "Clustered_" + workflow.name

  def load(self, path):
    raise NotImplementedError, "This method does not impliment yet!"

  def save(self, path=None):
    raise NotImplementedError, "This method does not impliment yet!"

  def __repr__(self):
    return "#%s#" % self.name

  def aggregate_group(self, group, group_name = None):
    if type(group) == list:
      g = Group(self.workflow, name=group_name)
      g.add_nodes(group)
    elif type(group) == Group:
      g = group
    else:
      raise Exception, "Type of group should be %s or %s!" % (type(Group), list)

    G = self.connection_graph
    new_edges = list()
    for s in G.edges:
      for e in G.edges[s]:
        for v in G.edges[s][e]:
          edge = G.edges[s][e][v]
          s_in_group = s in g.nodes
          e_in_group = e in g.nodes

          if not s_in_group and e_in_group:
            new_edges.append((s, edge["from_port"],
                              g.name, g.get_group_port_name(s, edge["from_port"], "from")))
          elif s_in_group and not e_in_group:
            new_edges.append((g.name, g.get_group_port_name(e, edge["to_port"], "to"),
                              e, edge["to_port"]))
          else:
            continue

    map(lambda (s, sp, e, ep): G.add_edge(s, sp, e, ep), new_edges)
    G.remove_nodes_from(g.nodes)

    # GenericComposite will have the same name as Group g
    G.node[g.name] = g.try_to_convert()
    return self
