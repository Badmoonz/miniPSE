# encoding: utf-8
# Copyright (C) Datadvance, 2013


import sys
sys.path.append("../")

import scheme

from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises



class TestLibrary:
  def setUp(self):
    pass
  def tearDown(self):
    pass

  def test_case_1(self):
    pass



class TestAtomics:
  def setUp(self):
    pass
  def tearDown(self):
    pass

  def test_f(self):
    print scheme.lib["F"]

  def test_map(self):
    print scheme.lib["Map"]


class TestComposites:
  def setUp(self):
    pass
  def tearDown(self):
    pass

  def test_E(self):
    pass


