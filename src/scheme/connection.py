#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

# It is simple wrapper on nx.MultiDiGraph

import library
import networkx as nx
from blockbase import BlockBase
from blockbase import split_by_comma
from sets import ImmutableSet as iset

def ports_dot(ports):
  return map(lambda p: "<%s> %s" % (p, p), ports)
  
def split_ports(s):
  if not s:
    return iset()
  return iset(split_by_comma(s))

class ConnectionGraph:
  _file_path = ""
  STOCK = "stock"
  SOURCE = "source"

  _inputs = set()
  _outputs = set()
  
  @property
  def file_path(self):
    return self._file_path
  
  _G = nx.MultiDiGraph()
  
  def __init__(self, path = None):
    """
      Load and convert dot graph.
    """
    if not path is None:
      self._file_path = path
      self._G = nx.read_dot(path)
      self.__transform()
  
  def __transform(self):
    self._inputs = split_ports(self.properties["inputs"])
    self._outputs = split_ports(self.properties["outputs"])
    self.__transform_nodes()
    self.__transform_eadges()
  
  def __transform_nodes(self):
    for node in self.nodes:
      if not (node == ConnectionGraph.SOURCE or  node == ConnectionGraph.STOCK):
        self.nodes[node] = library.get_block(self.nodes[node]["block_type"])
      elif node == ConnectionGraph.SOURCE:
        self.add_source(self.inputs)
      elif node == ConnectionGraph.STOCK:
        self.add_stock(self.outputs)
   
  def __transform_eadges(self):
    for s in self.edges:
      for e in self.edges[s]:
        for v in self.edges[s][e]:
          edge = self.edges[s][e][v]
          edge['from_port'] = edge.pop('tailport')
          edge['to_port'] = edge.pop('headport')
    
  def __validate(self):
    for src in self.edges:
      for dest in self.edges[src]:
        for variant in self.edges[src][dest]:
          edge = self.edge[src][dest][variant]
          self.__check_block_port(src, edge['from_port'], 'outputs')
          self.__check_block_port(dest, edge['to_port'], 'inputs')
    self_loops = self._G.selfloop_edges()
    if self_loops:
      raise Exception, "Self loops detected! %s" % (self_loops)

  def __check_block_port(self, block, port_name, direction):
    """
    direction = 'inputs' or 'outputs'
    """
    if not port_name in getattr(self.node[block], direction):
      raise Exception, "Block '%s' doesn't have %s port '%s'" % (block, direction, port_name)

  def add_source(self, inputs):
    self.nodes[ConnectionGraph.SOURCE] = SourceBlock(inputs)
    self._inputs = set(inputs)

  def add_stock(self, outputs):
    self.nodes[ConnectionGraph.STOCK] = StockBlock(outputs)
    self._outputs = set(outputs)

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
    return self._inputs
  
  @property
  def outputs(self):
    return self._outputs

  def add_edge(self, from_b, from_p, to_b, to_p):
    self._G.add_edge(from_b, to_b,
                     from_port=from_p, to_port=to_p)
  
  def __getattr__(self, name):
    try:
      return self.__getattribute__(name)
    except:
      pass
    finally:
      return getattr(self._G, name)


  def show(self, hierarchical = False, external_name = None):
    dot = self.to_dot(external_name, hierarchical, subgraph = False)
    import subprocess
    from tempfile import NamedTemporaryFile
    import os
    with NamedTemporaryFile(delete = False) as f:
      f.write(dot)
      f.close()
      subprocess.call(["xdot", f.name], shell = False)
    os.unlink(f.name)
  
  def port_to_dot(self, external_name, port, direction):
    return "%s_%s:%s" % (external_name, direction, port)
  
  def to_dot(self, external_name = None, hierarchical = False, subgraph = False):
    if external_name is None:
      external_name = self.name
    
    if hierarchical:
      def node_dot(node, node_name):
        return node.to_dot(external_name + "_" + node_name, True, True)
    else:
      def node_dot(node, node_name):
        return TrivialConnectionGraph(node.inputs, node.outputs).to_dot(external_name + "_" + node_name, True, True)
    
    if hierarchical:
      def edge_dot(from_node, from_name, to_node, to_name, attrs):
        pattern = """  %s -> %s[color = "%s"];\n"""
        from_p = attrs["from_port"]
        to_p = attrs["to_port"]
        color = attrs.get("color", "black")
        from_s = from_node.port_to_dot(external_name + "_" + from_name, from_p, ConnectionGraph.STOCK)
        to_s = to_node.port_to_dot(external_name + "_" + to_name, to_p, ConnectionGraph.SOURCE)
        return pattern % (from_s, to_s, color)
    else:
      def edge_dot(from_node, from_name, to_node, to_name, attrs):
        from_p = attrs["from_port"]
        to_p = attrs["to_port"]
        color = attrs.get("color", "black")
        pattern = """  %s -> %s[color = "%s"];\n"""
        from_l = external_name + "_" + from_name + ":" + from_p
        to_l = external_name + "_" + to_name + ":" + to_p
        return pattern % (from_l, to_l, color) 
    
    def header():
      if subgraph:
        return """subgraph cluster_%s {\n  color = blue;\n  rankdir = LR;\n  label = "%s";\n""" % \
                (external_name, external_name)
      else:
        return "digraph " + external_name + "{\n rankdir = LR;\n"
    
    def ender():
      return "}\n"
    
    dot = header()
    for n in self.nodes:
      dot += node_dot(self.nodes[n].connection_graph, n)

    for s in self.edge:
      for e in self.edge[s]:
        for v in self.edge[s][e]:
          from_n = self.node[s].connection_graph
          to_n = self.node[e].connection_graph
          dot += edge_dot(from_n, s, to_n, e, self.edge[s][e][v])
          
    dot += ender()
    return dot

class TrivialConnectionGraph(ConnectionGraph):
  def __init__(self, inputs, outputs):
    self._inputs = inputs
    self._outputs = outputs

  def port_to_dot(self, external_name, port, direction):
    return "%s:%s" % (external_name, port)
  
  def to_dot(self, external_name = None, hierarchical = False, subgraph = False):
    if not external_name:
      external_name = "trivial"
    
    def header():
      return "digraph " + external_name + "{\n  rankdir=LR;\n"
        
    def ender():
      return "}"
    
    pattern = """  %s [shape=Mrecord, label="%s"];\n"""
    inputs = " | ".join(ports_dot(self.inputs))
    outputs = " | ".join(ports_dot(self.outputs))
    ports_l = " | ".join((["{%s}" % inputs] if inputs else []) + (["{%s}" % outputs] if outputs else [])) 
    label = "%s | {%s}" % (external_name, ports_l)
    if subgraph:
      return pattern % (external_name, label)
    else:
      return header() + pattern % (external_name, label) + ender()

# Support class defenition
class SourceBlock(BlockBase):
  _name = ConnectionGraph.SOURCE
  _block_type = ConnectionGraph.SOURCE
  _block_group = ConnectionGraph.SOURCE

  def __init__(self, outputs):
    self._outputs = set(outputs)
    self._connection_graph = TrivialConnectionGraph([], outputs)

  def port_to_dot(self, external_name, port, direction):
    name = external_name if external_name else self.name
    return "%s:%s" % (external_name, port)

  def to_dot(self, external_name = None, hierarchical = False, subgraph = False):
    pattern = """  {rank = %s; %s [shape=Mrecord, label="%s"];}\n"""
    label = "|".join(ports_dot(self._outputs))
    return pattern % ("source", external_name, label)

class StockBlock(BlockBase):
  _name = ConnectionGraph.STOCK
  _block_type = ConnectionGraph.STOCK
  _block_group = ConnectionGraph.STOCK

  def __init__(self, inputs):
    self._inputs = set(inputs)
    self._connection_graph = TrivialConnectionGraph(inputs, [])
  
  def port_to_dot(self, external_name, port, direction):
    name = external_name if external_name else self.name
    return "%s:%s" % (external_name, port)
  
  def work(self, state, inputs):
    return set()

  def to_dot(self, external_name, hierarchical = False, subgraph = False):
    pattern = """  {rank = %s; %s [shape=Mrecord, label="%s"];}\n"""
    label = "|".join(ports_dot(self._inputs))
    return pattern % ("sink", external_name, label)
    
