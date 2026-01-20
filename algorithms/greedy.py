"""
Greedy algorithm with local search for breakout room assignment.
"""

import random
import copy
from utils import (
    is_valid_solution,
    calculate_happiness,
    calculate_stress_for_room,
    calculate_happiness_for_room
)


def greedy_local_search(graph, stress_budget, max_local_search_iterations=1000):
    nodes = list(graph.nodes)
    num_students = len(nodes)

    assignment, num_rooms = greedy_construction(graph, stress_budget, num_students)
    assignment, num_rooms = local_search(graph, stress_budget, assignment, num_rooms, max_local_search_iterations)

    return assignment, num_rooms


def greedy_construction(graph, stress_budget, num_students):
    """Build initial solution by greedily merging rooms"""
    nodes = list(graph.nodes)

    # Sort edges by happiness/stress ratio (prioritize high-value, low-stress pairs)
    edges = []
    for i in range(num_students):
        for j in range(i + 1, num_students):
            happiness = graph.edges[i, j]['happiness']
            stress = graph.edges[i, j]['stress']
            ratio = happiness / stress if stress > 0 else float('inf')
            edges.append((i, j, happiness, stress, ratio))
    edges.sort(key=lambda x: x[4], reverse=True)

    # Start with each student in their own room
    assignment = {i: i for i in range(num_students)}
    rooms = {i: [i] for i in range(num_students)}
    room_stress = {i: 0.0 for i in range(num_students)}

    def merge_rooms(room_a, room_b, budget_per_room):
        """Merge room_b into room_a if stress constraint allows"""
        if room_a == room_b:
            return False

        students_a = rooms[room_a]
        students_b = rooms[room_b]

        # Calculate total stress if rooms are merged
        combined_stress = room_stress[room_a] + room_stress[room_b]
        for student_a in students_a:
            for student_b in students_b:
                combined_stress += graph.edges[student_a, student_b]['stress']

        if combined_stress <= budget_per_room:
            for student in students_b:
                assignment[student] = room_a
                rooms[room_a].append(student)
            room_stress[room_a] = combined_stress
            del rooms[room_b]
            del room_stress[room_b]
            return True
        return False

    # Try merging rooms in order of highest happiness/stress ratio
    for student_i, student_j, happiness, stress, ratio in edges:
        num_rooms = len(rooms)
        if num_rooms <= 1:
            break

        room_i = assignment[student_i]
        room_j = assignment[student_j]

        # Only merge if students are in different rooms
        if room_i != room_j:
            # Calculate stress budget assuming merge succeeds
            potential_rooms = num_rooms - 1
            potential_budget = stress_budget / potential_rooms if potential_rooms > 0 else float('inf')
            merge_rooms(room_i, room_j, potential_budget)

    assignment, num_rooms = renumber_rooms(assignment)

    return assignment, num_rooms


def renumber_rooms(assignment):
    room_ids = sorted(set(assignment.values()))
    room_map = {old: new for new, old in enumerate(room_ids)}
    renumbered = {student: room_map[room] for student, room in assignment.items()}
    return renumbered, len(room_ids)


def local_search(graph, stress_budget, assignment, num_rooms, max_iterations):
    """Iteratively improve solution through local moves"""
    best_assignment = assignment.copy()
    best_num_rooms = num_rooms
    best_happiness = calculate_happiness(assignment, graph)

    for iteration in range(max_iterations):
        improved = False

        # Rebuild room structure
        rooms = {}
        for student, room in assignment.items():
            rooms.setdefault(room, []).append(student)
        num_rooms = len(rooms)
        room_ids = list(rooms.keys())

        # Try moving each student to a different room
        students = list(assignment.keys())
        random.shuffle(students)

        for student in students:
            current_room = assignment[student]
            current_room_students = rooms[current_room]

            # Don't empty a room
            if len(current_room_students) == 1:
                continue

            for target_room in room_ids:
                if target_room == current_room:
                    continue

                new_assignment = assignment.copy()
                new_assignment[student] = target_room

                if is_valid_solution(new_assignment, graph, stress_budget, num_rooms):
                    new_happiness = calculate_happiness(new_assignment, graph)
                    if new_happiness > best_happiness:
                        best_assignment = new_assignment.copy()
                        best_happiness = new_happiness
                        assignment = new_assignment
                        improved = True
                        break

            if improved:
                break

        if improved:
            continue

        # Try swapping students between rooms
        if len(room_ids) >= 2:
            for _ in range(min(100, num_rooms * num_rooms)):
                room_a, room_b = random.sample(room_ids, 2)
                if not rooms[room_a] or not rooms[room_b]:
                    continue

                student_a = random.choice(rooms[room_a])
                student_b = random.choice(rooms[room_b])

                new_assignment = assignment.copy()
                new_assignment[student_a] = room_b
                new_assignment[student_b] = room_a

                if is_valid_solution(new_assignment, graph, stress_budget, num_rooms):
                    new_happiness = calculate_happiness(new_assignment, graph)
                    if new_happiness > best_happiness:
                        best_assignment = new_assignment.copy()
                        best_happiness = new_happiness
                        assignment = new_assignment
                        improved = True
                        break

        # Try merging rooms if no other improvements found
        if not improved:
            if num_rooms > 1:
                merge_improved = try_merge_rooms(graph, stress_budget, assignment, rooms, best_happiness)
                if merge_improved:
                    assignment, num_rooms, best_happiness = merge_improved
                    best_assignment = assignment.copy()
                    improved = True
                else:
                    break  # No improvements possible
            else:
                break

    return best_assignment, len(set(best_assignment.values()))


def try_merge_rooms(graph, stress_budget, assignment, rooms, current_happiness):
    room_ids = list(rooms.keys())

    for i, room_a in enumerate(room_ids):
        for room_b in room_ids[i + 1:]:
            new_assignment = assignment.copy()
            for student in rooms[room_b]:
                new_assignment[student] = room_a

            new_num_rooms = len(set(new_assignment.values()))

            if is_valid_solution(new_assignment, graph, stress_budget, new_num_rooms):
                new_happiness = calculate_happiness(new_assignment, graph)
                if new_happiness >= current_happiness:
                    new_assignment, new_num_rooms = renumber_rooms(new_assignment)
                    return new_assignment, new_num_rooms, new_happiness

    return None
