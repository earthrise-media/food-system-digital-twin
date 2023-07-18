import pandas as pd
import polyline
from shapely.geometry import LineString
import geopandas as gpd
from tqdm import tqdm


# A simple script to convert the polylines from OSRM to a GeoJSON file


routes_df = pd.read_csv("complete_routes.csv")
routes_df = routes_df.rename(columns={"geometry": "polyline"})

# Initialize progress bars
tqdm.pandas(desc="Decoding Polylines:")

routes_df["coordinates"] = routes_df['polyline'].progress_apply(polyline.decode)

tqdm.pandas(desc="Creating LineStrings:")
routes_df["geometry"] = routes_df["coordinates"].progress_apply(LineString)

routes_df = gpd.GeoDataFrame(routes_df, geometry="geometry")
routes_df.set_crs("WGS84", inplace=True)

routes_df.drop(["coordinates"], axis=1).to_file("complete_route.geojson", driver="GeoJSON")
# routes_df.drop(["coordinates"], axis=1).to_file("complete_routes.shp")

print("Done!")
