
from pulp import *  # I usually don't like to do this, but EVERY example does, so maybe there's something to it
from tqdm import tqdm
import matplotlib as mpl
from matplotlib import pyplot as plt
import geopandas as gpd
import pandas as pd
import random as rd
import numpy as np
import time


# Script to solve the routing problem from supply to demand using OSRM and PuLP
# Note that a change in supply or demand will require a new solution to be generated
# Also note that the formulation may need to be changed if sum(supply) > sum(demand) or vice versa


rd.seed(1234)
np.random.seed(1234)

if __name__ == "__main__":

    state_names = pd.read_csv("state_names.txt", delimiter="|")

    # Note, this is unsynced data. It's not in the repo, but you can get it from the Census Bureau Website
    county_shapes = gpd.read_file("../unsynced-data/county_shapes/tl_2021_us_county.shp", bbox=(-130, 20, -60, 50)).to_crs("WGS84")
    county_shapes["NAME"] = county_shapes["NAME"].str.replace(" ", "").replace("-", "")
    county_shapes["STATEFP"] = county_shapes["STATEFP"].astype(int)
    county_shapes = county_shapes.merge(state_names, on="STATEFP")

    county_production = gpd.read_file("county-population-consumption-production-scaled.geojson")
    county_production.rename({"geoid": "GEOID", "state_name": "STATE_NAME", "name": "NAME"}, axis=1, inplace=True)
    county_production["GEOID"] = county_production["statefp"].astype(str) + county_production["countyfp"].astype(str)
    county_production["NAME"] = county_production["NAME"].str.replace(" ", "").replace("-", "")

    # Routes are one-way, so we need to duplicate them
    osrm_routes = pd.read_csv("complete_routes.csv")
    osrm_routes_copy = osrm_routes.copy()
    osrm_routes_copy["start_geoid"] = osrm_routes["end_geoid"]
    osrm_routes_copy["end_geoid"] = osrm_routes["start_geoid"]
    osrm_routes = pd.concat([osrm_routes, osrm_routes_copy], axis=0)

    county_pop = gpd.read_file("../synced-data/population_counties_conus.geojson")
    county_pop.rename({"statefp": "STATEFP", "state_name": "STATE_NAME", "name": "NAME"}, axis=1, inplace=True)
    county_pop["NAME"] = county_pop["namelsad"].str.replace(" County", "").str.replace(" Parish", "").str.replace(" ", "***")
    county_pop = county_pop.drop(["geometry"], axis=1)

    supply_columns = [col for col in county_production.columns if "kcal_produced" in col]
    supply_counts = {col: (county_production[col] > 0).astype(int).sum() for col in county_production.columns if "kcal_produced" in col}
    supply_columns = sorted(supply_columns, key=lambda x: supply_counts[x], reverse=True)
    print(f"Supply columns: {supply_columns}")

    demand_columns = [col for col in county_production.columns if "total_kcal_consumed" in col]
    demand_counts = {col: (county_production[col] > 0).astype(int).sum() for col in county_production.columns if "total_kcal_consumed" in col}
    demand_columns = sorted(demand_columns, key=lambda x: demand_counts[x], reverse=True)

    main_dataset = county_shapes.merge(county_production[["NAME", "STATE_NAME", "GEOID"] + supply_columns + demand_columns], on=["GEOID"])
    main_dataset.columns = [col.replace("_x", "") for col in main_dataset.columns]  # TODO: Clean this up
    main_dataset = gpd.GeoDataFrame(main_dataset)

    # DF That can be used to debug production / demand
    # production_debug_df = {"Crop": [], "Total Production": [], "Total Demand": [], "Total Production / Total Demand": []}
    #
    # for crop in tqdm(supply_columns):
    #
    #     crop_name = crop.split("_")[-1]
    #     demand_col = f"total_kcal_consumed_{crop_name}"
    #
    #     total_production = main_dataset[crop].sum()
    #     total_demand = main_dataset[demand_col].sum()
    #
    #     production_debug_df["Crop"].append(crop_name)
    #     production_debug_df["Total Production"].append(total_production)
    #     production_debug_df["Total Demand"].append(total_demand)
    #     production_debug_df["Total Production / Total Demand"].append(total_production / total_demand)
    #
    # production_debug_df = pd.DataFrame(production_debug_df)
    # production_debug_df.to_csv("production_debug.csv", index=False)

    for crop in tqdm(supply_columns):

        crop_name = crop.split("_")[-1]
        demand_col = f"total_kcal_consumed_{crop_name}"

        try:
            crop_df = main_dataset[["GEOID", "NAME", "geometry", crop, demand_col, "INTPTLAT", "INTPTLON"]] #, "total_population", ]]

            crop_df.drop(["geometry"], axis=1).to_csv("crop_df.csv")

            crop_df["LAT"] = crop_df["INTPTLAT"].astype(float)
            crop_df["LON"] = crop_df["INTPTLON"].astype(float)
            crop_df["centroids"] = crop_df.geometry.centroid
            crop_df["NAME"] = crop_df["NAME"].str.replace(" ", "")
            crop_df["GEOID"] = crop_df["GEOID"].astype(str)

            # If you want to subset the data, do it here. It should be done in the input data however.
            supply_counties = crop_df[crop_df[crop] > 0]#.sort_values(by=crop, ascending=False).iloc[:20]
            demand_counties = crop_df

            print("Total Supply", supply_counties[crop].sum())
            print("Total Demand", demand_counties[demand_col].sum())

            supply_names = [f"supply_{name}_{geoid}" for name, geoid in zip(supply_counties["NAME"],
                                                                            supply_counties["GEOID"])]
            demand_names = [f"demand_{name}_{geoid}" for name, geoid in zip(demand_counties["NAME"],
                                                                            demand_counties["GEOID"])]

            supply_amounts = {GEOID: supply_counties[supply_counties["GEOID"] == GEOID.split("_")[-1]][crop].values[0]
                              for GEOID in supply_names}
            demand_amounts = {GEOID: demand_counties[demand_counties["GEOID"] == GEOID.split("_")[-1]][demand_col].values[0]
                              for GEOID in demand_names}

            supply_locations = [[lat, lon] for lat, lon in zip(supply_counties["LAT"], supply_counties["LON"])]
            demand_locations = [[lat, lon] for lat, lon in zip(demand_counties["LAT"], demand_counties["LON"])]

            # Grab the costs from the osrm-routing data
            costs = []
            missing_count = 0
            for supply_loc in tqdm(supply_counties["GEOID"].values):
                supply_loc = int(supply_loc)
                supply_df = osrm_routes[osrm_routes["start_geoid"] == supply_loc]

                current_costs = []
                for demand_loc in demand_counties["GEOID"].values:
                    demand_loc = int(demand_loc)

                    if supply_loc != demand_loc:

                        distance = supply_df[supply_df["end_geoid"] == demand_loc]["total_distance"].values

                        # If there is no distance, then we need to calculate it ourselves
                        if len(distance) == 0:
                            missing_count += 1
                            supply_coords = [supply_counties[supply_counties["GEOID"] == supply_loc]["LAT"],
                                             supply_counties[supply_counties["GEOID"] == supply_loc]["LON"]]
                            demand_coords = [demand_counties[demand_counties["GEOID"] == demand_loc]["LAT"],
                                             demand_counties[demand_counties["GEOID"] == demand_loc]["LON"]]

                            # Linear Distance Calculation
                            distance = np.linalg.norm(np.array(supply_coords) - np.array(demand_coords))

                        # OSRM Distance
                        else:
                            distance = distance[0]
                    elif supply_loc == demand_loc:
                        distance = 0

                    current_costs.append(distance)

                costs.append(current_costs)

            # print("Missing", missing_count)

            # The cost data is made into a dictionary
            costs = makeDict([supply_names, demand_names], costs, 0)

            # Creates the 'prob' variable to contain the problem data
            prob = LpProblem("Food Distribution Problem", LpMinimize)

            Routes = [(w, b) for w in supply_names for b in demand_names]

            # A dictionary called 'Vars' is created to contain the referenced variables(the routes)
            vars = LpVariable.dicts("Route", (supply_names, demand_names), 0, None, LpContinuous)

            # The objective function is added to 'prob' first
            prob += (
                lpSum([vars[w][b] * costs[w][b] for (w, b) in Routes]),
                "Sum_of_Transportation_Costs",
            )

            # Use these constraints if demand < supply. We need to fill ALL of the demand while using only the supply that we need
            # The supply maximum constraints are added to prob for each supply node (warehouse)
            for w in supply_names:
                prob += (
                    lpSum([vars[w][b] for b in demand_names]) <= supply_amounts[w],
                    f"Sum_of_Products_out_of_Supply_{w}",
                )

            # The demand minimum constraints are added to prob for each demand node (bar)
            print("ADDING DEMAND CONSTRAINTS")
            for b in demand_names:
                prob += (
                    lpSum([vars[w][b] for w in supply_names]) == demand_amounts[b],
                    f"Sum_of_Products_into_Demand{b}",
                )
                print("DONE", b)

            ##################################

            # Use these constraints if demand > supply. We need to use ALL of the supply while filling as much demand as possible
            # # The supply maximum constraints are added to prob for each supply node (warehouse)
            # for w in supply_names:
            #     prob += (
            #         lpSum([vars[w][b] for b in demand_names]) == supply_amounts[w],
            #         f"Sum_of_Products_out_of_Supply_{w}",
            #     )
            #
            # # The demand minimum constraints are added to prob for each demand node (bar)
            # print("ADDING DEMAND CONSTRAINTS")
            # for b in demand_names:
            #     prob += (
            #         lpSum([vars[w][b] for w in supply_names]) <= demand_amounts[b],
            #         f"Sum_of_Products_into_Demand{b}",
            #     )
            #     print("DONE", b)

            ##################################

            # The problem data can be written to an .lp file
            # prob.writeLP("TestDistProblem.lp")

            # The problem is solved using PuLP's choice of Solver
            prob.solve(PULP_CBC_CMD(msg=True))

            # Prepare a list for storing results
            results_list = []

            for v in prob.variables():
                if v.varValue > 0:
                    # This can be fragile. It assumes that the supply and demand names are in the original format
                    # that we used. If you change the format, you will need to change this.
                    if v.name.split("_")[3].lower() == v.name.split("_")[3]:  # Check if item at location 3 is a number
                        supply_index = 3
                    else:
                        supply_index = 4

                    supply_loc = v.name.split("_")[supply_index]
                    demand_loc = v.name.split("_")[-1]
                    results_list.append([supply_loc, demand_loc, v.varValue])

            # This section saves the data in two ways:
            # 1. As a DataFrame, or the "Long" format
            # 2. As a pivoted DataFrame, or the "Wide" format

            # Create a DataFrame from the results list
            results_df = pd.DataFrame(results_list, columns=['Supply', 'Demand', 'Value'])
            results_df.to_csv(f"./routing_solves/long/{crop}_results_df.csv", index=False)

            # Pivot the DataFrame to get the desired format
            pivoted_results_df = results_df.pivot(index='Supply', columns='Demand', values='Value')

            # Save the pivoted DataFrame to a CSV file
            pivoted_results_df.to_csv(f"./routing_solves/pivoted/{crop}_results_pivoted.csv")

            print("DONE", crop)

            # # A quick sketch to make sure things are working correctly
            # # This is not necessary for the actual solving but useful in debugging
            # from matplotlib import pyplot as plt
            #
            # fig, ax = plt.subplots()
            #
            # routing_connections = []
            # for var in prob.variables():
            #     if var.varValue > 0:
            #         if var.name.split("_")[3].lower() == v.name.split("_")[3]:  # Check if item at location 3 is a number
            #             supply_index = 3
            #         else:
            #             supply_index = 4
            #         supply_geoid = var.name.split("_")[3]
            #         demand_geoid = var.name.split("_")[-1]
            #
            #         routing_connections.append([supply_geoid, demand_geoid])
            #
            # supply_to_demand = {}
            # for connection in routing_connections:
            #     if connection[0] not in supply_to_demand:
            #         supply_to_demand[connection[0]] = [connection[1]]
            #     else:
            #         supply_to_demand[connection[0]].append(connection[1])
            #
            # cat20_colormap = mpl.colormaps["tab20"]
            # colors = cat20_colormap.colors
            #
            # cnt = 0
            # supply_to_demand = {}
            # for row in pivoted_results_df.index:
            #     supply_to_demand[row] = []
            #     for col in pivoted_results_df.columns:
            #         if pivoted_results_df.loc[row, col] > 0:
            #             supply_to_demand[row].append(col)
            #
            # for supply_geoid in supply_to_demand:
            #     if len(supply_to_demand[supply_geoid]) > 0:
            #         demand_counties[demand_counties["GEOID"].isin(supply_to_demand[supply_geoid])].plot(ax=ax,
            #                                                                                             color=colors[cnt % len(colors)], alpha=1)
            #
            #     supply_counties[supply_counties["GEOID"] == supply_geoid].plot(
            #         ax=ax, marker="*", color=colors[cnt % len(colors)], edgecolor="black", linewidth=2,  markersize=75, zorder=10)
            #     cnt += 1
            #
            # county_shapes.boundary.plot(ax=ax, color="black", edgecolor="black", linewidth=0.1)
            #
            # plt.axis('off')
            # plt.savefig(f"total{crop}_linopt_test_counties.png", dpi=1200)
            # # plt.close()

        except Exception as e:
            with open('app.log', 'a') as f:
                f.write(str(e) + '\n')
                f.write(f"Error with {crop}" + '\n')
            continue