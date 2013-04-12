# encoding: utf-8
# Copyright (C) Datadvance, 2013

import sys
sys.path.append("../")
import scheme

from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises

from itertools import combinations

from scheme.workflow import WorkflowState
from scheme.workflow import Workflow

class TestWorkflow:
  def setUp(self):
    pass
  def tearDown(self):
    pass

  def test_run_example1(self):
    w = Workflow(composite = scheme.lib['Example'])
    w.work()