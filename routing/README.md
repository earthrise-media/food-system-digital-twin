# Routing

These files facilitate the solving of the food distribution problem. In general, we assume:

1. We are trying to satisfy all demand over a year while minimizing total transportation costs.
2. Every county has a demand for different types of food
3. Many counties have a supply of different types of food
4. The costs of transporting food from one county to another are calculated from OpenStreetMap using OSRM

## Files

### county_routing.py

The main file for solving the routing problem. This file contains the PuLP model and the functions for solving the
routing problem. The formulation is given below:

Minimize Z = sum(c_ij * x_ij) for all i in I, j in J  (Objective function)  
Subject to:
    
    sum(x_ij) for all j in J <= s_i for all i in I  (Supply constraint)  
    sum(x_ij) for all i in I >= d_j for all j in J  (Demand constraint)  
    x_ij >= 0 for all i in I, j in J               (Non-negativity)  

Given:  
A set I of supply nodes, indexed by i.  
A set J of demand nodes, indexed by j.  
s_i is the supply available at node i.  
d_j is the demand at node j.  
c_ij is the cost (distance, time, money, etc.) to ship one unit from node i to node j.  
Decision variable x_ij represents the amount to be shipped from i to j.

Where:  
The objective function Z is the total cost of shipping, which we want to minimize.  
The first set of constraints ensures that we do not ship more than the available supply from each supply node.  
The second set of constraints ensures that we meet the demand at each demand node.  
The last set of constraints ensures that we do not ship a negative amount.  

### call_routing_api_multithread.py

This file contains the functions for calling the OSRM API. It is multithreaded to speed up the process.
You will have to be running the OSRM server for this to work. We used a docker image on AWS using the tutorial linked
[here](https://gist.github.com/akiatoji/42c04598535e823637ba18a54747fca5).

### convert_polyline_routes_to_geojson.py

This file contains the functions for converting the routes from the OSRM API to GeoJSON format.

### plot_routes.py

A utility file to help plot the routes on a map.