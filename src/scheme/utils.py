#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

def ports_set(edge_attrs):
  return (edge_attrs["to_port"], edge_attrs["from_port"])

def edge_str(edge):
  return "%s[%s] -> %s[%s]"%(edge[0], edge[2][0], edge[1], edge[2][1])