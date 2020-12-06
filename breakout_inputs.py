import random as rand

def generate_inputs(num_students):
    print(num_students)
    stress_budget = rand.uniform(0.1,99.9)
    print("{:.3f}".format(stress_budget))
    for i in range(num_students):
        for j in range(i + 1, num_students):
            happiness = rand.uniform(0.1, 50.0)
            stress = rand.uniform(5.0, 10.0)
            print(i, j, "{:.3f}".format(happiness), "{:.3f}".format(stress))
