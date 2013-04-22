#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from ..scheme import load_all_default_libraries
from ..scheme import clear_library
from ..scheme import lib

from ..clustering import ImplicitConnection

class TestImplicitConnection:

  def setUp(self):
    load_all_default_libraries()

  def tearDown(self):
    clear_library()

  def test_load(self):
    ImplicitConnection("../blocks/implicit/map.implicit")

  def test_match(self):
    impl = ImplicitConnection("../blocks/implicit/map.implicit")
    assert impl.match_node("base", lib["Map"]), "Implicit `map' should match real `map' by group `for-like'"
    assert impl.match_node("f", lib["F"]), "Implicit `f' should match real `f' by group `functional'"
    assert impl.match_node("f", lib["Tube"]), "Implicit `f' should match real `f' by group `functional'"
    assert impl.match_node("f", lib["Example4"]), "Implicit `f' should match pure compisite."
    assert (not impl.match_node("f", lib["Map"])), "Implicit `f' should not match `Map' block."
    assert (not impl.match_node("f", lib["Example3"])), "Implicit `f' should not match dirty compisite."
