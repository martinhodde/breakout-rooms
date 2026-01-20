"""
Simulated Annealing algorithm for breakout room assignment.
"""

import math
import random as rand
import copy
from utils import (
    is_valid_solution,
    calculate_happiness,
    calculate_stress_for_room,
)


def simulated_annealing(G, s):
    nodes = list(G.nodes)
    n = len(nodes)

    def get_rooms_from_D(D):
        rooms = {}
        for student, room in D.items():
            rooms.setdefault(room, []).append(student)
        return [rooms[room_id] for room_id in sorted(rooms.keys())]

    def renumber_D(D):
        """Renumber rooms to be contiguous starting from 0"""
        room_map = {}
        next_room = 0
        new_D = {}
        for student in sorted(D.keys()):
            room = D[student]
            if room not in room_map:
                room_map[room] = next_room
                next_room += 1
            new_D[student] = room_map[room]
        return new_D

    def evaluate_solution(D):
        rooms = get_rooms_from_D(D)
        k = len(rooms)
        valid = is_valid_solution(D, G, s, k)
        happiness = calculate_happiness(D, G) if valid else -1000
        return happiness, valid

    # Start with greedy initialization
    D = greedy_init(G, s, n)
    room_assignments = get_rooms_from_D(D)

    best_D = D.copy()
    best_happiness, _ = evaluate_solution(D)

    # Geometric cooling schedule
    T_initial = 50.0
    T_min = 0.5
    alpha = 0.99
    iterations_per_temp = max(3, n // 3)
    max_iterations = 1000 * n
    reheat_threshold = 200  # Reheat if stuck in local optimum

    T = T_initial
    iteration = 0
    no_improve_count = 0

    while T > T_min and iteration < max_iterations:
        for _ in range(iterations_per_temp):
            iteration += 1
            num_rooms = len(room_assignments)

            # Choose move type probabilistically
            move_type = rand.choices(
                ['transfer', 'swap', 'merge', 'split'],
                weights=[0.5, 0.3, 0.1, 0.1]
            )[0]

            new_D = None
            new_rooms = None

            # Transfer: Move one student to a different room
            if move_type == 'transfer' and num_rooms > 1:
                from_room_idx = rand.randint(0, num_rooms - 1)
                if len(room_assignments[from_room_idx]) > 1:  # Don't empty a room
                    student = rand.choice(room_assignments[from_room_idx])
                    to_room_idx = rand.randint(0, num_rooms - 1)
                    if to_room_idx != from_room_idx:
                        new_D = D.copy()
                        new_D[student] = to_room_idx
                        new_D = renumber_D(new_D)
                        new_rooms = get_rooms_from_D(new_D)

            # Swap: Exchange students between two rooms
            elif move_type == 'swap' and num_rooms >= 2:
                room_a, room_b = rand.sample(range(num_rooms), 2)
                if room_assignments[room_a] and room_assignments[room_b]:
                    student_a = rand.choice(room_assignments[room_a])
                    student_b = rand.choice(room_assignments[room_b])
                    new_D = D.copy()
                    new_D[student_a] = room_b
                    new_D[student_b] = room_a
                    new_rooms = get_rooms_from_D(new_D)

            # Merge: Combine two rooms into one
            elif move_type == 'merge' and num_rooms >= 2:
                room_a, room_b = rand.sample(range(num_rooms), 2)
                new_D = D.copy()
                for student in room_assignments[room_b]:
                    new_D[student] = room_a
                new_D = renumber_D(new_D)
                new_rooms = get_rooms_from_D(new_D)

            # Split: Divide one room into two
            elif move_type == 'split' and num_rooms < n:
                room_idx = rand.randint(0, num_rooms - 1)
                room = room_assignments[room_idx]
                if len(room) >= 2:
                    num_to_split = rand.randint(1, len(room) - 1)
                    students_to_move = rand.sample(room, num_to_split)
                    new_D = D.copy()
                    new_room_id = max(D.values()) + 1
                    for student in students_to_move:
                        new_D[student] = new_room_id
                    new_D = renumber_D(new_D)
                    new_rooms = get_rooms_from_D(new_D)

            if new_D is None:
                continue

            new_happiness, new_valid = evaluate_solution(new_D)
            old_happiness, old_valid = evaluate_solution(D)

            delta = new_happiness - old_happiness

            # Acceptance criterion: always accept improvements, probabilistically accept worse solutions
            accept = False
            if delta > 0:
                accept = True
            elif T > 0:
                try:
                    prob = math.exp(delta / T)
                    accept = rand.random() < prob
                except OverflowError:
                    accept = False

            if accept:
                D = new_D
                room_assignments = new_rooms

                if new_valid and new_happiness > best_happiness:
                    best_happiness = new_happiness
                    best_D = D.copy()
                    no_improve_count = 0
                else:
                    no_improve_count += 1
            else:
                no_improve_count += 1

        T *= alpha

        # Reheat if stuck in local optimum
        if no_improve_count > reheat_threshold:
            T = min(T * 2, T_initial / 2)
            no_improve_count = 0

    return best_D, len(set(best_D.values()))


def greedy_init(G, s, n):
    """Greedy initialization: merge rooms with highest happiness/stress ratio"""
    # Start with each student in their own room
    D = {i: i for i in range(n)}
    rooms = {i: [i] for i in range(n)}
    room_stress = {i: 0.0 for i in range(n)}

    # Sort edges by happiness/stress ratio
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            happiness = G.edges[i, j]['happiness']
            stress = G.edges[i, j]['stress']
            ratio = happiness / stress if stress > 0 else float('inf')
            edges.append((i, j, ratio))
    edges.sort(key=lambda x: x[2], reverse=True)

    for i, j, _ in edges:
        if len(rooms) <= 1:
            break

        room_i = D[i]
        room_j = D[j]
        if room_i == room_j:
            continue

        students_i = rooms[room_i]
        students_j = rooms[room_j]
        merged_stress = room_stress[room_i] + room_stress[room_j]
        for si in students_i:
            for sj in students_j:
                merged_stress += G.edges[si, sj]['stress']

        potential_rooms = len(rooms) - 1
        budget = s / potential_rooms if potential_rooms > 0 else float('inf')

        if merged_stress <= budget:
            for student in students_j:
                D[student] = room_i
                rooms[room_i].append(student)
            room_stress[room_i] = merged_stress
            del rooms[room_j]
            del room_stress[room_j]

    room_map = {}
    next_room = 0
    for student in range(n):
        room = D[student]
        if room not in room_map:
            room_map[room] = next_room
            next_room += 1
        D[student] = room_map[room]

    return D
