#!/usr/bin/python
# encoding: utf-8
# Copyright (C) Datadvance, 2013


from composite import Composite
import fa
import connection


from copy import copy
from utils import ports_set, edge_str
from utils import RaceCondition, SurplusWave
from utils import WorkVariant

import networkx as nx
from copy import deepcopy
from sets import ImmutableSet as iset
from tempfile import NamedTemporaryFile
import os

from numpy import matrix
import uuid

from collections import namedtuple
from compiler.ast import flatten
def getID(name = None):
  getID.names_count.setdefault(name, -1)
  getID.names_count[name]+=1 
  return "%s%s"%(name,"_" + str(getID.names_count[name]) + "_"  if getID.names_count[name] !=0 else "")

getID.names_count = {}

class Workflow(object):
  def __init__(self, composite):
    self._composite = composite
    self.init_composite()
    self._place_map = {}
 

  def work(self, state=None, inputs=None):
    self.init_composite(state, inputs)
    while self._active_states:
      self._step()
    self.petrify()
    # return self._final_states()


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
      subprocess.Popen(["xdot", filepath], shell = False)
      print f.name
    # os.unlink(f.name)

  def show_petri_net(self):
    import subprocess
    with NamedTemporaryFile(delete = False) as f:
      filepath = self.save_petri_net(f)
      print filepath
      subprocess.Popen(["xdot", filepath], shell = False)

    #os.unlink(f.name)

  def show_task_graph(self):
    import subprocess
    with NamedTemporaryFile(delete = False) as f:
      filepath = self.save_task_graph(f)
      print filepath
      subprocess.Popen(["xdot", filepath], shell = False)


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

  def save_petri_net(self, file_):
    f = None
    filepath = ""
    if isinstance(file_, str) or isinstance(file_, unicode):
      filepath = file_ + ".dot"
      f = open(filepath, "w")
    else:
      filepath = file_.name
      f = file_.file
    f.write(self._petri_to_dot())
    f.close()
    return filepath  

  def save_task_graph(self, file_):
    f = None
    filepath = ""
    if isinstance(file_, str) or isinstance(file_, unicode):
      filepath = file_ + ".dot"
      f = open(filepath, "w")
    else:
      filepath = file_.name
      f = file_.file
    f.write(self._task_to_dot(self._create_task_graph()))
    f.close()
    return filepath 


  def to_dot(self):
    dot = "digraph %s {\n" % (self._composite.name)
    dot += "  rankdir=LR;\n"
    G = self._flow_graph
    
    for n in G.node:
      if isinstance(n , WorkflowState):
        dot += """  %s [label="%s"];\n""" % (n.__id__(), n.__str__())
    
    for s in G.edge:
      for e in G.edge[s]:
          base_edge = G.edge[s][e].get("base", None)
          if base_edge:
            dot += """  %s -> %s[label="%s"];\n""" % \
                    (s.__id__(), e.__id__(), "%s %s" % (",".join(["%s_%s" %(t,st) for t, st in base_edge['running_tasks']]), base_edge['p']))

    dot += "}"
    return dot



  def petrify(self):
    G = self._flow_graph
    pn = self._petri_net
    initial_state = self._state_pool[0]
    initial_flow = tuple(list(initial_state.wave_front)[0][:2])
    self._make_place(initial_state, initial_flow, name = "i")

    final_states = nx.attracting.attracting_components(self._flow_graph)
    print final_states
    if len(final_states) == 1:
      final_state = final_states[0][0]
      self._get_place(final_state, (), name = "o")
    else:
      outplace = uuid.uuid1()
      for s in final_states:
        final_state = s[0]
        zero_task_name = getID("zero_task")
        pn.add_node(zero_task_name, type = "task")
        for place_id in self._get_place(outplace, (), name = "o"):
          pn.add_edge(zero_task_name, place_id,  p = 1.)
        for place_id in self._make_place(final_state, ()):
          pn.add_edge(place_id, zero_task_name,  p = 1.) 

    for s in G.edge:
      for e in G.edge[s]:
          if G.edge[s][e].get("base", None):
            self._edge_to_task(s, e)


  def _petri_to_dot(self):
    dot = "digraph %s {\n" % (self._composite.name)
    dot += "  rankdir=LR;\n"
    pn = self._petri_net
    
    for n in pn.node:
      dot += """  %s [label="%s", shape= %s];\n""" % (n, n, "rectangle" if pn.node[n]['type'] == "task" else "circle")

    for s in pn.edge:
      for e in pn.edge[s]:
            dot += """  %s -> %s;\n""" % (s, e)

    dot += "}"
    return dot


 
  def _task_to_dot(self, graph=None):
    dot = "digraph %s {\n" % (self._composite.name)
    dot += "  rankdir=LR;\n"
    pn = graph if not graph is None else self._petri_net
    
    for n in pn.node:
      dot += """  %s [label="%s_%s_", shape="rectangle"];\n""" % (n,n, round(pn.node[n].get('k', 1.), 2))

    for s in pn.edge:
      for e in pn.edge[s]:
            dot += """  %s -> %s;\n""" % (s, e)

    dot += "}"
    return dot 



  def _create_task_graph(self):
    tg = self._petri_net.copy()
    for n in tg.nodes():
      if tg.node[n]['type'] == 'place':
        for (i,o) in zip(tg.predecessors(n), tg.successors(n)):
          tg.add_edge(i,o)
        tg.remove_node(n)
    return tg 

  def _step(self):
    self._step_counter += 1
    active_states = set(self._active_states)
    self._active_states = []
    for current_state in active_states:
      [self._add_new_state(current_state, new_state, probability) for new_state, probability in current_state.generate_states()]

  def _add_new_state(self, current_state, new_state, probability = 1.):
    print "_add_new_state(%s, %s, %s)"% (current_state, new_state, probability)
    if not isinstance(new_state, WorkflowState):
      raise AttributeError, "Object of `WorkflowState` expected."
    g = self._flow_graph
    if not new_state in self._state_pool:
      if current_state is None:
        g.add_node(new_state)
      else:
        self._add_edge(current_state, new_state, probability)
      self._state_pool.append(new_state)
      self._active_states.append(new_state)
    elif current_state != new_state:
      self._add_edge(current_state, new_state, probability)

  def _add_edge(self, current_state, new_state, probability):
    g = self._flow_graph
    tasks = set([(edge[1], current_state.block_state[edge[1]]) for edge in (current_state.wave_front).difference(new_state.wave_front)])
    g.add_edge(current_state, new_state, key = "base",  p = probability, running_tasks = tasks)

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
          result.add(WorkVariant(iset(self._source_ports), iset(outputs), str(node.block_state), 1.))
    return result

  def _make_place(self, node, flow, name=None):
    pn = self._petri_net
    places = []
    for place_id in self._place_map.get(node, []):
      if flow == pn.node[place_id].get("flow", None):
        places.append(place_id)
    if places:
      return places
    else:
      place_id = name if name else getID("place")
      self._place_map.setdefault(node, []).append(place_id)
      pn.add_node(place_id, {"type" : "place", "state" : node, "flow" : flow })
      return [place_id]



  def _get_place(self, node, flow, name=None):
    pn = self._petri_net
    places = []
    for place_id in self._place_map.get(node, []):
      if flow == pn.node[place_id].get("flow", ()):
        places.append(place_id)
    if places:
      return places
    else:
      place_id = name if name else getID("place")
      self._place_map.setdefault(node, []).append(place_id)
      pn.add_node(place_id, {"type" : "place", "state" : node, "flow" : flow})
      return [place_id]


  def _edge_to_task(self, src_node, dst_node):
    pn = self._petri_net
    G = self._flow_graph
    tasks = G[src_node][dst_node]["base"]['running_tasks']
    edge_probabylity = G.edge[src_node][dst_node]['base']['p']
    for task in tasks:
      unique_task_name = getID("_".join(task))
      pn.add_node(unique_task_name, type = "task")

      for edge in (src_node.wave_front).intersection(dst_node.wave_front):
        if edge[0] != task[0]:
          zero_task_name = getID("zero_task")
          pn.add_node(zero_task_name, type = "task")
          for place_id in self._get_place(dst_node, tuple(edge[:2])):
            pn.add_edge(zero_task_name, place_id,  p = 1.)
          for place_id in self._make_place(src_node, tuple(edge[:2])):
            pn.add_edge(place_id, zero_task_name,  p = edge_probabylity)         

      for edge in (src_node.wave_front).difference(dst_node.wave_front):
        if edge[1] == task[0]:
          for place_id in self._make_place(src_node, tuple(edge[:2])):
            pn.add_edge(place_id, unique_task_name,  p = edge_probabylity)

      for edge in (dst_node.wave_front).difference(src_node.wave_front):
        if edge[0] == task[0]:
          for place_id in self._get_place(dst_node, tuple(edge[:2])):
            pn.add_edge(unique_task_name, place_id,  p = 1.)

      
      if not dst_node.wave_front:
        for place_id in self._get_place(dst_node, ()):
          pn.add_edge(unique_task_name, place_id)

  def decycle(self):
    while(nx.simple_cycles(self._petri_net)):
      self._decycle()

  def _decycle(self):
    pn = self._petri_net
    cycle = nx.simple_cycles(self._petri_net)[0]

    exits = {}
    for i in cycle:
      for j in pn.edge[i]:
        if not j in cycle:
          exits.setdefault(j, set()).add(i)

    print exits
    cycle2 = copy(cycle)[:-1] + exits.keys()

    m = []
    for i in cycle2:
      m.append([pn.edge[i].get(j, {}).get('p', 0.) for j  in cycle2])
    m = matrix(m)
    
    result = reduce(lambda y, i: y + m**i , range(2,200), m)
    shortest_paths = nx.single_source_shortest_path_length(self._petri_net, 'i')
    shortest_paths = filter(lambda (k,v): k in cycle2, shortest_paths.iteritems())
    shortest_paths = sorted([(j,i) for (i,j) in iter(shortest_paths)])
    nearest_node = shortest_paths[0][1]
    predessor = nx.subgraph(self._petri_net, cycle2).predecessors(nearest_node)[0]
    result_v = result.base[cycle2.index(nearest_node)]
    result_m = dict([(cycle2[i], result_v[i]) for i in range(len(cycle2))])
    result =  sorted(zip(cycle2, result.base[cycle2.index(nearest_node)]))


    loop_exit = getID("place")
    pn.add_node(loop_exit, {"type" : "place", "state" : None, "flow" : None})
    pn.remove_edge(predessor, nearest_node)
    pn.add_edge(predessor, loop_exit)
    for (t, preds) in exits.iteritems():
      for p in preds:
        pn.remove_edge(p, t)
      pn.add_edge(loop_exit, t, p = result_m[t])
    for n in cycle:
      for i in pn.successors(n):
        pn.edge[n][i]['p'] = 1.
      pn.node[n]['k'] = pn.node[n].setdefault('k', 1.) * result_m[n] 

    return result

  def fork_groups(self):
    for p in nx.all_simple_paths(w._petri_net, 'i', 'place_6_'):
      pass


  def _merge_branches(self, source, target):
    base = []
    pn = self._petri_net
    allpathes = [p for p in nx.all_simple_paths(self._petri_net, source, target)]
    for p in allpathes:
      print p
      head = None
      if not base:
        base +=[source]
        head = source
      else:
        connection_place = getID("place")
        pn.add_node(connection_place, {"type" : "place", "state" : None, "flow" : None})
        head = connection_place

      partition = p[1:-1]
      k = pn.edge[source][partition[0]]['p']
      for n in partition:
        if pn.node[n]['type'] == 'task':
          pn.node[n]['k'] = pn.node[n].setdefault('k', 1.)* k

      pn.remove_edge(source, partition[0])
      pn.remove_edge(partition[-1], target)
      if head != base[-1]:
        pn.add_edge(base[-1], head, p = 1)
      pn.add_edge(head, partition[0], p =1)
      base += partition

    pn.add_edge(base[-1], target, p = 1)



  def _clear(self):
    self._source_ports = []
    self._state_pool = []
    self._active_states = []
    self._step_counter = 0
    self._flow_graph = nx.MultiDiGraph()
    self._petri_net = nx.DiGraph()
    getID.names_count = {}

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
    print self._dst_map, "\n#####"
    # print self.block_state
    self._src_map = self._wavefront_src_map()
    blocks_to_launch = set()
    for dst_block in self._dst_map:
      block_work_variants = self._block_work(dst_block, self.block_state[dst_block], set(self._dst_map[dst_block].keys()))
      if block_work_variants:
        blocks_to_launch.add((dst_block, iset(block_work_variants)))
    for state, probability in self._evolve_state(blocks_to_launch):
      yield state, probability

  def _block_work(self, block, state , inputs): 
    return self._composite.blocks[block].work(state, inputs)
 
  def _evolve_state(self, blocks_to_launch):
    if not blocks_to_launch:
      yield (self, 1.0)
    else:
      dst_block, target_variants = blocks_to_launch.pop()
      for state, prob in self._evolve_state(blocks_to_launch):
        for block_work_variant in target_variants: 
          print "@block_work_variant\n", block_work_variant, "\n"
          new_state = deepcopy(state)
          excited_edges = []
          out_ports = block_work_variant.outputs
          in_ports = block_work_variant.inputs
          new_block_state = block_work_variant.state
          probability = block_work_variant.probability * prob
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
          yield (new_state, probability)


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




