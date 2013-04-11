# encoding: utf-8
# Copyright (C) Datadvance, 2013


import unittest
import sys

from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises

sys.path.append("../")

import scheme

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
    print scheme.lib["Example"]


class TestWorkflow:
  def setUp(self):
    pass
  def tearDown(self):
    pass

  def test_run_E(self):
    from scheme import Workflow
    from scheme import lib
    w = Workflow(lib['Example'])
    for i in xrange(5):
      w.step()
    w.show_state_pool()


