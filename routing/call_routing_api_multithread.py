import requests
import polyline
from shapely.geometry import LineString
import pandas as pd
import geopandas as gpd
from multiprocessing import Pool
from tqdm import tqdm
import requests
from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry


# A script to query the OSRM API and get the routes to and from county centroids (as lat/lon pairs)
# This script is multithreaded to speed up the process
# You'll need to be running the OSRM API somewhere for this to work. We used a docker image on AWS.


session = None


def get_route_url(ip, coordinates):
    coords = ";".join([f"{coord[0]},{coord[1]}" for coord in coordinates])
    return f"http://{ip}:5000/route/v1/driving/{coords}?"


def setup_session():
    global session
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=5)
    session.mount("http://", adapter)
    session.mount("https://", adapter)


def query_osrm_route(ip, coordinates):
    global session
    if session is None:
        setup_session()

    url = get_route_url(ip, coordinates)
    r = session.get(url)

    if r.status_code == 200:

        res = r.json()
        routes = res['routes'][0]['geometry']  # TODO: Geometries aren't coming in request
        start_point = [res['waypoints'][0]['location'][1], res['waypoints'][0]['location'][0]]
        end_point = [res['waypoints'][1]['location'][1], res['waypoints'][1]['location'][0]]
        distance = res['routes'][0]['distance']
        duration = res['routes'][0]['duration']

        out = {'route': routes,  # Fix when we get geometries
               'start_point': start_point,
               'end_point': end_point,
               'distance': distance,
               "duration": duration,
               }

        return out

        return response.json()
    else:
        print(f"Error: {r.status_code}")
        return None


def process_counties(args):
    i, start_shape, end_shape = args

    start_coords = (start_shape["LON"], start_shape["LAT"])
    end_coords = (end_shape["LON"], end_shape["LAT"])

    # This IP address is the public IP address of the EC2 instance running the OSRM server
    result = query_osrm_route("54.165.254.227", [start_coords, end_coords])

    if result:
        return {
            "start_state": start_shape["STATEFP"],
            "start_name": start_shape["NAME"],
            "start_geoid": start_shape["GEOID"],
            "end_state": end_shape["STATEFP"],
            "end_name": end_shape["NAME"],
            "end_geoid": end_shape["GEOID"],
            "total_distance": result["distance"],
            "total_time": result["duration"],
            "geometry": result["route"]
            # "geometry": polyline_to_shapely_line_string(result["route"]),
        }


def main():

    dataframe_df = {"start_state": [], "start_name": [], "start_geoid": [], "end_state": [], "end_name": [],
                    "end_geoid": [], "total_distance": [], "total_time": [], "geometry": []}

    print("Reading in county shapes...")
    county_shapes = gpd.read_file("../unsynced-data/county_shapes/tl_2021_us_county.shp", bbox=(-130, 20, -60, 50)). \
        to_crs("WGS84")
    county_shapes = county_shapes
    print("Done reading in county shapes.")

    county_shapes["LAT"] = county_shapes["INTPTLAT"].astype(float)
    county_shapes["LON"] = county_shapes["INTPTLON"].astype(float)

    print("Creating tasks...")
    tasks = [(i, county_shapes.iloc[i], county_shapes.iloc[j])
             for i in range(len(county_shapes))
             for j in range(i, len(county_shapes))
             if i != j]

    with Pool(processes=15) as pool:
        results = list(tqdm(pool.imap(process_counties, tasks), total=len(tasks)))

    for result in results:
        if result:
            for key, value in result.items():
                dataframe_df[key].append(value)

    dataframe_df = pd.DataFrame(dataframe_df)
    dataframe_df.to_csv("complete_routes.csv", index=False)


if __name__ == "__main__":
    main()