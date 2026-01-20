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


def simulated_annealing(graph, stress_budget):
    nodes = list(graph.nodes)
    num_students = len(nodes)

    def get_room_lists(assignment):
        """Convert assignment dict to list of room memberships"""
        rooms = {}
        for student, room in assignment.items():
            rooms.setdefault(room, []).append(student)
        return [rooms[room_id] for room_id in sorted(rooms.keys())]

    def renumber_rooms(assignment):
        """Renumber rooms to be contiguous starting from 0"""
        room_map = {}
        next_room = 0
        renumbered = {}
        for student in sorted(assignment.keys()):
            room = assignment[student]
            if room not in room_map:
                room_map[room] = next_room
                next_room += 1
            renumbered[student] = room_map[room]
        return renumbered

    def evaluate_solution(assignment):
        """Calculate happiness and validity of an assignment"""
        rooms = get_room_lists(assignment)
        num_rooms = len(rooms)
        is_valid = is_valid_solution(assignment, graph, stress_budget, num_rooms)
        happiness = calculate_happiness(assignment, graph) if is_valid else -1000
        return happiness, is_valid

    # Start with greedy initialization
    current_assignment = greedy_init(graph, stress_budget, num_students)
    room_assignments = get_room_lists(current_assignment)

    best_assignment = current_assignment.copy()
    best_happiness, _ = evaluate_solution(current_assignment)

    # Cache current solution's happiness to avoid redundant calculations
    current_happiness = best_happiness

    # Geometric cooling schedule parameters
    initial_temp = 50.0
    min_temp = 0.5
    cooling_rate = 0.97  # Faster cooling (was 0.99) for performance
    iterations_per_temp = max(3, num_students // 3)
    max_iterations = 500 * num_students  # Reduced from 1000x for performance
    reheat_threshold = 150  # Reduced threshold (was 200) for faster convergence

    temperature = initial_temp
    iteration = 0
    no_improve_count = 0
    reheat_count = 0
    max_reheats = 3  # Early termination if reheating doesn't help

    while temperature > min_temp and iteration < max_iterations and reheat_count < max_reheats:
        for _ in range(iterations_per_temp):
            iteration += 1
            num_rooms = len(room_assignments)

            # Choose move type probabilistically
            move_type = rand.choices(
                ['transfer', 'swap', 'merge', 'split'],
                weights=[0.5, 0.3, 0.1, 0.1]
            )[0]

            new_assignment = None
            new_room_lists = None

            # Transfer: Move one student to a different room
            if move_type == 'transfer' and num_rooms > 1:
                from_room_idx = rand.randint(0, num_rooms - 1)
                if len(room_assignments[from_room_idx]) > 1:  # Don't empty a room
                    student = rand.choice(room_assignments[from_room_idx])
                    to_room_idx = rand.randint(0, num_rooms - 1)
                    if to_room_idx != from_room_idx:
                        new_assignment = current_assignment.copy()
                        new_assignment[student] = to_room_idx
                        # No renumbering needed for transfer
                        new_room_lists = get_room_lists(new_assignment)

            # Swap: Exchange students between two rooms
            elif move_type == 'swap' and num_rooms >= 2:
                room_a_idx, room_b_idx = rand.sample(range(num_rooms), 2)
                if room_assignments[room_a_idx] and room_assignments[room_b_idx]:
                    student_a = rand.choice(room_assignments[room_a_idx])
                    student_b = rand.choice(room_assignments[room_b_idx])
                    new_assignment = current_assignment.copy()
                    new_assignment[student_a] = room_b_idx
                    new_assignment[student_b] = room_a_idx
                    # No renumbering needed for swap
                    new_room_lists = get_room_lists(new_assignment)

            # Merge: Combine two rooms into one
            elif move_type == 'merge' and num_rooms >= 2:
                room_a_idx, room_b_idx = rand.sample(range(num_rooms), 2)
                new_assignment = current_assignment.copy()
                for student in room_assignments[room_b_idx]:
                    new_assignment[student] = room_a_idx
                # Renumber after merge to keep room IDs contiguous
                new_assignment = renumber_rooms(new_assignment)
                new_room_lists = get_room_lists(new_assignment)

            # Split: Divide one room into two
            elif move_type == 'split' and num_rooms < num_students:
                room_idx = rand.randint(0, num_rooms - 1)
                room_students = room_assignments[room_idx]
                if len(room_students) >= 2:
                    num_to_split = rand.randint(1, len(room_students) - 1)
                    students_to_move = rand.sample(room_students, num_to_split)
                    new_assignment = current_assignment.copy()
                    new_room_id = max(current_assignment.values()) + 1
                    for student in students_to_move:
                        new_assignment[student] = new_room_id
                    # Renumber after split to keep room IDs contiguous
                    new_assignment = renumber_rooms(new_assignment)
                    new_room_lists = get_room_lists(new_assignment)

            if new_assignment is None:
                continue

            new_happiness, new_valid = evaluate_solution(new_assignment)
            # Use cached current_happiness instead of re-evaluating
            happiness_delta = new_happiness - current_happiness

            # Acceptance criterion: always accept improvements, probabilistically accept worse solutions
            accept_move = False
            if happiness_delta > 0:
                accept_move = True
            elif temperature > 0:
                try:
                    acceptance_prob = math.exp(happiness_delta / temperature)
                    accept_move = rand.random() < acceptance_prob
                except OverflowError:
                    accept_move = False

            if accept_move:
                current_assignment = new_assignment
                room_assignments = new_room_lists
                current_happiness = new_happiness  # Update cached happiness

                if new_valid and new_happiness > best_happiness:
                    best_happiness = new_happiness
                    best_assignment = current_assignment.copy()
                    no_improve_count = 0
                else:
                    no_improve_count += 1
            else:
                no_improve_count += 1

        temperature *= cooling_rate

        # Reheat if stuck in local optimum
        if no_improve_count > reheat_threshold:
            temperature = min(temperature * 2, initial_temp / 2)
            no_improve_count = 0
            reheat_count += 1

    return best_assignment, len(set(best_assignment.values()))


def greedy_init(graph, stress_budget, num_students):
    """Greedy initialization: merge rooms with highest happiness/stress ratio"""
    # Start with each student in their own room
    assignment = {i: i for i in range(num_students)}
    rooms = {i: [i] for i in range(num_students)}
    room_stress = {i: 0.0 for i in range(num_students)}

    # Sort edges by happiness/stress ratio
    edges = []
    for i in range(num_students):
        for j in range(i + 1, num_students):
            happiness = graph.edges[i, j]['happiness']
            stress = graph.edges[i, j]['stress']
            ratio = happiness / stress if stress > 0 else float('inf')
            edges.append((i, j, ratio))
    edges.sort(key=lambda x: x[2], reverse=True)

    for student_i, student_j, _ in edges:
        if len(rooms) <= 1:
            break

        room_i = assignment[student_i]
        room_j = assignment[student_j]
        if room_i == room_j:
            continue

        students_in_room_i = rooms[room_i]
        students_in_room_j = rooms[room_j]
        merged_stress = room_stress[room_i] + room_stress[room_j]
        for si in students_in_room_i:
            for sj in students_in_room_j:
                merged_stress += graph.edges[si, sj]['stress']

        potential_rooms = len(rooms) - 1
        budget_per_room = stress_budget / potential_rooms if potential_rooms > 0 else float('inf')

        if merged_stress <= budget_per_room:
            for student in students_in_room_j:
                assignment[student] = room_i
                rooms[room_i].append(student)
            room_stress[room_i] = merged_stress
            del rooms[room_j]
            del room_stress[room_j]

    # Renumber rooms to be contiguous
    room_map = {}
    next_room = 0
    for student in range(num_students):
        room = assignment[student]
        if room not in room_map:
            room_map[room] = next_room
            next_room += 1
        assignment[student] = room_map[room]

    return assignment
