
import geopandas as gpd
import matplotlib.pyplot as plt
import os
from tqdm import tqdm

# Quick script to visualize the supply data

# Requires the following files:
#  * cdl-codes.csv
#  * county_crops-v1.gpkg

county_crops = gpd.read_file("./supply_data/county-crops-v1.gpkg", bbox=(-130, 20, -60, 50))
cdl_codes = gpd.read_file("./supply_data/cdl-codes.csv")
cdl_codes.dropna(subset=["Class_Names"], inplace=True)

county_crops.drop(["geometry"], axis=1).iloc[:10].to_csv("county_crops_excerpt.csv")

if not os.path.exists("./crop_plots"):
    os.mkdir("./crop_plots")

for crop_code in tqdm(cdl_codes["crop_code"].unique()):
    if crop_code in county_crops.columns:
        crop_name = cdl_codes[cdl_codes["crop_code"] == crop_code]["Class_Names"].iloc[0]
        crop_name = crop_name.replace("/", "_")

        county_crops.plot(column=crop_code)
        plt.axis("off")
        plt.title(crop_name)
        plt.savefig(f"./crop_plots/{crop_name}.png", dpi=600)
        plt.close()