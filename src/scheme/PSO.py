from numpy import array
from random import random
from math import *
from copy import copy
import networkx as nx

iter_max = 100
pop_size = 30
dimensions = 0
nodes = 5
c1 = 2
c2 = 5
err_crit = 0.00001

one_process_time = 0.
F = 50

class Particle:
    pass

gbest = Particle()
working_blocks = []

Transition = {
  0: [1],
  1: [2,3 ,7,8,9],
  2: [4],
  3: [6],
  4: [5]
}

Task_graph = nx.DiGraph()


Times = {
  'Map': 100,
  'F': 500,
  'Map2': 200,
  None : 0,
  'stock':0,
  'Tube': 0

}



def defuzz(x):
  x = x * nodes
  d, u  = floor(x), ceil(x) - 1
  node =  int(d) if (u+d)/2 > x else int(u)
  if node < 0 :
    return 0
  elif node > nodes - 1:
    return nodes - 1
  else:
    return node


def time_calc(proc_destrib):
  timeTable = {}
  for n in range(nodes):
    timeTable[n] = [(0,0)]
  
  first_task_item = [n for n,d in Task_graph.in_degree().items() if d==0][0]
  queue = [(first_task_item, 0.)]
  while(len(queue)):
   # print "Queue:",queue
   # print "TimeTable",timeTable
    new_queue = []
    for task_item, start_time in queue:
      print task_item, start_time
      task = Task_graph.node[task_item]['block_name']
      task_type = Task_graph.node[task_item]['block_type']
      # try:     
      node = proc_destrib[task]
      start_time = max(timeTable[node][-1][1], start_time)
      finish_time = start_time + Times[task_type]*Task_graph.node[task_item].get('k', 1.)
      timeTable[node] += [(start_time, finish_time)]
      next = Task_graph.successors(task_item)
      new_queue += zip(next, [finish_time]*len(next))
      # except:
      #   print "Task: %s, node:%s"%(task, proc_destrib[task])
      #   raise
    queue = new_queue
 # print [node_table[-1][1] for node_table in timeTable.values()]
  return max([node_table[-1][1] for node_table in timeTable.values()])



def f6(param, w1,w2):
    '''Schaffer's F6 function'''
    task_destrib = dict(zip(working_blocks, [defuzz(x) for x in param]))
    makespan = time_calc(task_destrib)
    f6 = (one_process_time - makespan)/one_process_time  + 0.5*one_process_time/makespan/len(set(task_destrib.values()))
    # f6 = 1.* processtime/makespan
    errorf6 = 600 - f6
    print task_destrib, f6
    return f6, errorf6;


def crisp_nodes(fuzzy):
  return [defuzz(x) for x in fuzzy]


def count(l):
  return len(set(l))

def calc(task_graph):
  #initialize the particles
  global Task_graph
  global dimensions
  global working_blocks
  global one_process_time
  Task_graph = task_graph
  working_blocks = list(set([Task_graph.node[t]['block_name'] for t in Task_graph.nodes()]))
  dimensions = len(working_blocks)
  one_process_time = time_calc(dict(zip(working_blocks, [0]*dimensions)))
  particles = []
  for i in range(pop_size):
      p = Particle()
      p.params = array([random() for i in range(dimensions)])
      p.best = p.params
      p.fitness = 0.0
      p.v = array([0.0 for i in range(dimensions)])
      particles.append(p)

  # let the first particle be the global best
  global gbest
  gbest = particles[0]
  err = 999999999
  while i < iter_max :
      global gbest
      w1 = abs(sin(2*pi*i/F))
      for p in particles:
          fitness,err = f6(p.params, w1, 1. - w1)
          if fitness > p.fitness:
              p.fitness = fitness
              p.best = p.params

          if fitness > gbest.fitness:
              gbest.fitness = p.fitness
              gbest.params = copy(p.params)

          if fitness == gbest.fitness:
            para = [defuzz(x) for x in p.params]
            if count(crisp_nodes(gbest.params)) > count(crisp_nodes(p.params)):
              gbest.params = copy(p.params)
            print fitness,count(para), para,"#", count(crisp_nodes(gbest.params))
          p.v = 0.1 * p.v + c1 * random() * (p.best - p.params) \
                  + c2 * random() * (gbest.params - p.params)
          p.params += p.v

      i  += 1
      if err < err_crit:
          break
      #progress bar. '.' = 10%
      if i % (iter_max/10) == 0:
          print '.'

  print '\nParticle Swarm Optimisation\n'
  print 'PARAMETERS\n','-'*9
  print 'Population size : ', pop_size
  print 'Dimensions      : ', dimensions
  print 'Error Criterion : ', err_crit
  print 'c1              : ', c1
  print 'c2              : ', c2
  print 'function        :  f6'

  print 'RESULTS\n', '-'*7
  print 'gbest fitness   : ', gbest.fitness
  print 'gbest params    : ', count(crisp_nodes(gbest.params)), zip(working_blocks,  crisp_nodes(gbest.params))
  print 'iterations      : ', i+1
  ## Uncomment to print particles
  #for p in particles:
   # print 'params: %s, fitness: %s, best: %s' % (p.params, p.fitness, p.best)


if __name__ == '__main__':
    main()

