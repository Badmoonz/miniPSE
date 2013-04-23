#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013


from collections import namedtuple
from sets import ImmutableSet as iset


def ports_set(edge_attrs):
    return edge_attrs["from_port"], edge_attrs["to_port"]


def edge_str(edge):
    print edge
    return "%s[%s] -> %s[%s]"%(edge[0], edge[2][0], edge[1], edge[2][1])


# Useful function
def split_by_comma(xs):
    return map(lambda x: x.strip(), xs.split(","))


def ports_dot(ports):
    return map(lambda p: "<%s> %s" % (p, p), ports)


def split_ports(s):
    if not s:
        return iset()
    return iset(split_by_comma(s))


def pure_block_states(val):
    result = None
    if isinstance(val, (str, unicode)):
        result = eval(val)
    elif isinstance(val, dict):
        result = dict(val)
    else:
        raise TypeError, "String or dict required"
    result.pop("source") if "source" in result else None
    result.pop("stock") if "stock" in result else None
    return str(result)


WorkVariant = namedtuple('WorkVariant', ['inputs', 'outputs', 'state'])


class RaceCondition(Exception):
    pass


class SurplusWave(Exception):
    pass