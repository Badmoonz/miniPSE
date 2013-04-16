#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from composite import Composite
from connection import ConnectionGraph

# Dirty hack
__name_index = 0
def _get_name_index():
  global __name_index
  __name_index += 1
  return __name_index

class GenericComposite(Composite):
  GENERIC = "generic"
  _block_type = GENERIC
  _block_group = GENERIC

  def __init__(self, path=None, connection_graph=None, name=None, group=None):
    if path:
      self.load(path)
    else:
      self._connection_graph = ConnectionGraph()
      self._name = name if name else ("generic" + str(_get_name_index()))
      self._block_group = group if group else GenericComposite.GENERIC

  def load(self, path):
    raise NotImplementedError, "This method does not impliment yet!"

  def __repr__(self):
    return "<%s>" % self.name