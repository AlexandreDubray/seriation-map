import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist
from seriate import seriate
import plotly.express as px

import sys

from preprocess import add_fields
from normalization import *


def read_csv(filename, lon, lat, timestamp):
    df = pd.read_csv(filename, parse_dates=[timestamp])
    return gpd.GeoDataFrame(df, crs='epsg:4326', geometry=gpd.points_from_xy(df['lon'], df['lat']))


def load_file(filename, lon='lon', lat='lat', timestamp='daytime'):
    if filename.endswith('.csv'):
        return read_csv(filename, lon, lat, timestamp)
    return gpd.read_file(filename)


if __name__ == '__main__':
    print('Loading data set')
    df = load_file(sys.argv[1])
    print('Adding fields for seriation')
    add_fields(df)
    print('Loading grid')
    grid = load_file(sys.argv[2])
    df = gpd.sjoin(df, grid, op='within')
    df.rename(columns={'index_right': 'region_id'}, inplace=True)
    df['region_id'].fillna(-1)

    feature_df = df[df['region_id'] != -1].groupby('region_id').agg({
        'distance': sum,
        'duration': sum,
        'velocity': np.mean,
    })

    norm_df = min_max_norm(feature_df)

    order = seriate(pdist(norm_df), timeout=0)

    px.choropleth_mapbox(norm_df, geojson=grid, locations=[x for x in range(len(norm_df))],
                         color=order, mapbox_style='carto-positron',
                         opacity=0.5).show()
