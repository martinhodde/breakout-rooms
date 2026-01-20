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


def genetic_algorithm(graph, stress_budget, population_size=50, generations=200, mutation_rate=0.1,
                      tournament_size=3, elite_count=2):
    """Genetic algorithm using chromosomes as room assignment vectors"""
    nodes = list(graph.nodes)
    num_students = len(nodes)

    population = initialize_population(graph, stress_budget, num_students, population_size)

    best_individual = None
    best_fitness = float('-inf')

    for generation in range(generations):
        fitness_scores = [evaluate_fitness(ind, graph, stress_budget) for ind in population]

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

            child1, child2 = crossover(parent1, parent2, num_students)

            if random.random() < mutation_rate:
                child1 = mutate(child1, num_students)
            if random.random() < mutation_rate:
                child2 = mutate(child2, num_students)

            child1 = repair_chromosome(child1, graph, stress_budget)
            child2 = repair_chromosome(child2, graph, stress_budget)

            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)

        population = new_population

    fitness_scores = [evaluate_fitness(ind, graph, stress_budget) for ind in population]
    for i, fitness in enumerate(fitness_scores):
        if fitness > best_fitness:
            best_fitness = fitness
            best_individual = population[i].copy()

    assignment = chromosome_to_dict(best_individual)
    num_rooms = len(set(best_individual))

    if not is_valid_solution(assignment, graph, stress_budget, num_rooms):
        assignment = {i: i for i in range(num_students)}
        num_rooms = num_students

    return assignment, num_rooms


def initialize_population(graph, stress_budget, num_students, population_size):
    """Create diverse initial population with identity, greedy, and random solutions"""
    population = []

    # Identity solution: each student in their own room
    population.append([i for i in range(num_students)])

    # Greedy solutions provide good starting points
    for _ in range(population_size // 4):
        chromosome = create_greedy_chromosome(graph, stress_budget, num_students)
        population.append(chromosome)

    # Random solutions for diversity
    while len(population) < population_size:
        num_rooms = random.randint(1, num_students)
        chromosome = [random.randint(0, num_rooms - 1) for _ in range(num_students)]
        population.append(chromosome)

    return population


def create_greedy_chromosome(graph, stress_budget, num_students):
    """Create chromosome using greedy room merging based on happiness gain"""
    # Start with each student in their own room
    chromosome = list(range(num_students))

    def get_room_stress(chromosome, room):
        students = [i for i, room_id in enumerate(chromosome) if room_id == room]
        if len(students) <= 1:
            return 0
        return calculate_stress_for_room(students, graph)

    active_rooms = set(range(num_students))

    # Try merging rooms greedily
    for _ in range(num_students - 1):
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
                merged_stress = calculate_stress_for_room(merged, graph)

                # Check if merge respects stress constraint
                potential_rooms = len(active_rooms) - 1
                if potential_rooms > 0:
                    budget_per_room = stress_budget / potential_rooms
                    if merged_stress <= budget_per_room:
                        # Calculate happiness gain from merging
                        happiness_gain = 0
                        for student_a in students_a:
                            for student_b in students_b:
                                happiness_gain += graph.edges[student_a, student_b]['happiness']

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
    for i in range(num_students):
        if chromosome[i] not in room_mapping:
            room_mapping[chromosome[i]] = next_room
            next_room += 1
        chromosome[i] = room_mapping[chromosome[i]]

    return chromosome


def evaluate_fitness(chromosome, graph, stress_budget):
    """Evaluate fitness: happiness for valid solutions, negative penalty for invalid"""
    assignment = chromosome_to_dict(chromosome)
    num_rooms = len(set(chromosome))

    if not is_valid_solution(assignment, graph, stress_budget, num_rooms):
        # Penalize but don't completely reject invalid solutions (allows evolution to fix)
        stress_penalty = calculate_stress_violation(chromosome, graph, stress_budget)
        return -stress_penalty

    return calculate_happiness(assignment, graph)


def calculate_stress_violation(chromosome, graph, stress_budget):
    num_rooms = len(set(chromosome))
    if num_rooms == 0:
        return float('inf')

    budget_per_room = stress_budget / num_rooms
    total_violation = 0

    rooms = {}
    for i, room in enumerate(chromosome):
        rooms.setdefault(room, []).append(i)

    for students in rooms.values():
        room_stress = calculate_stress_for_room(students, graph)
        if room_stress > budget_per_room:
            total_violation += room_stress - budget_per_room

    return total_violation


def tournament_select(population, fitness_scores, tournament_size):
    indices = random.sample(range(len(population)), min(tournament_size, len(population)))
    best_idx = max(indices, key=lambda i: fitness_scores[i])
    return population[best_idx].copy()


def crossover(parent1, parent2, num_students):
    child1 = []
    child2 = []

    for i in range(num_students):
        if random.random() < 0.5:
            child1.append(parent1[i])
            child2.append(parent2[i])
        else:
            child1.append(parent2[i])
            child2.append(parent1[i])

    return child1, child2


def mutate(chromosome, num_students):
    chromosome = chromosome.copy()
    num_rooms = len(set(chromosome))

    mutation_type = random.choice(['swap', 'move', 'split', 'merge'])

    if mutation_type == 'swap' and num_students >= 2:
        i, j = random.sample(range(num_students), 2)
        chromosome[i], chromosome[j] = chromosome[j], chromosome[i]

    elif mutation_type == 'move':
        i = random.randint(0, num_students - 1)
        chromosome[i] = random.randint(0, num_rooms - 1)

    elif mutation_type == 'split' and num_rooms > 0:
        room_to_split = random.randint(0, num_rooms - 1)
        students_in_room = [i for i, room_id in enumerate(chromosome) if room_id == room_to_split]
        if len(students_in_room) > 1:
            new_room = max(chromosome) + 1
            num_to_move = random.randint(1, len(students_in_room) - 1)
            students_to_move = random.sample(students_in_room, num_to_move)
            for student in students_to_move:
                chromosome[student] = new_room

    elif mutation_type == 'merge' and num_rooms > 1:
        rooms = list(set(chromosome))
        if len(rooms) >= 2:
            room_a, room_b = random.sample(rooms, 2)
            for i in range(num_students):
                if chromosome[i] == room_b:
                    chromosome[i] = room_a

    return chromosome


def repair_chromosome(chromosome, graph, stress_budget):
    """Attempt to fix constraint violations by splitting overloaded rooms"""
    num_students = len(chromosome)

    # Renumber rooms to be contiguous
    room_mapping = {}
    next_room = 0
    for i in range(num_students):
        if chromosome[i] not in room_mapping:
            room_mapping[chromosome[i]] = next_room
            next_room += 1
        chromosome[i] = room_mapping[chromosome[i]]

    assignment = chromosome_to_dict(chromosome)
    num_rooms = len(set(chromosome))

    if is_valid_solution(assignment, graph, stress_budget, num_rooms):
        return chromosome

    # Try splitting overloaded rooms (up to 10 attempts)
    for attempt in range(10):
        rooms = {}
        for i, room in enumerate(chromosome):
            rooms.setdefault(room, []).append(i)

        num_rooms = len(rooms)
        budget_per_room = stress_budget / num_rooms if num_rooms > 0 else 0

        fixed = True
        for room, students in list(rooms.items()):
            room_stress = calculate_stress_for_room(students, graph)
            if room_stress > budget_per_room and len(students) > 1:
                fixed = False
                # Move highest-stress student to new room
                max_stress_student = max(students, key=lambda student: sum(
                    graph.edges[student, other]['stress'] for other in students if other != student
                ))
                new_room = max(chromosome) + 1
                chromosome[max_stress_student] = new_room
                break

        if fixed:
            break

    return chromosome


def chromosome_to_dict(chromosome):
    return {i: room for i, room in enumerate(chromosome)}
