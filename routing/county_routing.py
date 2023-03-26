
from pulp import *  # I usually don't like to do this, but EVERY example does, so maybe there's something to it
from tqdm import tqdm
from matplotlib import pyplot as plt
import geopandas as gpd
import random as rd
import numpy as np
import time

rd.seed(1234)
np.random.seed(1234)

if __name__ == "__main__":
    supply_amount_ranges = (1600, 1600)
    demand_amount_ranges = (10, 10)

    county_data = gpd.read_file("county_shapes/tl_2021_us_county.shp", bbox=(-130, 20, -60, 50)).to_crs("WGS84")

    county_data["LAT"] = county_data["INTPTLAT"].astype(float)
    county_data["LON"] = county_data["INTPTLON"].astype(float)
    county_data["centroids"] = county_data.geometry.centroid

    supply_counties = county_data.sample(20)
    demand_counties = county_data[~county_data.index.isin(supply_counties.index)]

    print(county_data.columns)

    supply_names = [f"supply_{name}_{geoid}" for name, geoid in zip(supply_counties["NAME"], supply_counties["GEOID"])]
    demand_names = [f"demand_{name}_{geoid}" for name, geoid in zip(demand_counties["NAME"], demand_counties["GEOID"])]

    supply_amounts = {name: rd.randint(supply_amount_ranges[0], supply_amount_ranges[1]) for name in supply_names}
    demand_amounts = {name: rd.randint(demand_amount_ranges[0], demand_amount_ranges[1]) for name in demand_names}

    supply_locations = [[lat, lon] for lat, lon in zip(supply_counties["LAT"], supply_counties["LON"])]
    demand_locations = [[lat, lon] for lat, lon in zip(demand_counties["LAT"], demand_counties["LON"])]


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
    print("Solving Problem...")
    start = time.time()

    print("Pre-Solve Size", sys.getsizeof(prob))
    prob.solve(PULP_CBC_CMD(msg=0))
    print("Post-Solve Size", sys.getsizeof(prob))
    print(f"Solved Problem in {(time.time() - start)/60} minutes.")


    # The status of the solution is printed to the screen
    print("Status:", LpStatus[prob.status])

    # Each of the variables is printed with it's resolved optimum value
    # for v in prob.variables():
    #     print(v.name, "=", v.varValue)

    # The optimised objective function value is printed to the screen
    print("Total Cost of Transportation = ", value(prob.objective))

    # A quick sketch to make sure things are working correctly
    from matplotlib import pyplot as plt

    fig, ax = plt.subplots()

    supply_x = [loc[0] for loc in supply_locations]
    supply_y = [loc[1] for loc in supply_locations]

    demand_x = [loc[0] for loc in demand_locations]
    demand_y = [loc[1] for loc in demand_locations]

    # ax.scatter(supply_y, supply_x, zorder=5, color="blue")
    # ax.scatter(demand_y, demand_x, zorder=3, color="orange")
    # ax.legend(["Supply", "Demand"])

    routing_connections = []
    for var in prob.variables():
        if var.varValue > 0:
            supply_geoid = var.name.split("_")[3]
            demand_geoid = var.name.split("_")[-1]

            routing_connections.append([supply_geoid, demand_geoid])

    supply_to_demand = {}
    for connection in routing_connections:
        if connection[0] not in supply_to_demand:
            supply_to_demand[connection[0]] = []
        else:
            supply_to_demand[connection[0]].append(connection[1])

    colors = ["green", "black", "pink", "purple", "red", "grey", "yellow", "blue", "orange"]

    cnt = 0
    for supply_geoid in supply_to_demand:
        demand_counties[demand_counties["GEOID"].isin(supply_to_demand[supply_geoid])]["centroids"].plot(ax=ax,
                                                                                                         color=colors[cnt % len(colors)], alpha=1)
        supply_counties[supply_counties["GEOID"] == supply_geoid]["centroids"].plot(
            ax=ax, marker="*", color=colors[cnt % len(colors)], edgecolor="orange", linewidth=0.25,  markersize=75, zorder=10)
        cnt += 1

    plt.axis('off')
    plt.savefig(f"linopt_test_counties.png")
    plt.close()
