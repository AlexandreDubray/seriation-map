from dataclasses import dataclass

import pandas as pd
import geopandas as gpd
import os

from preprocess import get_unormalized_feature_dataframe
from sklearn.preprocessing import StandardScaler, QuantileTransformer, MinMaxScaler
from sklearn.preprocessing import normalize

@dataclass
class Config:

    traj_file: str
    regions_file: str
    poi_file: str
    radius: int

    def __post_init__(self):
        self.regions = load_gdf(self.regions_file)
        self.nb_regions = len(self.regions)

        l = [self.traj_file, self.regions_file]
        if self.poi_file is not None:
            l.append(self.poi_file)

        if not os.path.exists('cached'):
            os.makedirs('cached')

        feature_df_cache_name = '-'.join([os.path.splitext(os.path.basename(x))[0] for x in l])
        feature_df_cache_name = os.path.join('cached', feature_df_cache_name) + '.csv'

        if os.path.exists(feature_df_cache_name):
            self.pre_feature_df = pd.read_csv(feature_df_cache_name)
        else:
            traj_df = csv_to_gdf(self.traj_file)
            lab_regions = load_gdf(self.poi_file) if self.poi_file is not None else None
            self.pre_feature_df = get_unormalized_feature_dataframe(traj_df, self.regions, lab_regions)
            self.pre_feature_df.to_csv(feature_df_cache_name, index=False)

        self.features = list(self.pre_feature_df.columns)
        self.features = [x for x in self.features if x not in {'rid', 'tid', 'total'}]

        self._last_radius_feature = None
        self.feature_df = None
        self._solution_cache = {}
        self.scaler = QuantileTransformer()


    def _compute_feature_for_region(self, rids):
        sdf = self.pre_feature_df[self.pre_feature_df['rid'].isin(rids)].groupby('tid').agg({
            x: sum for x in self.features + ['total']
        })
        sdf = sdf[sdf['total'] != 0]
        for c in sdf.columns:
            sdf[c] /= sdf['total']
        return [sdf[c].mean() for c in self.features]


    def get_feature_df(self):
        if self.radius == self._last_radius_feature:
            return self.feature_df
        self._last_radius_feature = self.radius
        buf_regions = self.regions.copy()
        buf_regions.geometry = buf_regions.geometry.to_crs('epsg:27700').buffer(self.radius*1000).to_crs(self.regions.crs)

        op = 'covers' if self.radius == 0 else 'intersects'
        df = gpd.sjoin(self.regions, buf_regions , op=op).reset_index()
        df.rename(columns={'index_right': 'neighbors'}, inplace=True)
        df = df.groupby('index').agg({'neighbors': set})
        df[self.features] = [self._compute_feature_for_region(x) for x in df['neighbors']]
        df.drop(['neighbors'], axis=1, inplace=True)
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'rid'}, inplace=True)
        self.feature_df = df
        return self.feature_df

    def get_data(self):
        return self.get_feature_df()[self.features]

    def cache_solution(self, method, solution):
        try:
            self._solution_cache[method][self.radius] = solution
        except KeyError:
            self._solution_cache[method] = {self.radius: solution}

    def get_cache_solution(self, method):
        try:
            return self._solution_cache[method][self.radius]
        except KeyError:
            return None


config = None
def create_config(traj_file, region_file, poi_file, radius=0):
    global config
    config = Config(traj_file, region_file, poi_file, radius)


def get_config():
    return config


def csv_to_gdf(filename: str, lon: str='lon', lat: str='lat', timestamp: str='daytime'):
    df = pd.read_csv(filename, parse_dates=[timestamp])
    return gpd.GeoDataFrame(df, crs='epsg:4326', geometry=gpd.points_from_xy(df[lon], df[lat]))


def load_gdf(filename: str):
    return gpd.read_file(filename)
