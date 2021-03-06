#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013



# from composite import Composite

from composite import Composite
import fa
import connection

from utils import ports_set, edge_str
from utils import RaceCondition, SurplusWave
from utils import WorkVariant

import networkx as nx
from copy import deepcopy
from sets import ImmutableSet as iset
from tempfile import NamedTemporaryFile
import os
from collections import namedtuple

class Workflow(object):
  def __init__(self, composite):
    self._composite = composite
    self._clear()
 

  def work(self, state=None, inputs=None):
    self.init_composite(state, inputs)
    while self._active_states:
      self._step()
    return self._final_states()


  def init_composite(self, state=None, inputs=None):
    self._clear()
    self._source_ports = inputs or self._composite.inputs
    self._add_new_state(None, WorkflowState(self._composite, inputs, state))
    # self.show_active_states(3)


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


  def _step(self):
    self._step_counter += 1
    active_states = set(self._active_states)
    self._active_states = []
    for current_state in active_states:
      [self._add_new_state(current_state, new_state) for new_state in current_state.generate_states()]
    # self.show_active_states()


  def _add_new_state(self, current_state, new_state):
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
    elif current_state != new_state:
      g.add_edge(current_state, new_state)


  def _checked_final_states(self):
    if self._active_states:
      raise Exception, "Nonfinal step! There are some active states"
    final_states = nx.attracting.attracting_components(self._flow_graph)
    for final_subgroup in final_states:
      for node in final_subgroup:
        for wave in node.wave_front_rich:
          if wave.dst_block != connection.STOCK:
            raise SurplusWave, "Filthy wave `%s`!"%(wave)

  def _final_states(self):
    self._checked_final_states()
    final_states = nx.attracting.attracting_components(self._flow_graph)
    result = set()
    for final_subgroup in final_states:
      for node in final_subgroup:
          outputs = [w.dst_port for w in node.wave_front_rich]
          result.add(WorkVariant(iset(self._source_ports), iset(outputs), str(node.block_state)))
    return result

  def _clear(self):
    self._source_ports = []
    self._state_pool = []
    self._active_states = []
    self._step_counter = 0
    self._flow_graph = nx.MultiDiGraph()


WaveHistory = namedtuple('WaveHistory', ['state', 'split'])

class WorkflowState(object):
  def __init__(self, composite = None, initial_inputs = None, block_states = None):
    self._block_states = {}
    self._wave_front = set()
    self._composite = None
    self._block_history = {}
    if composite:
      self._init_from_composite(composite, initial_inputs, block_states)


 
  @property
  def block_state(self):
    return self._block_states

 
  @property
  def wave_front(self):
    #return map(lambda w: {'edge' : w.edge, 'splitting' : w.splitting}, self._wave_front)
    return set([w.edge for w in self._wave_front])

  @property 
  def wave_front_rich(self):
    return self._wave_front
 
  @property
  def port_history(self):
    return self._block_history

 
  def save(self, path):
    ws = self._colored_composte()
    return ws.save(path)

 
  def show(self):
    ws = self._colored_composte()
    ws.show()


  def generate_states(self):
    self._dst_map = self._wavefront_dst_map()
    print self._dst_map, "\n#####\n"
    print self.block_state
    self._src_map = self._wavefront_src_map()
    blocks_to_launch = set()
    for dst_block in self._dst_map:
      block_work_variants = self._block_work(dst_block, self.block_state[dst_block], set(self._dst_map[dst_block].keys()))
      if block_work_variants:
        blocks_to_launch.add((dst_block, iset(block_work_variants)))
    for state in self._evolve_state(blocks_to_launch):
      yield state

  def _block_work(self, block, state , inputs): 
    return self._composite.blocks[block].work(state, inputs)
 
  def _evolve_state(self, blocks_to_launch):
    if not blocks_to_launch:
      yield self
    else:
      dst_block, target_variants = blocks_to_launch.pop()
      for state in self._evolve_state(blocks_to_launch):
        for block_work_variant in target_variants: 
          new_state = deepcopy(state)
          excited_edges = []
          out_ports = block_work_variant.outputs
          in_ports = block_work_variant.inputs
          new_block_state = block_work_variant.state
          if any([self._src_map.has_key(dst_block) and self._src_map[dst_block].has_key(port) for port in out_ports]):
            #yield self
            raise Exception, "Stack!"
          for o in out_ports:
            candidate_edges = self._composite.edges_from_port(dst_block, o)
            excited_edges += candidate_edges
          
          united_spliting = BaseWaveSplit(init = None)
          for i in in_ports:
            used_wave = self._dst_map[dst_block][i]
            new_state._wave_front.remove(used_wave)
            unite_spliting = united_spliting + used_wave.splitting

          # fill history
          for i in in_ports:
            new_state._add_block_history(dst_block, i, self.block_state[dst_block], unite_spliting)       

          splitting_count = len(excited_edges) 
          unite_spliting.after = self._split_history(dst_block)
          j = 0
          for e in excited_edges:
            new_spliting = deepcopy(united_spliting)
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
        raise RaceCondition, "Race condition on block `%s` port `%s`"%(wave.dst_block, wave.dst_port)
    return wavefront_grouped


  def _add_block_history(self, block, port, state, split):
    if not self._block_history.has_key(block):
      self._block_history[block] = {}
    if not self._block_history[block].has_key(port):
      self._block_history[block][port] = WaveHistory(state, split)
      return
    pre_state = self._block_history[block][port].state
    pre_split = self._block_history[block][port].split
    if not split.is_expanded_from(pre_split):
      raise RaceCondition, "Race condition on block `%s` port `%s`"%(block, port)
    if self._block_work(block, pre_state, set(port)) and not pre_split.is_ahead(split):
      raise RaceCondition, "Race condition on block `%s` state `%s` "%(block, pre_state) 
    else:
      self._block_history[block][port] = WaveHistory(state, split) 

  def _split_history(self, block):
    result = BaseWaveSplit(init = None)
    for wh in self._block_history.get(block, {}).values():
      result += wh.split
    return result if not result.is_basic() else None
 
  def _wavefront_src_map(self):
    wavefront_grouped = {}
    for wave in self._wave_front:
      if not wavefront_grouped.has_key(wave.src_block):
        wavefront_grouped[wave.src_block] = {}
      if not wavefront_grouped[wave.src_block].has_key(wave.src_port):
        wavefront_grouped[wave.src_block][wave.src_port] = []
      wavefront_grouped[wave.src_block][wave.src_port].append(wave)
    return wavefront_grouped  


  def _init_from_composite(self, composite_block, initial_inputs = None, block_states = None):
    if not isinstance(composite_block, Composite):
      raise AttributeError, "compoiste_block should be of `Composite` type"

    self._composite = composite_block
    # set initial block states
    self._block_states = eval(self._composite.initial_state)
    if block_states:
      block_states = eval(block_states)
      if set(block_states.keys()).difference(set(self._composite.blocks)):
        raise Exception, "Uknown blocks!"
      self._block_states.update(block_states)

    #  set initial wavefront
    init_esges = []
    if initial_inputs:
      if initial_inputs.difference(self._composite.connected_outputs(connection.SOURCE)):
        raise Exception, "Unknown sorce inputs %s" % initial_inputs.difference(self._composite.connected_outputs(connection.SOURCE))
      init_edges = reduce(lambda x,y: x.union(self._composite.edges_from_port(connection.SOURCE, y)), initial_inputs, set())
    else:
      init_edges = set(self._composite.edges_from_block(connection.SOURCE))
    self._wave_front = set([Wave(e) for e in init_edges])


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


  def __deepcopy__(self, mem):
    result =  WorkflowState()
    result._composite = self._composite
    result._wave_front = deepcopy(self._wave_front)
    result._block_states = deepcopy(self._block_states)
    result._block_history = deepcopy(self._block_history)
    return result


  def __id__(self):
    return "WS_" + str(abs(self.__hash__()))

 
  def __str__(self):
    block_states = dict([(k,v) for k,v in self._block_states.items() if v != fa.INITIAL])
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


  def expand(self, id = 0, length = 1):
    if not length == 1:
      for i in range(len(self)):
        if isinstance(self._value[i], bool):
          self._value[i] = WaveSplit(id, length)
        elif not self._value[i] is None:
          self._value[i].expand(id, length)
    else:
      self._spoil()
    return self


  def is_expanded_from(self, other):
    def expanded(diff):
      if isinstance(diff, DiffPair):
        return not diff.fst is None
      else:
        return all([expanded(d) for d in diff if d])
    return expanded(self._differ(other))  


  def is_ahead(self, other):
    if self.is_basic():
      return True
    def is_advanced(diff, no_race):
      if isinstance(diff, DiffPair):
        return diff.fst == True or (diff.snd != True) and None
      else:
        mp = [is_advanced(d, no_race) for d in diff if d]
        mp = filter(lambda a: not a is None, mp)
        return any(mp) and (all(mp) or no_race)
   
    return not other._followed_by(self) and is_advanced(self._differ(other), self._followed_by(other))

  def _followed_by(self, other):
    return False

  def _spoil(self):
    for i in range(len(self)):
      if self._value[i] == True:
        self._value[i] = False
      elif isinstance(self._value[i], WaveSplit):
        self._value[i]._spoil()
    return self


  def _differ(self, other):
    if not isinstance(other, WaveSplit):
      raise TypeError, "Can be applied only to WaveSplit"  
    if len(self) != len(other):
      raise Exception, "Cannot be compared"
    for i in xrange(len(self)):
      if self._value[i] == other[i]:
        yield None
      elif isinstance(self._value[i], (bool,type(None))) or isinstance(other[i], (bool,type(None))):
        yield DiffPair(self._value[i], other[i])
      elif isinstance(self._value[i], WaveSplit) and isinstance(other[i], WaveSplit):
        yield [diff for diff in self._value[i]._differ(other[i])]


  def __add__(self, other):
    result = deepcopy(self)
    if other is None:
      return result
    if not isinstance(other, WaveSplit):
      raise TypeError, "Unsupported operator +"
    if len(self) != len(other):
      raise Exception, "Different splitings"
    result = deepcopy(self)
    for i in xrange(len(result)):
      if result[i] is None:
        result[i] = other[i]
      elif other[i] is None:
        continue
      else:
        result[i] = result[i] if isinstance(result[i], bool) else other[i] if isinstance(other[i], bool) else result[i] + other[i]
    if all([isinstance(i, bool) for i in result]):
      if len(result) == 1:
        result.__init__(init = False)
      else:
        result = False
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


  def __eq__(self, other):
    if isinstance(other, WaveSplit):
      return self._key() == other._key()
    return False

  def __ne__(self, other):
    return not self.__eq__(other)


class BaseWaveSplit(WaveSplit):
  _after = None

  @property
  def after(self):
    return self._after


  @after.setter
  def after(self, value):
    if not isinstance(value, (self.__class__, type(None))):
      raise TypeError, "Can be applied only to BaseWaveSplit"
    self._after = value

  def __add__(self, other):
    result = super(BaseWaveSplit, self).__add__(other)
    result.after = other.after if not result.after else result.after + other.after if other.after else result.after
    return result


  def _followed_by(self, other):
    return self.after != other.after and other.after and other.after.is_expanded_from(self)


  def is_basic(self):
    return isinstance(self._value[0], (bool, type(None)))


class Wave(object):
  # _edge =(src_block, dst_block, (src_port, dst_port))
  # _splitting = [(part_id, parts_count),...]
  def __init__(self, edge, splitting = BaseWaveSplit(0,1)): 
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




