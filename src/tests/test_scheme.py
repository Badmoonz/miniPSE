# encoding: utf-8
# Copyright (C) Datadvance, 2013


#import sys
#sys.path.append("../")

from src import scheme

from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises

def load_library(lib_name):
  import os
  import os.path as osp
  scheme.import_library(osp.join(os.path.dirname(__file__), "../../blocks", lib_name), verbose = True)

class TestLibrary:
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_library_atomics(self):
    load_library("atomic")
    assert len(scheme.lib) > 0, "Library is empty %d" % len(scheme.lib)
    scheme.clear_library()
    assert len(scheme.lib) == 0, "Library is not empty %d after cleaning" % len(scheme.lib)

  def test_composites(self):
    load_library("atomic")
    load_library("composite")
    assert len(scheme.lib) > 0, "Library is empty %d" % len(scheme.lib)
    scheme.clear_library()
    assert len(scheme.lib) == 0, "Library is not empty %d after cleaning" % len(scheme.lib)

  def test_super_composites(self):
    load_library("atomic")
    load_library("composite")
    load_library("composite_composite")
    assert len(scheme.lib) > 0, "Library is empty %d" % len(scheme.lib)
    scheme.clear_library()
    assert len(scheme.lib) == 0, "Library is not empty %d after cleaning" % len(scheme.lib)

  def test_case_1(self):
    pass


def assert_block(block_name):
  assert scheme.lib[block_name], "There no block %s in the lib!" % block_name

class TestAtomics:
  def setUp(self):
    load_library("atomic")

  def tearDown(self):
    scheme.clear_library()

  def test_blocks(self):
    blocks = ["Map", "F"]
    map(assert_block, blocks)

class TestComposites:
  def setUp(self):
    pass
  def tearDown(self):
    pass

  def test_E(self):
    pass


