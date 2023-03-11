
from pulp import *  # I usually don't like to do this, but EVERY example does, so maybe there's something to it
from tqdm import tqdm
from matplotlib import pyplot as plt
import random as rd
import numpy as np
import time

rd.seed(1234)
np.random.seed(1234)

problem_size = 30

times = []
for problem_size in tqdm(range(5000)):
    start = time.time()

    supply_amount_ranges = (100, 1000)
    demand_amount_ranges = (100, 500)
    area_range = (0, 10000)

    # Create our nodes
    supply_names = [f"supply_{i}" for i in range(problem_size)]
    demand_names = [f"demand_{i}" for i in range(problem_size)]

    # Creates a dictionary for the number of units of supply for each supply node
    supply_amounts = {name: rd.randint(supply_amount_ranges[0], supply_amount_ranges[1]) for name in supply_names}

    # Creates a dictionary for the number of units of demand for each demand node
    demand_amounts = {name: rd.randint(demand_amount_ranges[0], demand_amount_ranges[1]) for name in demand_names}

    supply_locations = [(rd.randint(area_range[0], area_range[1]),
                         rd.randint(area_range[0], area_range[1])) for i in range(problem_size)]
    demand_locations = [(rd.randint(area_range[0], area_range[1]),
                         rd.randint(area_range[0], area_range[1])) for i in range(problem_size)]


    # Calculate the Euclidean distances as the Cost
    costs = []
    for supply_loc in supply_locations:
        current_costs = []
        for demand_loc in demand_locations:
            distance = np.linalg.norm(np.array(supply_loc) - np.array(demand_loc))
            current_costs.append(distance)
        costs.append(current_costs)


    # The cost data is made into a dictionary
    costs = makeDict([supply_names, demand_names], costs, 0)

    # Creates the 'prob' variable to contain the problem data
    prob = LpProblem("Beer Distribution Problem", LpMinimize)

    # Creates a list of tuples containing all the possible routes for transport
    Routes = [(w, b) for w in supply_names for b in demand_names]

    # A dictionary called 'Vars' is created to contain the referenced variables(the routes)
    vars = LpVariable.dicts("Route", (supply_names, demand_names), 0, None, LpInteger)

    # The objective function is added to 'prob' first
    prob += (
        lpSum([vars[w][b] * costs[w][b] for (w, b) in Routes]),
        "Sum_of_Transporting_Costs",
    )

    # The supply maximum constraints are added to prob for each supply node (warehouse)
    for w in supply_names:
        prob += (
            lpSum([vars[w][b] for b in demand_names]) <= supply_amounts[w],
            f"Sum_of_Products_out_of_Supply_{w}",
        )

    # The demand minimum constraints are added to prob for each demand node (bar)
    for b in demand_names:
        prob += (
            lpSum([vars[w][b] for w in supply_names]) >= demand_amounts[b],
            f"Sum_of_Products_into_Demand{b}",
        )

    # The problem data is written to an .lp file
    # prob.writeLP("TestDistProblem.lp")

    # The problem is solved using PuLP's choice of Solver
    # print("Solving Problem...")
    prob.solve(PULP_CBC_CMD(msg=0))
    # print("Solved Problem.")

    times.append(time.time() - start)

plt.plot(times)
plt.title("Runtime by Problem Size")
plt.savefig("runtime_by_problem_size.png")

    # # The status of the solution is printed to the screen
    # print("Status:", LpStatus[prob.status])
    #
    # # Each of the variables is printed with it's resolved optimum value
    # for v in prob.variables():
    #     print(v.name, "=", v.varValue)
    #
    # # The optimised objective function value is printed to the screen
    # print("Total Cost of Transportation = ", value(prob.objective))

    # # A quick sketch to make sure things are working correctly
    # from matplotlib import pyplot as plt
    #
    # supply_x = [loc[0] for loc in supply_locations]
    # supply_y = [loc[1] for loc in supply_locations]
    #
    # demand_x = [loc[0] for loc in demand_locations]
    # demand_y = [loc[1] for loc in demand_locations]
    #
    # plt.scatter(supply_x, supply_y)
    # plt.scatter(demand_x, demand_y)
    # plt.legend(["Supply", "Demand"])
    #
    # routing_connections = []
    # for var in prob.variables():
    #     if var.varValue > 0:
    #         supply_index = int(var.name.split("_")[2])
    #         demand_index = int(var.name.split("_")[-1])
    #
    #         routing_connections.append([supply_index, demand_index])
    #
    # for connection in routing_connections:
    #     supply_point = supply_locations[connection[0]]
    #     demand_point = demand_locations[connection[1]]
    #
    #     xs = [supply_point[0], demand_point[0]]
    #     ys = [supply_point[1], demand_point[1]]
    #
    #     print(supply_point, demand_point)
    #     plt.plot(xs, ys, color="green")
    #
    #
    # for i in range(problem_size):
    #     supply_point = supply_locations[i]
    #     plt.text(supply_point[0], supply_point[1], str(supply_amounts[f"supply_{i}"]))
    #
    #     demand_point = demand_locations[i]
    #     plt.text(demand_point[0], demand_point[1], str(demand_amounts[f"demand_{i}"]))
    #
    # plt.show()
