#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013
from networkx.classes.function import subgraph

import fa
from sets import ImmutableSet as iset

# Useful function
def split_by_comma(xs):
  return map(lambda x: x.strip(), xs.split(",")) if xs else list()

class BlockBase(object):
  # Property section
  _name = ""
  _file_path = ""
  _block_type = "incomplite"
  _initial_state = fa.INITIAL
  _is_composite = False
  _block_groups = list()
  
  _connection_graph = None
  _fa_graph = None
  
  _inputs = iset()
  _outputs = iset()
  
  # Property section
  @property
  def name(self):
    return self._name
  
  @property
  def file_path(self):
    return self._file_path
  
  @property
  def block_type(self):
    return self._block_type

  @property
  def block_groups(self):
    return self._block_groups

  @property
  def is_composite(self):
    return self._is_composite
  
  @property
  def connection_graph(self):
    return self._connection_graph
  
  @property
  def initial_state(self):
    return self._initial_state

  @property
  def fa_graph(self):
    return self._fa_graph

  @property
  def inputs(self):
    return self._inputs

  @property
  def outputs(self):
    return self._outputs
  
  # Load section
  def __init__(self, path):
    self._file_path = path
    self.load(path)
    self.validate()
  
  def load(self, path):
    self._load_fa(path)
    self._load_connection_graph(path)
    self._set_data_from_graphs()
    
  def _load_connection_graph(self, path):
    pass
    
  def _load_fa(self, path):
    pass

  def _set_data_from_graphs(self):
    pass

  # Save section
  def save(self, path = None):
    path_ =  path if path else self._file_path
    self._save_fa(path_)
    self._save_connection_graph(path_)

  def _save_fa(self, path):
    pass

  def _save_connection_graph(self, path):
    pass

  # Validate section
  def validate(self):
    pass
  
  # Refresh section
  def refresh(self):
    self.fa_graph.save(self.file_path)
    
  # Main method
  def work(self, state, inputs):
    if self.fa_graph:
      return self._fa_graph.variants(state, inputs)
    else:
      raise Exception, 'No FA defined'

  # Sugar section
  def show(self):
    self.show_fa()
  
  def show_connection_graph(self):
    self.connection_graph.show(False, self.name)
  
  def show_fa(self):
    self.fa_graph.show()

  def save_representation(self, path, hierarchical=False):
    self._connection_graph.save_repr(path + "_cg.dot", hierarchical, external_name=self.name)
    self._fa_graph.save_repr(path + "_fa.dot")
  
  def __str__(self):
    s = repr(self)
    s += "{inputs: %s, outputs: %s}" % (str(list(self.inputs)), str(list(self.outputs)))
    return s
    
  def __repr__(self):
    return "<%s>" % self.name
