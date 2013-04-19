#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from ..scheme import Composite


class Pattern(Composite):
  PATTERN = 'pattern'
  _block_type = Pattern.PATTERN
  _is_composite = False
  _block_group = Pattern.PATTERN