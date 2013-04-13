# encoding: utf-8
# Copyright (C) Datadvance, 2013

from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises

from itertools import combinations

from src.scheme.workflow import BaseWaveSplit as BWS

class TestWaveSplit:
  def setUp(self):
    pass
  def tearDown(self):
    pass

  def test_create_new(self):
    for init in [True, False, None]:
      assert_equal(BWS(init = init), BWS(init = init))
      assert_equal(BWS(init = init).is_basic(), True)

    #id = 0, len = 1, init = True
    assert_equal(BWS(0, 1, init = True), BWS())

  def test_expand(self):
    for init in [True, False, None]:
      w1 = BWS(init = init).expand()
      if init is None:
        assert_equal(w1, BWS(init = None))
      else:
        assert_equal(w1, BWS(init = False))

    w2 = BWS().expand(0,2).expand(1,6)
    assert_equal(w2.is_basic(), False)
     
  def tets_sum(self):
    w1 = BWS(init = None)
    #commutation
    for i,j  in combinations([True, False, None], 2):
      if i == j == None:
        assert_equal(BWS(init = i) + BWS(init = j), BWS(init = None))
      else:
        assert_equal(BWS(init = i) + BWS(init = j), BWS(init = False))


    SPLITTING = 5
    w1 = BWS(init = None)
    for i,j in combinations(range(SPLITTING), 2):
      w1 +=  BWS().expand(j, SPLITTING).expand(i, SPLITTING)
    assert_equal(w1, BWS(init = False))

    w2 = BWS().expanf(1,2).expand(0,4)
    assert_equal(w2 + BWS(), BWS(init = False))


  def test_is_expanded_from(self):
    w = BWS()
    w2 = BWS().expand()
    assert_equal(w2.is_expanded_from(w), True)
    w3 = BWS().expand(2, 5)
    assert_equal(w3.is_expanded_from(w), True)
    w4 = BWS().expand(1, 5)
    assert_equal(w3.is_expanded_from(w4), False)
    assert_equal(w4.is_expanded_from(w3), False) 
    w5 = w3 + w4
    w5.expand(0,2)
    assert_equal(w5.is_expanded_from(w4), True)
    assert_equal(w5.is_expanded_from(w3), True)


  def test_is_ahead(self):
    w1 = BWS().expand(0, 3)
    w2 = BWS().expand(1, 3)
    assert_not_equal(w1.is_ahead(w2), True)
    assert_not_equal(w2.is_ahead(w1), True)
    w2._spoil()
    assert_equal(w1.is_ahead(w2), True)
    assert_not_equal(w2.is_ahead(w1), True)
    w1.expand(1,3)
    assert_not_equal(w1.is_ahead(w2), True)
    assert_not_equal(w2.is_ahead(w1), True)


    w1 = BWS().expand(0, 3)
    w2 = BWS().expand(1, 3)
    w3 = BWS().expand(2, 3)
    w2.after = w1
    w3.after = w2 + w2.after
    assert_equal(w1.is_ahead(w2), True)
    assert_equal(w1.is_ahead(w3), True)
    assert_not_equal(w2.is_ahead(w1), True)
    assert_not_equal(w3.is_ahead(w1), True)
    assert_equal(w2.is_ahead(w3), True)
    assert_not_equal(w3.is_ahead(w2), True)
    w1._spoil()
    assert_not_equal(w1.is_ahead(w2), True)
    assert_not_equal(w2.is_ahead(w1), True)   
    assert_not_equal(w3.is_ahead(w1), True) 








