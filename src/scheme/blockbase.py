#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from sets import ImmutableSet as iset

class BlockBase(object):
  # Property section
  _name = ""
  _file_path = ""
  _block_type = "incomplite"
  
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
  def connection_graph(self):
    return self._connection_graph
  
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
    
  def _load_connection_graph(self, path):
    pass
    
  def _load_fa(self, path):
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
    raise Exception, "Work of incomplite block!"

  # Sugar section
  def show(self):
    self.show_fa()
  
  def show_connection_graph(self):
    self.connection_graph.show(False, self.name)
  
  def show_fa(self):
    self.fa_graph.show()
  
  def __str__(self):
    s = repr(self)
    s += "{inputs: %s, outputs: %s}" % (str(list(self.inputs)), str(list(self.outputs)))
    return s
    
  def __repr__(self):
    return "<%s>" % self.name
