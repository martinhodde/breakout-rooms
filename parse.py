import re
import os

import networkx as nx

import utils


def validate_file(path):
    """Validate that file is under 100KB and contains only numbers/spaces"""
    if os.path.getsize(path) > 100000:
        print(f"{path} exceeds 100KB, make sure you're not repeating edges!")
        return False
    with open(path, "r") as file:
        if not re.match(r"^[\d\.\s]+$", file.read()):
            print(f"{path} contains characters that are not numbers and spaces")
            return False
    return True


def read_input_file(path, max_size=None):
    """
    Parses and validates an input file.

    Args:
        path: Path to input file
        max_size: Maximum number of nodes allowed (optional)

    Returns:
        tuple: (G, stress_budget) where G is a complete, connected networkx.Graph

    Raises:
        AssertionError: If input file is malformed or invalid
    """
    with open(path, "r") as file:
        # Read number of students
        num_students = file.readline().strip()
        assert num_students.isdigit()
        num_students = int(num_students)

        # Read stress budget
        stress_budget = file.readline().strip()
        assert bool(re.match(r"(^\d+\.\d{1,3}$|^\d+$)", stress_budget))
        stress_budget = float(stress_budget)
        assert 0 < stress_budget < 100

        lines = file.read().splitlines()
        file.close()

        # Validate edge format
        for line in lines:
            tokens = line.split(" ")

            assert len(tokens) == 4
            assert tokens[0].isdigit() and int(tokens[0]) < num_students
            assert tokens[1].isdigit() and int(tokens[1]) < num_students
            assert bool(re.match(r"(^\d+\.\d{1,3}$|^\d+$)", tokens[2]))
            assert bool(re.match(r"(^\d+\.\d{1,3}$|^\d+$)", tokens[3]))
            assert 0 <= float(tokens[2]) < 100
            assert 0 <= float(tokens[3]) < 100

        # Build graph with happiness and stress edge attributes
        G = nx.parse_edgelist(lines, nodetype=int, data=(("happiness", float),("stress", float),))
        G.add_nodes_from(range(num_students))

        # Verify graph is complete and connected
        assert nx.is_connected(G)
        assert len(G.edges()) == num_students * (num_students - 1) // 2

        if max_size is not None:
            assert len(G) <= max_size

        return G, stress_budget


def write_input_file(G, stress_budget, path):
    """Write graph and stress budget to input file"""
    with open(path, "w") as file:
        num_students = len(G)
        lines = nx.generate_edgelist(G, data=["happiness", "stress"])
        file.write(str(num_students) + "\n")
        file.write(str(stress_budget) + "\n")
        file.writelines("\n".join(lines))
        file.close()


def read_output_file(path, G, s):
    """
    Parses and validates an output file.

    Args:
        path: Path to output file
        G: Input graph corresponding to this output
        s: Stress budget

    Returns:
        dict: Mapping of student to room

    Raises:
        AssertionError: If output file is malformed or invalid
    """
    with open(path, "r") as file:
        students_seen = set()
        rooms_seen = set()
        D = {}
        lines = file.read().splitlines()
        file.close()

        for line in lines:
            tokens = line.split()
            assert len(tokens) == 2

            # Validate student
            student = int(tokens[0])
            assert tokens[0].isdigit() and 0 <= student < len(G)
            assert student not in students_seen
            students_seen.add(student)

            # Validate room
            room = int(tokens[1])
            assert tokens[0].isdigit() and 0 <= room < len(G)
            rooms_seen.add(room)

            D[student] = room

        # Verify all students assigned and solution is valid
        assert len(students_seen) == len(G)
        assert utils.is_valid_solution(D, G, s, len(rooms_seen))

    return D


def write_output_file(D, path):
    """
    Writes a student-to-room mapping to an output file.

    Args:
        path: Path to output file
        D: Dictionary mapping student to room
    """
    with open(path, "w") as file:
        for student, room in D.items():
            file.write(str(student) + " " + str(room) + "\n")
        file.close()