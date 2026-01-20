import networkx as nx

def is_valid_solution(D, G, s, num_rooms):
    """
    Checks whether D is a valid mapping by verifying each room adheres to the stress budget.

    Args:
        D: Dictionary mapping student to room
        G: networkx.Graph
        s: Total stress budget
        num_rooms: Number of breakout rooms

    Returns:
        bool: whether D is a valid solution
    """
    budget_per_room = s / num_rooms
    room_to_students = {}
    for student, room in D.items():
        room_to_students.setdefault(room, []).append(student)

    for room, students in room_to_students.items():
        room_stress = calculate_stress_for_room(students, G)
        if room_stress > budget_per_room:
            return False
    return True


def calculate_happiness(D, G):
    """
    Calculates the total happiness in mapping D by summing the happiness of each room.

    Args:
        D: Dictionary mapping student to room
        G: networkx.Graph

    Returns:
        float: total happiness
    """
    room_to_students = {}
    for student, room in D.items():
        room_to_students.setdefault(room, []).append(student)

    total_happiness = 0
    for room, students in room_to_students.items():
        room_happiness = calculate_happiness_for_room(students, G)
        total_happiness += room_happiness
    return total_happiness

def convert_dictionary(room_to_students):
    """
    Converts the dictionary mapping room_to_students to student_to_room format.

    Args:
        room_to_students: Dictionary of room to a list of students

    Returns:
        D: Dictionary mapping student to room

    Example: {0: [1,2,3]} ==> {1:0, 2:0, 3:0}
    """
    student_to_room = {}
    for room, students in room_to_students.items():
        for student in students:
            student_to_room[student] = room
    return student_to_room


def calculate_stress_for_room(students, G):
    """
    Calculate total stress for a room (sum of pairwise stress values).

    Args:
        students: List of students in the room
        G: networkx.Graph with stress edge attribute

    Returns:
        float: Total stress for the room
    """
    subgraph = G.subgraph(students)
    return subgraph.size("stress")


def calculate_happiness_for_room(students, G):
    """
    Calculate total happiness for a room (sum of pairwise happiness values).

    Args:
        students: List of students in the room
        G: networkx.Graph with happiness edge attribute

    Returns:
        float: Total happiness for the room
    """
    subgraph = G.subgraph(students)
    return subgraph.size("happiness")
