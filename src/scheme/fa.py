#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

import networkx as nx
from utils import split_ports
from utils import WorkVariant

INITIAL = "initial"

class FA:

  _G = None
  _file_path = ""

  def __init__(self, path):
    self._G = nx.read_dot(path)
    self._transform()
    self._validate()

  def _transform(self):
    self.properties["inputs"] = split_ports(self.properties["inputs"])
    self.properties["outputs"] = split_ports(self.properties["outputs"])
    for s in self.edges:
      for e in self.edges[s]:
        for v in self.edges[s][e]:
          edge = self.edges[s][e][v]
          edge["inputs"] = split_ports(edge["inputs"])
          edge["outputs"] = split_ports(edge["outputs"])
          edge["probability"] = float(edge.get("p", 1.))

  def _validate(self):
    for s in self.edges:
      prob_sum = 0.
      for e in self.edges[s]:
        for v in self.edges[s][e]:
          edge = self.edges[s][e][v]
          assert edge["inputs"].issubset(self.inputs),\
            "Inputs of edge %s -> %s of %s FA is bad: should be non-empty subset of %s" % (s, e, self.name, self.inputs)
          assert edge["outputs"].issubset(self.outputs),\
            "Outputs of edge %s -> %s of %s FA is bad: should be non-empty subset of %s" % (s, e, self.name, self.outputs)
          prob_sum+=edge['probability']
      assert prob_sum == 1. , "[%s]: Wrong probability destribution from state `%s`" % (self.name, s)    


  def save(self, path = None):
    pass

  def refresh(self, path = None):
    pass

  def to_dot(self):
    node_pattern = """  "%s" [color=%s];\n"""
    edge_pattern = """  "%s" -> "%s" [label=\"[%s] / [%s]\"];\n"""
    dot_pattern = """digraph %s {\n rankdir=LR;\n%s\n}"""
    body = ""
    for n in self.nodes:
      body += node_pattern % (n, "green" if n == INITIAL else "black")

    for s in self.edges:
      for e in self.edges[s]:
        for v in self.edges[s][e]:
          edge = self.edges[s][e][v]
          body += edge_pattern % (s, e, ", ".join(edge["inputs"]), ", ".join(edge["outputs"]))
    return dot_pattern % (self.name, body)

  def show(self):
    dot = self.to_dot()
    import subprocess
    from tempfile import NamedTemporaryFile
    import os
    with NamedTemporaryFile(delete = False) as f:
      f.write(dot)
      f.close()
      subprocess.call(["xdot", f.name], shell = False)
    os.unlink(f.name)

  def save_repr(self, path):
    dot = self.to_dot()
    file = open(path, "w")
    file.write(dot)
    file.close()

  def variants(self, state, inputs):
    variants = set()
    if not state in self.nodes:
      raise Exception, "Uknown state `%s` of block `%s`"%(state, self.name)
    for next_state in self.edge[state]:
      for variant in self.edge[state][next_state].values():
        if inputs.issuperset(variant['inputs']):
          variants.add(WorkVariant(variant['inputs'], variant['outputs'], next_state, variant["probability"]))
    return variants

  @property
  def G(self):
    return self._G

  @property
  def node(self):
    return self._G.node
  
  @property
  def nodes(self):
    return self.node
  
  @property
  def edge(self):
    return self._G.edge

  @property
  def edges(self):
    return self._G.edge
  
  @property
  def name(self):
    return self._G.graph['name']
  
  @property
  def properties(self):
    return self._G.graph["graph"]
  
  @property
  def inputs(self):
    return self.properties['inputs']
  
  @property
  def outputs(self):
    return self.properties['outputs']


class TrivialFA(FA):
  def __init__(self, initial, inputs, outputs):
    self._G = nx.MultiDiGraph()
    self._G.add_node(initial)

    self._G.graph["graph"] = dict()
    self.properties["inputs"] = inputs
    self.properties["outputs"] = outputs
    self._G.graph["name"] = "trivial"