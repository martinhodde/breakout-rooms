import math
import random as rand
import copy
from parse import read_input_file, write_output_file
from utils import *
import sys
from os.path import basename, normpath
import os
import glob
from multiprocessing import Pool, cpu_count
import numba

def solve(G, s):
    """
    Args:
        G: networkx.Graph
        s: stress_budget
    Returns:
        D: Dictionary mapping for student to breakout room r e.g. {0:2, 1:0, 2:1, 3:2}
        k: Number of breakout rooms
    """
    return sim_annealing(G, s)

def greedy_fast(G, s):
    # listing nodes in decreasing happiness/stress order
    nodes = list(G.nodes)
    n = len(nodes)
    edges = []
    for i in range(n):
        for j in range(i):
            h, s =  G.edges[i, j]['happiness'], G.edges[i, j]['stress']
            val = float('inf') if s == 0 else h / s
            edges.append((i, j, val, s, h))
    edges.sort(reverse = True, key = lambda t: t[2])

    k = 20
    D = {}
    rooms = []
    stress = []
    stress_budget = s / k

    def new_room(i,j):
        nonlocal k
        k += 1
        D[i] = k
        D[j] = k
        rooms[k] = [i,j]
        stress[k] = G.edges[i,j]['stress']

    def add_room(i, j):
        room_number = D[i]
        potential_stress = stress[room_number] + stress_from_adding(j, rooms[room_number])
        if potential_stress < stress_budget:
            rooms[room_number].append(j)
            D[j] = room_number
            stress[room_number] = potential_stress

    def stress_from_adding(i, others):
        tot = 0.0
        for j in others:
            tot += G.edges[i, j]['stress']
        return tot

    for edge in edges:
        i = edge[0]
        j = edge[1]
        currKeys = D.keys()
        if i in currKeys or j in currKeys:
            pass
        else:
            new_room(i,j)

    while edges:
        top = edges.pop(0)
        i, j = top[0], top[1]
        if i in D and j in D:
            continue
        elif i in D and j not in D:
            add_room(i, j)
        elif j in D and i not in D:
            add_room(j,i)
        elif i not in D and j not in D:
            new_room(i, j)

@numba.jit
def add_to_room(room_number, person, D, room_assignments):
    from_room = D[person]
    if from_room == room_number:
        return False, None, None
    new_D = D.copy()
    new_rooms = copy.deepcopy(room_assignments)

    old_room = new_rooms[from_room]
    old_room.remove(person)
    if not old_room:
        new_rooms.remove(old_room)
        for person in new_D:
            if new_D[person] > from_room:
                new_D[person] -= 1
        if room_number > from_room:
            room_number -= 1
    new_rooms[room_number].append(person)
    new_D[person] = room_number
    return True, new_D, new_rooms

@numba.jit
def sim_annealing(G, s):
    
    nodes = list(G.nodes)
    n = len(nodes)
    D = {student : student for student in range(n)}
    room_assignments = [[node] for node in nodes]

    def E(G, rooms):
        stress, happiness = 0, 0
        for room in rooms:
            happiness += calculate_happiness_for_room(room, G)
            stress += calculate_stress_for_room(room, G)
        if happiness == 0:
            return math.inf
        else:
            return stress / happiness

    def delta_E(G, rooms_curr, rooms_new):
        return E(G, rooms_new) - E(G, rooms_curr)

    def P(G, rooms_curr, rooms_new, temp):
        return 1 / (1 +  math.exp(-delta_E(G, rooms_curr, rooms_new) / temp))

    def temperature(t):
        return 1 / t

    min_temp, t = 0.04, 0.02

    while temperature(t) > min_temp or not is_valid_solution(D, G, s, len(room_assignments)):
        if temperature(t) < 0.005:
            return D, len(room_assignments)
        while True:
            num_rooms = len(room_assignments)
            rand_from_room_number = rand.randint(0, num_rooms - 1)
            rand_from_room = room_assignments[rand_from_room_number]
            rand_student = rand.choice(rand_from_room)

            rand_to_room_number = rand.randint(0, num_rooms-1)

            success, new_D, new_rooms = add_to_room(rand_to_room_number, rand_student, D, room_assignments)
            if success:
                break
        delta = delta_E(G, room_assignments, new_rooms)
        if delta < 0:
            room_assignments = new_rooms
            D = new_D
        else:
            v = rand.uniform(0,1)
            temp = temperature(t)
            if P(G, room_assignments, new_rooms, temp) > v:
                room_assignments = new_rooms
                D = new_D
        t += 0.02
        
    k = len(room_assignments)
    return D, k

def evaluate(input_path):
    output_path = 'outputs/' + basename(normpath(input_path))[:-3] + '.out'
    G, s = read_input_file(input_path)
    D, k = solve(G, s)
    assert is_valid_solution(D, G, s, k)
    print("solved ", input_path)
    if not os.path.exists(output_path):
        write_output_file(D, output_path)
        os.rename(input_path, 'used_inputs/' + basename(normpath(input_path)))

if __name__ == '__main__':
    inputs = glob.glob('inputs/large-*')
    while inputs:
        p = Pool(cpu_count())
        p.imap_unordered(evaluate, inputs)
        p.close()
        p.join()
        inputs = glob.glob('inputs/large-*')

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
