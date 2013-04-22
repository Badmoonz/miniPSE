#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

import atomic
import composite
# from gcomposite import GComposite
import os
import os.path as osp

__library = dict()

default_library_path = {
    "atomic": osp.abspath(osp.dirname(__file__) + "../../../blocks/atomic"),
    "composite" : osp.abspath(osp.dirname(__file__) + "../../../blocks/composite"),
    "supercomposite" : osp.abspath(osp.dirname(__file__) + "../../../blocks/supercomposite")
}

default_load_order = ["atomic", "composite", "supercomposite"]


def load_default_libraries(lib_names):
  importer = lambda lname: import_library(default_library_path[lname], verbose=True)
  map(importer, lib_names)


def load_all_default_libraries():
  load_default_libraries(default_load_order)


def clear_library():
  __library.clear()


def import_library(path, into = __library, lib_prefix = "", verbose = False):
  items = os.listdir(path)
  for item in items:
    item_path = osp.join(path, item)
    if osp.isfile(item_path):
      if item.endswith(".atomic"):
        import_atomic(item_path, into, lib_prefix, verbose)
      elif item.endswith(".composite"):
        import_composite(item_path, into, lib_prefix, verbose)
      elif item.endswith(".dot"):
        continue
      elif verbose:
        print "File %s has unknown extention!" % item_path
        continue
    
    elif osp.isdir(item_path) and not item.startswith("."):
      if into.has_key(item):
        raise Exception("Sublibrary %s%s has name has already been imported!" % (lib_prefix, item))
      into[item] = dict()
      import_library(item_path, into[item], lib_prefix + "." + item, verbose)
  return into


def __add_block(path, constr, into = __library, lib_prefix = "", verbose = False):
  try:
    block = constr(path)
  except Exception as e:
    raise Exception, "Fail to load %s: %s" % (path, e)
  
  if into.has_key(block.name):
    raise Exception("Block %s%s has name has already been imported!" % (lib_prefix, block.name))
  else:
    into[block.name] = block
    if verbose:
      print "Block %s%s has been loaded." % (lib_prefix, repr(block))


def import_composite(path, into = __library, lib_prefix = "", verbose = False):
  __add_block(path, lambda p: composite.Composite(p), into, lib_prefix, verbose)


def import_atomic(path, into = __library, lib_prefix = "", verbose = False):
  __add_block(path, lambda p: atomic.Atomic(p), into, lib_prefix, verbose)


def get_block(block_name, library = __library):
  block_path = block_name.split(".")
  try:
    block = __get_block_by_path(block_path, library)
  except Exception as e:
    raise Exception("Fail while search block %s: %s" % (block_name, e.message))
  return block


def __get_block_by_path(block_path, lib = __library):
  if not block_path:
    raise Exception("What?")
  
  if block_path[0] in lib:
    if (len(block_path) == 1) == (type(lib[block_path[0]]) is dict):
      raise Exception("wrong name")
      
    if type(lib[block_path[0]]) is dict:
      return __get_block_by_path(block_path[1:], lib = lib[block_path[0]])
    else:
      return lib[block_path[0]]
  else:
    raise Exception("can not find")


def get_main_library():
  return __library


def reload_library(lib = __library, lib_prefix = "", verbose = True):
  for item in lib:
    if type(lib[item]) == dict:
      reload_library(lib[item], lib_prefix + "." + item)
    else:
      block_type = lib[item].block_type
      path = lib.pop(item).file_path
      if block_type == "composite":
        import_composite(path, lib, lib_prefix, verbose)
      elif block_type == "atomic":
        import_atomic(path, lib, lib_prefix, verbose)
      else:
        raise Exception("Bad block %s in library %s", lib[item], lib_prefix)

load_workflow = import_composite
