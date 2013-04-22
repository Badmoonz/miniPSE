#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

import networkx as nx
from ..scheme import ConnectionGraph
from ..scheme.connection import split_ports
from ..scheme.blockbase import split_by_comma
from ..scheme import get_block
from copy import copy

node_default_dict = {
                     "block_type" : None,
                     "block_groups" : set([]),
                     "inputs" : None,
                     "outputs" : None
                    }

class ImplicitConnection(ConnectionGraph):
  def _transform(self):
    self._inputs = split_ports(self.properties["inputs"]) if self.properties.has_key("inputs") else None
    self._outputs = split_ports(self.properties["outputs"]) if self.properties.has_key("outputs") else None

    self._transform_nodes()
    self._transform_edges()

  def _transform_nodes(self):
    for n in self.nodes:
      def_copy = copy(node_default_dict)
      def_copy.update(self.nodes[n])
      self.nodes[n] = def_copy

      self.nodes[n]["block_groups"] = set(split_by_comma(self.nodes[n]["block_groups"]))

      if self.nodes[n]["inputs"]:
        self.nodes[n]["inputs"] = set(split_by_comma(self.nodes[n]["inputs"]))

      if self.nodes[n]["outputs"]:
        self.nodes[n]["outputs"] = set(split_by_comma(self.nodes[n]["inputs"]))

  def _transform_edges(self):
    for s in self.edges:
      for e in self.edges[s]:
        for v in self.edges[s][e]:
          edge = self.edge[s][e][v]
          edge["from_port"] = edge.pop("tailport", None)
          edge["to_port"] = edge.pop("headport", None)

  def validate(self):
    self._validate_nodes()
    self._validate_edges()

  def _validate_nodes(self):
    # Fuck python without partial formatting!
    not_contain = "Implicit connection graph `" + self.name + "' does not contain `%s' block!"
    assert "source" in self.nodes, not_contain % "source"
    assert "stock" in self.nodes, not_contain % "stock"
    assert "base" in self.nodes, not_contain % "base"

    human_all = lambda pred, xs: all(map(pred, xs))
    is_default = lambda node, prop: self.nodes[node][prop] == node_default_dict[prop]
    is_all_default = lambda node:  human_all(lambda prop: is_default(node, prop), node_default_dict.keys())
    non_default = "`%s' block in implicit connection `" + self.name + "' graph can not contain non-default values!"
    assert is_all_default("source"), non_default % "source"
    assert is_all_default("stock"), non_default % "stock"

    non_type = "Can not find block type %s of node %s in `" + self.name + "' implicit connection graph!"
    for n in self.nodes:
      node = self.nodes[n]
      if node["block_type"]:
        try:
          get_block(node["block_type"])
        except Exception:
          raise Exception, non_type % (node["block_type"], n)


  def _validate_edges(self):
    for s in self.edges:
      for e in self.edges[s]:
        for v in self.edges[s][e]:
          edge = self.edges[s][e][v]
          if edge["from_port"] and self.nodes[s]["block_type"]:
            assert edge["from_port"] in get_block(self.nodes[s]["block_type"])

  def port_to_dot(self, external_name, port, direction):
    raise Exception, "Can not represent implicit connection graph as subgraph!"

  def to_dot(self, external_name=None, hierarchical=False, subgraph=False):
    dots = list() 
    for n in self.nodes:
      node_pattern = "  " + n + " [shape=%s, label=\"%s\"];\n"
      if self.nodes[n]["inputs"]:
        inputs = self.nodes[n]["inputs"]
        outputs = self.nodes[n]["outputs"]
        shape = "Mrecord"
        label = "{ %s | {%s} | {%s}}" % \
                (n, " | ".join(inputs), " | ".join(outputs))
      else:
        label = n
        shape = "circle"
      dots.append(node_pattern % (shape, label))

    edge_pattern = "  %s -> %s;\n"
    for s in self.edges:
      for e in self.edges[s]:
        for v in self.edges[s][e]:
          edge = self.edges[s][e][v]
          if edge.has_key("from_port"):
            from_edge = "%s:%s" % (s, edge["from_port"])
          else:
            from_edge = "%s" % s

          if edge.has_key("to_port"):
            to_edge = "%s:%s" % (e, edge["to_port"])
          else:
            to_edge = "%s" % e

          dots.append(edge_pattern % (from_edge, to_edge))
    dot_pattern = "digraph %s {\n  rankdir=LR;\n%s\n}"
    return dot_pattern % (self.name, "\n".join(dots))

  def match_node(self, self_node, external_node):
    assert self_node in self.nodes, "There are not node `%s' in implicit connection graph `%s'" % (self_node, self.name)
    pattern = self.nodes[self_node]

    if pattern["outputs"] and pattern["outputs"] != external_node.outputs:
      return False

    if pattern["inputs"] and pattern["inputs"] != external_node.inputs:
      return False

    if not pattern["block_groups"].issubset(external_node.block_groups):
      return False

    if pattern["block_type"] and pattern["block_type"] != external_node.name:
      return False

    return True