def rooms_happiness(G, rooms, max_stress):
    def room_stats(members):
        happiness, stress = 0, 0
        for i in members:
            for j in members:
                if not i == j:
                    happiness += G.edges[i, j]['happiness']
                    stress += G.edges[i, j]['stress']
        return happiness, stress
    happ = 0
    for room in rooms:
        res = room_stats(room)
        if res[1] > max_stress:
            return None
        happ += res[0]
    return happ
def werk(G, max_stress):
    nodes = list(G.nodes)
    best_rooms = None
    best_happiness = -69
    best_k = -69
    n = len(nodes)
    for k in range(3, 4):
        print("k={}".format(k))
        for x in range(k ** n):
            rooms = [[] for _ in range(k)]
            for i in range(n):
                id = x % k
                x //= k
                rooms[id].append(nodes[i])
            happ = rooms_happiness(G, rooms, max_stress / k)
            if happ is not None and happ > best_happiness:
                best_rooms, best_happiness, best_k = rooms, happ, k
    rooms_dict = {}
    for i, room in enumerate(best_rooms):
        for student in room:
            rooms_dict[student] = i
    return rooms_dict, best_k
