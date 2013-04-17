#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

import keys
from collections import namedtuple

def ports_set(edge_attrs):
  return (edge_attrs["from_port"], edge_attrs["to_port"])

def edge_str(edge):
  print edge
  return "%s[%s] -> %s[%s]"%(edge[0], edge[2][0], edge[1], edge[2][1])

# Useful function
def split_by_comma(xs):
  return map(lambda x: x.strip(), xs.split(","))

def composite_state(val):
  result = None
  if isinstance(val, (str, unicode)):
    result = eval(val)
  elif isinstance(val, dict):
    result = dict(val)
  else:
    raise TypeError, "String or dict required"
  result.pop(keys.SOURCE)
  result.pop(keys.STOCK)
  return str(result)


WorkVariant = namedtuple('WorkVariant', ['inputs', 'outputs', 'state'])


class RaceCondition(Exception):
  pass

class SurplusWave(Exception):
  pass