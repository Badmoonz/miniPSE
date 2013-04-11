#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013

import networkx as nx

from composite import Composite
from atomic import Block

import copy
from copy import deepcopy
from sets import ImmutableSet as iset
from tempfile import NamedTemporaryFile
import os
from collections import namedtuple
from itertools import combinations

def ports_set(edge_attrs):
  return (edge_attrs["tailport"], edge_attrs["headport"])

def edge_str(edge):
  return "%s[%s] -> %s[%s]"%(edge[0], edge[2][0], edge[1], edge[2][1])

class Workflow(object):
  def __init__(self, composite):
    self._composite = composite
    self._state_pool = []
    self._active_states = []
    self._step_counter = 0
    self._flow_graph = nx.MultiDiGraph()
    self.__add_new_state(None, WorkflowState(composite = self._composite))
    self.show_active_states()
    
 
  def step(self):
    self._step_counter += 1
    generated_states = []
    active_states = set(self._active_states)
    self._active_states = []
    for current_state in active_states:
      [self.__add_new_state(current_state, new_state) for new_state in current_state.generate_states()]
    self.show_active_states()

 
  def work(self):
    while self._active_states:
      self.step()
    print "End"
    print "Pure Initial States:" 
    print "Pure Out States:"
    self.show_state_graph()

 
  def show_active_states(self):
    print "STEP %s"%(self._step_counter)
    print "\n".join(map(lambda ws: str(ws.block_state) + str(ws.wave_front), self._active_states))

 
  def show_state_pool(self):
    print "\n".join(map(lambda ws: str(ws.block_state) + str(ws.wave_front), self._state_pool))

 
  def show_state_graph(self):
    import subprocess
    with NamedTemporaryFile(delete = False) as f:
      filepath = self.save_state_graph(f)
      subprocess.call(["xdot", filepath], shell = False)
    os.unlink(f.name)

 
  def save_state_graph(self, file_):
    f = None
    filepath = ""
    if isinstance(file_, str) or isinstance(file_, unicode):
      filepath = file_ + ".dot"
      f = open(filepath, "w")
    else:
      filepath = file_.name
      f = file_.file
    f.write(self.to_dot())
    f.close()
    return filepath


  def to_dot(self):
    dot = "digraph %s {\n" % (self._composite.name)
    dot += "  rankdir=LR;\n"
    G = self._flow_graph
    
    for n in G.node:
      dot += """  %s [label="%s"];\n""" % (n.__id__(), n.__str__())
    
    for s in G.edge:
      for e in G.edge[s]:
        for v in G.edge[s][e]:
          dot += """  %s -> %s[label="%s"];\n""" % \
                  (s.__id__(), e.__id__(), ', '.join([edge_str(edge) for edge in (s.wave_front).difference(e.wave_front)]))

    dot += "}"
    return dot


  def __add_new_state(self, current_state, new_state):
    if not isinstance(new_state, WorkflowState):
      raise AttributeError, "Object of `WorkflowState` expected."
    g = self._flow_graph
    if not new_state in self._state_pool:
      if current_state is None:
        g.add_node(new_state)
      else:
        g.add_edge(current_state, new_state)
      self._state_pool.append(new_state)
      self._active_states.append(new_state)
    else:
      g.add_edge(current_state, new_state)

  @property
  def attracting_components(self):
    return nx.attracting.attracting_components(self._flow_graph)

class WorkflowState(object):
  def __init__(self, parent = None, composite = None):
    self._block_states = {}
    self._wave_front = set()
    self._composite = None
    self._port_history = {}
    self._locked_blocks = {}
    if parent == None and composite == None:
      raise Exception, "Workflow cannot be initialized without parent workflow instance or composite schedule"
    if parent:
      self._init_from_workflowstate(parent)
    else:
      self._init_from_composite(composite)

 
  @property
  def block_state(self):
    return self._block_states

 
  @property
  def wave_front(self):
    #return map(lambda w: {'edge' : w.edge, 'splitting' : w.splitting}, self._wave_front)
    return set([str(w) for w in self._wave_front])

 
  @property
  def port_history(self):
    return self._port_history

 
  def save(self, path):
    ws = self._colored_composte()
    return ws.save(path)

 
  def show(self):
    ws = self._colored_composte()
    ws.show()


  def generate_states(self):
    self._dst_map = self._wavefront_dst_map()
    self._src_map = self._wavefront_src_map()
    new_state = WorkflowState(parent = self)
    blocks_to_launch = set()
    for dst_block in self._dst_map:
      block_instance = self._composite.blocks[dst_block]['block_type']
      if dst_block in self._locked_blocks:
        inputs_to_check = set(self._dst_map[dst_block].keys()).intersection(self._locked_blocks[dst_block])
        if any([self._dst_map[dst_block][j].splitting.is_concurrent(self._dst_map[dst_block][k].splitting) for j,k in combinations(inputs_to_check, 2)]):
          raise Exception, "Race condition on block `%s` "%(wave.dst_block)
      else:
        required_inputs = block_instance.required_inputs(self.block_state[dst_block], self._composite.connected_ports(dst_block))
        if len(required_inputs) > 1:
          self._locked_blocks[dst_block] = required_inputs
      block_work_variants = block_instance.work(self.block_state[dst_block], set(self._dst_map[dst_block].keys()))
      if block_work_variants:
        print block_work_variants
        blocks_to_launch.add((dst_block, iset(block_work_variants)))
    for state in self._evolve_state(blocks_to_launch):
      yield state

 
  def _evolve_state(self, blocks_to_launch):
    if not blocks_to_launch:
      yield self
    else:
      dst_block, target_variants = blocks_to_launch.pop()
      for state in self._evolve_state(blocks_to_launch):
        print "block to fire : %s"%(dst_block)
        print "\twork variants : %s" % (target_variants)
        for block_work_variant in target_variants: 
          new_state = WorkflowState(parent = state)
          #block_work_variant = block_work_variants[0]
          excited_edges = []
          out_ports = block_work_variant[1]
          in_ports = block_work_variant[0]
          new_block_state = block_work_variant[2]
          if any([self._src_map.has_key(dst_block) and self._src_map[dst_block].has_key(port) for port in out_ports]):
            #yield self
            raise Exception, "Stack!"
          for o in out_ports:
            candidate_edges = self._composite.edges_from_port(dst_block, o)
            excited_edges += candidate_edges
          
          unite_spliting = None
          for i in in_ports:
            used_wave = self._dst_map[dst_block][i]
            new_state._add_port_history(dst_block, i, used_wave.splitting)
            new_state._wave_front.remove(used_wave)
            unite_spliting = used_wave.splitting if unite_spliting is None else unite_spliting + used_wave.splitting
          
          j = 0
          splitting_count = len(excited_edges) 
          for e in excited_edges:
            new_spliting = deepcopy(unite_spliting)
            new_spliting.expand(j, splitting_count)
            new_state._wave_front.add(Wave(e, new_spliting))     
            j+=1       
          new_state._block_states[dst_block] = new_block_state
          yield new_state


  def _wavefront_dst_map(self):
    wavefront_grouped = {}
    for wave in self._wave_front:
      if not wavefront_grouped.has_key(wave.dst_block):
        wavefront_grouped[wave.dst_block] = {}
      if not wavefront_grouped[wave.dst_block].has_key(wave.dst_port):
        wavefront_grouped[wave.dst_block][wave.dst_port] = wave
      else:
        raise Exception, "Race condition on block `%s` port `%s`"%(wave.dst_block, wave.dst_port)
    return wavefront_grouped


  def _add_port_history(self, block, port, wavesplit):
    if not self._port_history.has_key(block):
      self._port_history[block] = {}
    if not self._port_history[block].has_key(port):
      self._port_history[block][port] = wavesplit
    elif wavesplit.is_expanded(self._port_history[block][port]):
      self._port_history[block][port] = wavesplit
    else:
      raise Exception, "Race condition on block `%s` port `%s`"%(block, port)  
    print "ph:", self._port_history

 
  def _wavefront_src_map(self):
    wavefront_grouped = {}
    for wave in self._wave_front:
      if not wavefront_grouped.has_key(wave.src_block):
        wavefront_grouped[wave.src_block] = {}
      if not wavefront_grouped[wave.src_block].has_key(wave.src_port):
        wavefront_grouped[wave.src_block][wave.src_port] = []
      wavefront_grouped[wave.src_block][wave.src_port].append(wave)
    return wavefront_grouped  


  def _init_from_composite(self, composite_block):
    if not isinstance(composite_block, Composite):
      raise AttributeError, "compoiste_block should be of `Composite` type"

    self._composite = composite_block
    # set initial block states
    for block_name in self._composite.blocks:
      self._block_states[block_name] = Block.INITIAL

    #  set initial wavefront
    init_edges = self._composite.edges_from_block(Composite.SOURCE)
    self._wave_front = set([Wave(e) for e in init_edges])


  def _init_from_workflowstate(self, parent_state):   
    if not isinstance(parent_state, WorkflowState):
      raise AttributeError, "workflowstate should be of `WorkflowState` type"
    #self._parent = parent_state
    self._composite = parent_state._composite
    self._wave_front = deepcopy(parent_state._wave_front)
    self._block_states = deepcopy(parent_state._block_states)
    self._port_history = deepcopy(parent_state._port_history)


  def _colored_composte(self):
    ws = deepcopy(self._composite)
    G = ws._connection_graph
    for wave in self._wave_front:
      src = wave.src_block
      dst = wave.dst_block
      for v in G.edge[src][dst]:
        if ports_set(G.edge[src][dst][v]) == wave.edge[2]:
          G.edge[src][dst][v]['color'] = 'green'
    return ws


  def __id__(self):
    return "WS_" + str(abs(self.__hash__()))

 
  def __str__(self):
    block_states = dict([(k,v) for k,v in self._block_states.items() if v != Block.INITIAL])
    return str(block_states or "Initial")


  def _key(self):
    return type(self), iset(self._wave_front), iset(self._block_states.items())


  def __hash__(self):
    return hash(self._key())


  def __eq__(self,other):
    if isinstance(other, self.__class__):
      return self._key() == other._key()
    return False


  def __ne__(self,other):
    return not self.__eq__(other)




DiffPair = namedtuple('DiffPair', ['fst', 'snd'])

class WaveSplit(object):
  def __init__(self, id = 0, length = 1, init  = True):
    self._value = list([None]*length)
    self._value[id] = init
  
  def expand(self, id, length):
    if not length == 1:
      for i in range(len(self)):
        if self._value[i] in [True, False]:
          self._value[i] = WaveSplit(id, length)
        elif not self._value[i] is None:
          self._value[i].expand(id, length)
    else:
      for i in range(len(self)):
        if self._value[i] == True:
          self._value[i] = False
        elif isinstance(self._value[i], self.__class__):
          self._value[i].expand(id, length)
    return self

  def _differ(self, other):
    if not isinstance(other, self.__class__):
      raise TypeError, "Can be applied only to WaveSplit"  
    if len(self) != len(other):
      raise Exception, "Cannot be compared"
    for i in xrange(len(self)):
      if self._value[i] == other[i]:
        continue
      elif isinstance(self._value[i], (bool,type(None))) or isinstance(other[i], (bool,type(None))):
        yield DiffPair(self._value[i], other[i])
      elif isinstance(self._value[i], self.__class__) and isinstance(other[i], self.__class__):
        yield [diff for diff in self._value[i]._differ(other[i])]


  def is_concurrent(self, other):
    def concurrency_counter(diff, counter = 0):
      # if counter > 0:
      #   return counter
      if isinstance(diff, DiffPair):
        return (diff[0] == True) + (diff[1] == True)
      else:
        return reduce(lambda y,x: y + concurrency_counter(x, y), diff, counter)
    
    return concurrency_counter(self._differ(other)) != 1


  def is_expanded(self, other):
    def expanded(diff):
      if isinstance(diff, DiffPair):
        return not isinstance(diff[0], type(None))
      else:
        return all([expanded(d) for d in diff])
    return expanded(self._differ(other))  


  def __add__(self, other):
    result = deepcopy(self)
    if other is None:
      return result
    if not isinstance(other, self.__class__):
      raise TypeError, "Unsupported operator +"
    if len(self) != len(other):
      raise Exception, "Different splitings"
    result = deepcopy(self)
    for i in xrange(len(result)):
      if result[i] is None:
        result[i] = other[i]
      elif other[i] is None:
        continue
      elif not isinstance(result[i], self.__class__) or not isinstance(other[i], self.__class__):
        raise TypeError, "Unsupported operator +"
      else:
        result[i] += other[i]
    if all([isinstance(i, bool) for i in result]):
      result = WaveSplit().expand(0,1) if len(result) == 1 else False
    return result
        

  def __deepcopy__(self, memo):
    result = WaveSplit(0,1)
    result._value = deepcopy(self._value)
    return result


  def __repr__(self):
    return str(self._value)


  def  __len__(self):
    return len(self._value)


  def __getitem__(self, i):
    return self._value[i]
 

  def __setitem__(self, i, y):
    self._value[i] = y


  def _key(self):
    return type(self), self.__repr__()


  def __hash__(self):
    return hash(self._key())


  def __eq__(self,other):
    if isinstance(other, self.__class__):
      return self._key() == other._key()
    return False


  # def __ge__(self, other):
  #   if not isinstance(other, self.__class__):
  #     raise TypeError, "Can be applied only to WaveSplit" 
  #   if len(other) == 1:
  #     return True
  #   if len(ws) != len(other):
  #     return False


class Wave(object):
  # _edge =(src_block, dst_block, (src_port, dst_port))
  # _splitting = [(part_id, parts_count),...]
  def __init__(self, edge, splitting = WaveSplit(0,1)): 
    self._splitting = splitting
    self._edge = edge
 

  @property
  def edge(self):
    return self._edge
 

  @property
  def dst_block(self):
    return self._edge[1]


  @property
  def src_block(self):
    return self._edge[0]


  @property
  def dst_port(self):
    return self._edge[2][1]


  @property
  def src_port(self):
    return self._edge[2][0]


  @property
  def splitting(self):
    return self._splitting


  def __str__(self):
    return str(self._edge) + ":" + str(self._splitting)


  def _key(self):
    return type(self), self._edge


  def __hash__(self):
    return hash(self._key())


  def __eq__(self,other):
    if isinstance(other, self.__class__):
      return self._key() == other._key()
    return False


  def __ne__(self,other):
    return not self.__eq__(other)




