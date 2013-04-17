# encoding: utf-8
# Copyright (C) Datadvance, 2013

from .. import scheme
from ..scheme.utils import *
from nose.tools import *

from src.scheme.workflow import Workflow

class TestWorkflow:
  def setUp(self):
    scheme.load_all_default_libraries()

  def tearDown(self):
    scheme.clear_library()

  def test_run_example1(self):
    w = Workflow(composite = scheme.lib['Example1'])
    w.work()

  def test_run_example2(self):
    w = Workflow(composite = scheme.lib['Example2'])
    w.work()

  @raises(RaceCondition)
  def test_run_example3(self):
    w = Workflow(composite = scheme.lib['Example3'])
    w.work()

  
  def test_run_example4(self):
    w = Workflow(composite = scheme.lib['Example4'])
    w.work()

  
  def test_run_example5(self):
    w = Workflow(composite = scheme.lib['Example5'])
    w.work()

  @nottest
  def test_run_example6(self):
    w = Workflow(composite = scheme.lib['Example6'])
    w.work()

  def test_example2_fa(self):
    c = scheme.lib['Example2']
    c._full_calc_fa()