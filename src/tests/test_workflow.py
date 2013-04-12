# encoding: utf-8
# Copyright (C) Datadvance, 2013

#import sys
#sys.path.append("../")

from src import scheme

from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises

from itertools import combinations

from src.scheme.workflow import Workflow

def load_library(lib_name):
  import os
  import os.path as osp
  scheme.import_library(osp.join(os.path.dirname(__file__), "../../blocks", lib_name), verbose = True)

class TestWorkflow:
  def setUp(self):
    load_library("atomic")
    load_library("composite")
    load_library("composite_composite")

  def tearDown(self):
    scheme.clear_library()

  def test_run_example1(self):
    w = Workflow(composite = scheme.lib['Example'])
    w.work()

  def test_run_example2(self):
    w = Workflow(composite = scheme.lib['Example2'])
    w.work()

  def test_run_example3(self):
    w = Workflow(composite = scheme.lib['Example3'])
    w.work()

  def test_run_example4(self):
    w = Workflow(composite = scheme.lib['Example4'])
    w.work()
  
  def test_run_example5(self):
    w = Workflow(composite = scheme.lib['Example5'])
    w.work()

  def test_run_example6(self):
    w = Workflow(composite = scheme.lib['Example6'])
    w.work()