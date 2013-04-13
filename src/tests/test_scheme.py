# encoding: utf-8
# Copyright (C) Datadvance, 2013

from src import scheme

from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises

class TestLibrary:
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_library_atomics(self):
    scheme.load_default_libraries(["atomic"])
    assert len(scheme.lib) > 0, "Library is empty [%d]" % len(scheme.lib)
    scheme.clear_library()
    assert len(scheme.lib) == 0, "Library is not empty [%d] after cleaning" % len(scheme.lib)

  def test_composites(self):
    scheme.load_default_libraries(["atomic", "composite"])
    assert len(scheme.lib) > 0, "Library is empty [%d]" % len(scheme.lib)
    scheme.clear_library()
    assert len(scheme.lib) == 0, "Library is not empty [%d] after cleaning" % len(scheme.lib)

  def test_super_composites(self):
    scheme.load_default_libraries(["atomic", "composite", "supercomposite"])
    assert len(scheme.lib) > 0, "Library is empty [%d]" % len(scheme.lib)
    scheme.clear_library()
    assert len(scheme.lib) == 0, "Library is not empty [%d] after cleaning" % len(scheme.lib)

  def test_case_1(self):
    pass


def assert_block(block_name):
  assert scheme.lib[block_name], "There no block %s in the lib!" % block_name

class TestAtomics:
  def setUp(self):
    scheme.load_default_libraries(["atomic"])

  def tearDown(self):
    scheme.clear_library()

  def test_blocks(self):
    blocks = ["Map", "F"]
    map(assert_block, blocks)

class TestComposites:
  def setUp(self):
    scheme.load_default_libraries(["atomic", "composite", "supercomposite"])

  def tearDown(self):
    scheme.clear_library()

  def test_Examples(self):
    numbers = range(1, 7)
    composite_names = map(lambda x: "Example" + str(x), numbers)
    map(assert_block, composite_names)