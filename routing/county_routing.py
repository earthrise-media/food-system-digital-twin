
from pulp import *  # I usually don't like to do this, but EVERY example does, so maybe there's something to it
from tqdm import tqdm
from matplotlib import pyplot as plt
import geopandas as gpd
import pandas as pd
import random as rd
import numpy as np
import time

rd.seed(1234)
np.random.seed(1234)

if __name__ == "__main__":

    # supply_amount_ranges = (1600, 1600)
    # demand_amount_ranges = (10, 10)

    county_shapes = gpd.read_file("../unsynced-data/county_shapes/tl_2021_us_county.shp", bbox=(-130, 20, -60, 50)).to_crs("WGS84")
    county_production = gpd.read_file("../unsynced-data/county_production-v1.geojson")

    county_pop = pd.read_csv("../synced-data/county_population.csv")
    county_pop.rename({"STATE": "STATEFP", "STNAME": "State", "CTYNAME": "NAME"}, axis=1, inplace=True)
    county_pop["NAME"] = county_pop["NAME"].str.replace(" County", "").str.replace(" Parish", "")
    county_pop = county_pop[county_pop["COUNTY"] != 0]  # States are County 0

    state_crop_columns = [col for col in county_production.columns if "kcal_state_crop" in col]
    state_crop_counts = {col: (county_production[col] > 0).astype(int).sum() for col in county_production.columns if "kcal_state_crop" in col}
    state_crop_columns = sorted(state_crop_columns, key=lambda x: state_crop_counts[x], reverse=True)

    main_dataset = county_shapes.merge(county_production[["GEOID", "State"] + state_crop_columns], on="GEOID")
    main_dataset = main_dataset.merge(county_pop[["ESTIMATESBASE2020", "State", "NAME"]], on=["State", "NAME"])  # Lose LA Here
    main_dataset.columns = [col.replace("_x", "") for col in main_dataset.columns]  # TODO: Clean this up
    main_dataset = gpd.GeoDataFrame(main_dataset)

    main_dataset.drop("geometry", axis=1).to_csv("xerpt.csv")

    total_demand = main_dataset["ESTIMATESBASE2020"].sum()*2144*365

    print(county_production.columns)

    for crop in ["kcal_state_crop_1"]:# state_crop_columns:

        crop_df = main_dataset[["GEOID", "NAME", "geometry", crop, "ESTIMATESBASE2020", "INTPTLAT", "INTPTLON"]]

        crop_df["LAT"] = crop_df["INTPTLAT"].astype(float)
        crop_df["LON"] = crop_df["INTPTLON"].astype(float)
        crop_df["centroids"] = crop_df.geometry.centroid
        crop_df["NAME"] = crop_df["NAME"].str.replace(" ", "")
        crop_df["GEOID"] = crop_df["GEOID"].astype(str)

        supply_counties = crop_df[crop_df[crop] > 0] # .sort_values(by=crop, ascending=False).iloc[:150]
        demand_counties = crop_df

        # assert False

        print("Number of supply counties", len(supply_counties))

        supply_adjustment = (total_demand / supply_counties[crop].sum())

        print(county_shapes.columns)

        supply_names = [f"supply_{name}_{geoid}" for name, geoid in zip(supply_counties["NAME"], supply_counties["GEOID"])]
        demand_names = [f"demand_{name}_{geoid}" for name, geoid in zip(demand_counties["NAME"], demand_counties["GEOID"])]

        supply_amounts = {GEOID: supply_counties[supply_counties["GEOID"] == GEOID.split("_")[-1]][crop].values[0]*supply_adjustment + 1 for GEOID in supply_names}
        # Print total supply
        print("Supply", sum(supply_amounts.values()))

        # Demand is 2144kcal per person per day (so mult again by 365 to get a year)
        demand_amounts = {GEOID: demand_counties[demand_counties["GEOID"] == GEOID.split("_")[-1]]["ESTIMATESBASE2020"].values[0]*2144*365 for GEOID in demand_names}
        print("Demand", sum(demand_amounts.values()))

        supply_locations = [[lat, lon] for lat, lon in zip(supply_counties["LAT"], supply_counties["LON"])]
        demand_locations = [[lat, lon] for lat, lon in zip(demand_counties["LAT"], demand_counties["LON"])]

        # print(max(demand_amounts.values()))
        # 7836562883040
        # print(min(demand_amounts.values()))
        # 50083840

        # Calculate the Euclidean distances as the Cost
        costs = []
        cost_df_dict = {"Supply_GEOID": [], "Demand_GEOID": [], "Cost": []}
        for supply_loc in supply_locations:

            current_costs = []
            for demand_loc in demand_locations:

                distance = np.linalg.norm(np.array(supply_loc) - np.array(demand_loc))
                current_costs.append(distance)

            costs.append(current_costs)
        # frac_to_keep_param = 0.1
        cost_df = pd.DataFrame(cost_df_dict)

        # The cost data is made into a dictionary
        costs = makeDict([supply_names, demand_names], costs, 0)

        # Creates the 'prob' variable to contain the problem data
        prob = LpProblem("Food Distribution Problem", LpMinimize)

        Routes = [(w, b) for w in supply_names for b in demand_names]
        print("Route Count", len(Routes))

        # A dictionary called 'Vars' is created to contain the referenced variables(the routes)
        vars = LpVariable.dicts("Route", (supply_names, demand_names), 0, None, LpContinuous)

        # The objective function is added to 'prob' first
        prob += (
            lpSum([vars[w][b] * costs[w][b] for (w, b) in Routes]),
            "Sum_of_Transportation_Costs",
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
        prob.solve(PULP_CBC_CMD(msg=True))
        print(f"Solved Problem in {(time.time() - start)/60} minutes.")


        # The status of the solution is printed to the screen
        print("Status:", LpStatus[prob.status])

        # Prepare a list for storing results
        results_list = []

        for v in prob.variables():
            if v.name.split("_")[3].lower() == v.name.split("_")[3]:  # Check if item at location 3 is a number
                supply_index = 3
            else:
                supply_index = 4

            supply_loc = v.name.split("_")[3]
            demand_loc = v.name.split("_")[-1]
            results_list.append([supply_loc, demand_loc, v.varValue])

        # Create a DataFrame from the results list
        results_df = pd.DataFrame(results_list, columns=['Supply', 'Demand', 'Value'])
        results_df.to_csv(f"{crop}_results_df.csv")

        # Pivot the DataFrame to get the desired format
        pivoted_results_df = results_df.pivot(index='Supply', columns='Demand', values='Value')

        # Save the pivoted DataFrame to a CSV file
        pivoted_results_df.to_csv(f"{crop}_results_pivoted.csv")

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
                if v.name.split("_")[3].lower() == v.name.split("_")[3]:  # Check if item at location 3 is a number
                    supply_index = 3
                else:
                    supply_index = 4
                supply_geoid = var.name.split("_")[3]
                demand_geoid = var.name.split("_")[-1]

                routing_connections.append([supply_geoid, demand_geoid])

        supply_to_demand = {}
        for connection in routing_connections:
            if connection[0] not in supply_to_demand:
                supply_to_demand[connection[0]] = [connection[1]]
            else:
                supply_to_demand[connection[0]].append(connection[1])

        import matplotlib as mpl

        cat20_colormap = mpl.colormaps["tab20"]

        colors = cat20_colormap.colors

        cnt = 0
        for supply_geoid in supply_to_demand:
            if len(supply_to_demand[supply_geoid]) > 0:
                demand_counties[demand_counties["GEOID"].isin(supply_to_demand[supply_geoid])].plot(ax=ax,
                                                                                                    color=colors[cnt % len(colors)], alpha=1)

            supply_counties[supply_counties["GEOID"] == supply_geoid].plot(
                ax=ax, marker="*", color=colors[cnt % len(colors)], edgecolor="black", linewidth=2,  markersize=75, zorder=10)
            cnt += 1

        county_shapes.boundary.plot(ax=ax, color="black", edgecolor="black", linewidth=0.1)

        # plt.axis('off')
        plt.savefig(f"total{crop}_linopt_test_counties.png", dpi=1200)
        # plt.close()
