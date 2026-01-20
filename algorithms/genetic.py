"""
Genetic Algorithm for breakout room assignment.
"""

import random
import copy
from utils import (
    is_valid_solution,
    calculate_happiness,
    calculate_stress_for_room
)


def genetic_algorithm(G, s, population_size=50, generations=200, mutation_rate=0.1,
                      tournament_size=3, elite_count=2):
    """Genetic algorithm using chromosomes as room assignment vectors"""
    nodes = list(G.nodes)
    n = len(nodes)

    population = initialize_population(G, s, n, population_size)

    best_individual = None
    best_fitness = float('-inf')

    for generation in range(generations):
        fitness_scores = [evaluate_fitness(ind, G, s) for ind in population]

        # Track best solution found so far
        for i, fitness in enumerate(fitness_scores):
            if fitness > best_fitness:
                best_fitness = fitness
                best_individual = population[i].copy()

        new_population = []

        # Elitism: preserve best individuals
        sorted_pop = sorted(zip(fitness_scores, population), key=lambda x: x[0], reverse=True)
        for i in range(min(elite_count, len(sorted_pop))):
            new_population.append(sorted_pop[i][1].copy())

        # Generate offspring through selection, crossover, and mutation
        while len(new_population) < population_size:
            parent1 = tournament_select(population, fitness_scores, tournament_size)
            parent2 = tournament_select(population, fitness_scores, tournament_size)

            child1, child2 = crossover(parent1, parent2, n)

            if random.random() < mutation_rate:
                child1 = mutate(child1, n)
            if random.random() < mutation_rate:
                child2 = mutate(child2, n)

            child1 = repair_chromosome(child1, G, s)
            child2 = repair_chromosome(child2, G, s)

            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)

        population = new_population

    fitness_scores = [evaluate_fitness(ind, G, s) for ind in population]
    for i, fitness in enumerate(fitness_scores):
        if fitness > best_fitness:
            best_fitness = fitness
            best_individual = population[i].copy()

    D = chromosome_to_dict(best_individual)
    k = len(set(best_individual))

    if not is_valid_solution(D, G, s, k):
        D = {i: i for i in range(n)}
        k = n

    return D, k


def initialize_population(G, s, n, population_size):
    """Create diverse initial population with identity, greedy, and random solutions"""
    population = []

    # Identity solution: each student in their own room
    population.append([i for i in range(n)])

    # Greedy solutions provide good starting points
    for _ in range(population_size // 4):
        chromosome = create_greedy_chromosome(G, s, n)
        population.append(chromosome)

    # Random solutions for diversity
    while len(population) < population_size:
        num_rooms = random.randint(1, n)
        chromosome = [random.randint(0, num_rooms - 1) for _ in range(n)]
        population.append(chromosome)

    return population


def create_greedy_chromosome(G, s, n):
    """Create chromosome using greedy room merging based on happiness gain"""
    # Start with each student in their own room
    chromosome = list(range(n))

    def get_room_stress(chromosome, room):
        students = [i for i, room_id in enumerate(chromosome) if room_id == room]
        if len(students) <= 1:
            return 0
        return calculate_stress_for_room(students, G)

    active_rooms = set(range(n))

    # Try merging rooms greedily
    for _ in range(n - 1):
        if len(active_rooms) <= 1:
            break

        best_merge = None
        best_benefit = float('-inf')

        rooms_list = list(active_rooms)
        for i, room_a in enumerate(rooms_list):
            students_a = [j for j, room_id in enumerate(chromosome) if room_id == room_a]

            for room_b in rooms_list[i + 1:]:
                students_b = [j for j, room_id in enumerate(chromosome) if room_id == room_b]

                merged = students_a + students_b
                merged_stress = calculate_stress_for_room(merged, G)

                # Check if merge respects stress constraint
                potential_rooms = len(active_rooms) - 1
                if potential_rooms > 0:
                    stress_budget = s / potential_rooms
                    if merged_stress <= stress_budget:
                        # Calculate happiness gain from merging
                        happiness_gain = 0
                        for student_a in students_a:
                            for student_b in students_b:
                                happiness_gain += G.edges[student_a, student_b]['happiness']

                        if happiness_gain > best_benefit:
                            best_benefit = happiness_gain
                            best_merge = (room_a, room_b)

        if best_merge:
            room_a, room_b = best_merge
            for i in range(n):
                if chromosome[i] == room_b:
                    chromosome[i] = room_a
            active_rooms.remove(room_b)
        else:
            break

    room_mapping = {}
    next_room = 0
    for i in range(n):
        if chromosome[i] not in room_mapping:
            room_mapping[chromosome[i]] = next_room
            next_room += 1
        chromosome[i] = room_mapping[chromosome[i]]

    return chromosome


def evaluate_fitness(chromosome, G, s):
    """Evaluate fitness: happiness for valid solutions, negative penalty for invalid"""
    D = chromosome_to_dict(chromosome)
    k = len(set(chromosome))

    if not is_valid_solution(D, G, s, k):
        # Penalize but don't completely reject invalid solutions (allows evolution to fix)
        stress_penalty = calculate_stress_violation(chromosome, G, s)
        return -stress_penalty

    return calculate_happiness(D, G)


def calculate_stress_violation(chromosome, G, s):
    k = len(set(chromosome))
    if k == 0:
        return float('inf')

    budget_per_room = s / k
    total_violation = 0

    rooms = {}
    for i, room in enumerate(chromosome):
        rooms.setdefault(room, []).append(i)

    for students in rooms.values():
        room_stress = calculate_stress_for_room(students, G)
        if room_stress > budget_per_room:
            total_violation += room_stress - budget_per_room

    return total_violation


def tournament_select(population, fitness_scores, tournament_size):
    indices = random.sample(range(len(population)), min(tournament_size, len(population)))
    best_idx = max(indices, key=lambda i: fitness_scores[i])
    return population[best_idx].copy()


def crossover(parent1, parent2, n):
    child1 = []
    child2 = []

    for i in range(n):
        if random.random() < 0.5:
            child1.append(parent1[i])
            child2.append(parent2[i])
        else:
            child1.append(parent2[i])
            child2.append(parent1[i])

    return child1, child2


def mutate(chromosome, n):
    chromosome = chromosome.copy()
    num_rooms = len(set(chromosome))

    mutation_type = random.choice(['swap', 'move', 'split', 'merge'])

    if mutation_type == 'swap' and n >= 2:
        i, j = random.sample(range(n), 2)
        chromosome[i], chromosome[j] = chromosome[j], chromosome[i]

    elif mutation_type == 'move':
        i = random.randint(0, n - 1)
        chromosome[i] = random.randint(0, num_rooms - 1)

    elif mutation_type == 'split' and num_rooms > 0:
        room_to_split = random.randint(0, num_rooms - 1)
        students_in_room = [i for i, r in enumerate(chromosome) if r == room_to_split]
        if len(students_in_room) > 1:
            new_room = max(chromosome) + 1
            num_to_move = random.randint(1, len(students_in_room) - 1)
            students_to_move = random.sample(students_in_room, num_to_move)
            for s in students_to_move:
                chromosome[s] = new_room

    elif mutation_type == 'merge' and num_rooms > 1:
        rooms = list(set(chromosome))
        if len(rooms) >= 2:
            room_a, room_b = random.sample(rooms, 2)
            for i in range(n):
                if chromosome[i] == room_b:
                    chromosome[i] = room_a

    return chromosome


def repair_chromosome(chromosome, G, s):
    """Attempt to fix constraint violations by splitting overloaded rooms"""
    n = len(chromosome)

    # Renumber rooms to be contiguous
    room_mapping = {}
    next_room = 0
    for i in range(n):
        if chromosome[i] not in room_mapping:
            room_mapping[chromosome[i]] = next_room
            next_room += 1
        chromosome[i] = room_mapping[chromosome[i]]

    D = chromosome_to_dict(chromosome)
    k = len(set(chromosome))

    if is_valid_solution(D, G, s, k):
        return chromosome

    # Try splitting overloaded rooms (up to 10 attempts)
    for attempt in range(10):
        rooms = {}
        for i, room in enumerate(chromosome):
            rooms.setdefault(room, []).append(i)

        k = len(rooms)
        budget_per_room = s / k if k > 0 else 0

        fixed = True
        for room, students in list(rooms.items()):
            room_stress = calculate_stress_for_room(students, G)
            if room_stress > budget_per_room and len(students) > 1:
                fixed = False
                # Move highest-stress student to new room
                max_stress_student = max(students, key=lambda student: sum(
                    G.edges[student, other]['stress'] for other in students if other != student
                ))
                new_room = max(chromosome) + 1
                chromosome[max_stress_student] = new_room
                break

        if fixed:
            break

    return chromosome


def chromosome_to_dict(chromosome):
    return {i: room for i, room in enumerate(chromosome)}
