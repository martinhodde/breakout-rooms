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


def greedy_local_search(G, s, max_local_search_iterations=1000):
    nodes = list(G.nodes)
    n = len(nodes)

    D, k = greedy_construction(G, s, n)
    D, k = local_search(G, s, D, k, max_local_search_iterations)

    return D, k


def greedy_construction(G, s, n):
    """Build initial solution by greedily merging rooms"""
    nodes = list(G.nodes)

    # Sort edges by happiness/stress ratio (prioritize high-value, low-stress pairs)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            happiness = G.edges[i, j]['happiness']
            stress = G.edges[i, j]['stress']
            ratio = happiness / stress if stress > 0 else float('inf')
            edges.append((i, j, happiness, stress, ratio))
    edges.sort(key=lambda x: x[4], reverse=True)

    # Start with each student in their own room
    D = {i: i for i in range(n)}
    rooms = {i: [i] for i in range(n)}
    room_stress = {i: 0.0 for i in range(n)}

    def merge_rooms(room_a, room_b, stress_budget_per_room):
        """Merge room_b into room_a if stress constraint allows"""
        if room_a == room_b:
            return False

        students_a = rooms[room_a]
        students_b = rooms[room_b]

        # Calculate total stress if rooms are merged
        combined_stress = room_stress[room_a] + room_stress[room_b]
        for student_a in students_a:
            for student_b in students_b:
                combined_stress += G.edges[student_a, student_b]['stress']

        if combined_stress <= stress_budget_per_room:
            for student in students_b:
                D[student] = room_a
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

        room_i = D[student_i]
        room_j = D[student_j]

        # Only merge if students are in different rooms
        if room_i != room_j:
            # Calculate stress budget assuming merge succeeds
            potential_rooms = num_rooms - 1
            potential_budget = s / potential_rooms if potential_rooms > 0 else float('inf')
            merge_rooms(room_i, room_j, potential_budget)

    D, k = renumber_rooms(D)

    return D, k


def renumber_rooms(D):
    room_ids = sorted(set(D.values()))
    room_map = {old: new for new, old in enumerate(room_ids)}
    new_D = {student: room_map[room] for student, room in D.items()}
    return new_D, len(room_ids)


def local_search(G, s, D, k, max_iterations):
    """Iteratively improve solution through local moves"""
    best_D = D.copy()
    best_k = k
    best_happiness = calculate_happiness(D, G)

    for iteration in range(max_iterations):
        improved = False

        # Rebuild room structure
        rooms = {}
        for student, room in D.items():
            rooms.setdefault(room, []).append(student)
        k = len(rooms)
        room_ids = list(rooms.keys())

        # Try moving each student to a different room
        students = list(D.keys())
        random.shuffle(students)

        for student in students:
            current_room = D[student]
            current_room_students = rooms[current_room]

            # Don't empty a room
            if len(current_room_students) == 1:
                continue

            for target_room in room_ids:
                if target_room == current_room:
                    continue

                new_D = D.copy()
                new_D[student] = target_room

                if is_valid_solution(new_D, G, s, k):
                    new_happiness = calculate_happiness(new_D, G)
                    if new_happiness > best_happiness:
                        best_D = new_D.copy()
                        best_happiness = new_happiness
                        D = new_D
                        improved = True
                        break

            if improved:
                break

        if improved:
            continue

        # Try swapping students between rooms
        if len(room_ids) >= 2:
            for _ in range(min(100, k * k)):
                room_a, room_b = random.sample(room_ids, 2)
                if not rooms[room_a] or not rooms[room_b]:
                    continue

                student_a = random.choice(rooms[room_a])
                student_b = random.choice(rooms[room_b])

                new_D = D.copy()
                new_D[student_a] = room_b
                new_D[student_b] = room_a

                if is_valid_solution(new_D, G, s, k):
                    new_happiness = calculate_happiness(new_D, G)
                    if new_happiness > best_happiness:
                        best_D = new_D.copy()
                        best_happiness = new_happiness
                        D = new_D
                        improved = True
                        break

        # Try merging rooms if no other improvements found
        if not improved:
            if k > 1:
                merge_improved = try_merge_rooms(G, s, D, rooms, best_happiness)
                if merge_improved:
                    D, k, best_happiness = merge_improved
                    best_D = D.copy()
                    improved = True
                else:
                    break  # No improvements possible
            else:
                break

    return best_D, len(set(best_D.values()))


def try_merge_rooms(G, s, D, rooms, current_happiness):
    room_ids = list(rooms.keys())

    for i, room_a in enumerate(room_ids):
        for room_b in room_ids[i + 1:]:
            new_D = D.copy()
            for student in rooms[room_b]:
                new_D[student] = room_a

            new_k = len(set(new_D.values()))

            if is_valid_solution(new_D, G, s, new_k):
                new_happiness = calculate_happiness(new_D, G)
                if new_happiness >= current_happiness:
                    new_D, new_k = renumber_rooms(new_D)
                    return new_D, new_k, new_happiness

    return None
