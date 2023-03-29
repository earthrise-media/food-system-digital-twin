# this function takes a dataframe and a list of prefixes to transform to percentile values for ins
import geopandas as gpd
import pandas as pd
def df_to_percentile(df, prefix):
    for p in prefix:
        for col in df.columns:
            if col.startswith(p):
                df[col] = df[col] / df[col].max()
    return df