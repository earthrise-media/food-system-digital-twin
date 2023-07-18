
import geopandas as gpd
from shapely.geometry import LineString
from tqdm import tqdm
import matplotlib.pyplot as plt
import time


# A utility file to plot the routes in a GeoJSON file


start = time.time()


# Function to swap coordinates
def swap_xy(line_string):
    return LineString([(y,x) for x,y in line_string.coords])


gdf = gpd.read_file("complete_routes.geojson")

# Apply the function to the 'geometry' column
geometry_list = gdf['geometry'].tolist()

# Initialize a progress bar
with tqdm(total=len(geometry_list), desc="Swapping Coordinates") as pbar:
    for i in range(len(geometry_list)):
        # Swap the coordinates
        geometry_list[i] = swap_xy(geometry_list[i])
        # Update the progress bar
        pbar.update()

# Convert the list back to a GeoSeries
gdf['geometry'] = gpd.GeoSeries(geometry_list)

# Create a plot
fig, ax = plt.subplots(figsize=(12, 10))

# Plot the geometry
gdf.plot(ax=ax, color="black", linewidth=0.15, edgecolor='black', alpha=0.075)
plt.axis('off')

# Show the plot
plt.show()

print(f"Time elapsed: {time.time() - start} seconds")