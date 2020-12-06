import networkx as nx
import numpy as np
from parse import read_input_file, write_output_file
from utils import is_valid_solution, calculate_happiness
import sys
from os.path import basename, normpath
import glob
from multiprocessing import Pool, cpu_count
import glob

def solve(G, s):
    """
    Args:
        G: networkx.Graph
        s: stress_budget
    Returns:
        D: Dictionary mapping for student to breakout room r e.g. {0:2, 1:0, 2:1, 3:2}
        k: Number of breakout rooms
    """

    #sort values in descending happiness/stress order
    #happiness = G.edges[i, j]['happiness']
    #stress = G.edges[i, j]['stress']
    nodes = list(G.nodes)
    n = len(nodes)
    edges = []
    for i in range(n):
        for j in range(i):
            h, s =  G.edges[i, j]['happiness'], G.edges[i, j]['stress']
            val = float('inf') if s == 0 else h / s
            edges.append((i, j, val))
    edges.sort(reverse = True, key = lambda t: t[2])

    k = 0
    D = {}
    rooms = {}
    stress = {}

    def new_room(i,j):
        nonlocal k
        k += 1
        D[i] = k
        D[j] = k
        rooms[k] = [i,j]
        stress[k] = G.edges[i,j]['stress']
    
    def add_to_room(i, j):
        room_number = D[i]
        potential_stress = stress[room_number] + stress_from_adding(j, rooms[room_number])
        if potential_stress < s:
            rooms[room_number].append(j)
            D[j] = room_number
            stress[room_number] = potential_stress
    
    def stress_from_adding(i, others):
        tot = 0
        for j in others:
            tot += G[i,j]['stress']
        return stress

    while edges:
        top = edges.pop(0)
        i, j = top[0], top[1]
        if i in D and j in D:
            continue
        elif i in D and j not in D:
            add_to_room(i, j) 
        elif j in D and i not in D:
            add_to_room(j,i)
        elif i not in D and j not in D:
            new_room(i, j)

    return D,k

def evaluate(input_path):
    output_path = 'outputs/' + basename(normpath(input_path))[:-3] + '.out'
    G, s = read_input_file(input_path)
    D, k = solve(G, s)
    assert is_valid_solution(D, G, s, k)
    happiness = calculate_happiness(D, G)
    write_output_file(D, output_path)


if __name__ == '__main__':
    p = Pool(cpu_count())
    inputs = glob.glob('inputs/small-*')
    p.map(evaluate, inputs)
    p.close()
    p.join()

# Here's an example of how to run your solver.

# Usage: python3 solver.py test.in

# if __name__ == '__main__':
#     assert len(sys.argv) == 2
#     path = sys.argv[1]
#     G, s = read_input_file(path)
#     D, k = solve(G, s)
#     assert is_valid_solution(D, G, s, k)
#     print("Total Happiness: {}".format(calculate_happiness(D, G)))
#     write_output_file(D, 'outputs/small-1.out')


# For testing a folder of inputs to create a folder of outputs, you can use glob (need to import it)