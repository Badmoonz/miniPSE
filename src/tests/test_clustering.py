#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

from ..clustering import Group
from ..clustering import Clustering

from .. import scheme

from nose.tools import nottest



class TestClustering:
  def setUp(self):
    scheme.load_all_default_libraries()

  def tearDown(self):
    scheme.clear_library()

  def test_group(self):
    ex = scheme.lib["Example4"]
    g = Group(ex)
    g.add_nodes(["map2", "f"])
    g.try_to_convert()

  @nottest
  def test_clustering(self):
    ex = scheme.lib["Example4"]

    g = Group(ex)
    g.add_nodes(["map2", "f"])

    clustered = Clustering(ex)
    clustered.aggregate_group(g, "Group1")
    # clustered.connection_graph.show(True)