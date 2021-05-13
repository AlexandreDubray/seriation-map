from dataclasses import dataclass
import os

import pandas as pd
import geopandas as gpd
import numpy as np

from smap.features import Feature

@dataclass
class Smap:

    traj_file: str
    regions_file: str
    labelized_regions_file: str
    features: list[Feature]
    radius: int
    id_field: str
    lat_field: str
    lon_field: str
    timestamp_field: str

    def __post_init__(self):
        self.regions = gpd.read_file(self.regions_file)

        self.labelized_regions = gpd.read_file(self.labelized_regions_file) if\
            self.labelized_regions_file is not None else None

        _script_dir = os.path.dirname(os.path.realpath(__file__))
        self._cache_dir = os.path.join(_script_dir, 'cached')
        if not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir)
        self._compute_pre_dataframe()

        self._last_radius_request = None

    def register_feature(self, f: Feature):
        self.features.append(f)

    def _get_cache_name(self):
        l = [self.traj_file, self.regions_file]
        if self.labelized_regions_file is not None:
            l.append(self.labelized_regions_file)
        l = [os.path.splitext(os.path.basename(x))[0] for x in l]
        l += [f.name for f in self.features]
        filename = '-'.join(l)
        return os.path.join(self._cache_dir, filename)

    def _compute_pre_dataframe(self, force=False):
        cached_file = self._get_cache_name()
        if not force and os.path.exists(cached_file):
            df = pd.read_csv(cached_file)
            return df

        # TODO: not memory efficient at all... Find a better way?
        # Maybe I should directly store the dataset as a geojson file?
        df = pd.read_csv(self.traj_file, parse_dates=[self.timestamp_field])
        df.sort_values(by=[self.id_field, self.timestamp_field], inplace=True)
        df['duration'] = (df[self.timestamp_field].shift(-1).fillna(df.loc[len(df)-1, self.timestamp_field]) -\
                          df[self.timestamp_field])/np.timedelta64(1, 's')
        switch = [df.loc[i, self.id_field] != df.loc[i+1, self.id_field] for i in range(len(df)-1)] + [False]
        df['duration'][switch] = 0
        df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[self.lon_field], df[self.lat_field]))
        df = gpd.sjoin(df, self.regions, op='within')
        df.rename(columns={'index_right': 'region_id'}, inplace=True)

        if self.labelized_regions is not None:
            df = gpd.sjoin(df, self.labelized_regions, op='within', how='left')
            df.drop(['index_right'], axis=1, inplace=True)
            df['label'].fillna('', inplace=True)

        df.reset_index(inplace=True)
        df.drop(['index'], axis=1, inplace=True)
        if self.labelized_regions is not None:
            for f in self.features:
                    f.compute(df, lat=self.lat_field, lon=self.lon_field, predefined_labels=df['label'])
        else:
            for f in self.features:
                    f.compute(df, lat=self.lat_field, lon=self.lon_field)

        cols_to_keep = ['id', 'region_id', 'duration'] + [f.name for f in self.features]
        df.drop(df.columns.difference(cols_to_keep), axis=1, inplace=True)

        categorical_features = [f for f in self.features if f.categorical]
        numerical_features = [f.name for f in self.features if not f.categorical]

        # Each numerical feature is averaged per id and per BSU
        if len(numerical_features) != 0:
            pre_df = df.groupby(['id', 'region_id']).agg({
                x: 'mean' for x in numerical_features
            })

        # Then we handle the catagorical feature separately and merge them afterward
        to_merge = list()
        indexed = df.set_index(['id', 'region_id'])
        for feat in categorical_features:
            to_merge.append(indexed[[feat.name, 'duration']].pivot_table(
                values='duration',
                index=indexed.index,
                columns=feat.name,
                aggfunc=sum))

        if len(numerical_features) != 0:
            pre_df = pd.concat([pre_df] + to_merge, axis=1)
        else:
            pre_df = pd.concat(to_merge, axis=1)
        pre_df.rename(columns={'level_0': 'id', 'level_1': 'region_id'})
        pre_df.fillna({c: 0.0 for c in pre_df.columns}, inplace=True)
        pre_df['id'], pre_df['region_id'] = zip(*pre_df.index)
        self.pre_feature_df = pre_df


    def _compute_features_for_bsus(self, rids):
        agg_funcs = {}
        for f in self.features:
            if f.categorical:
                for v in f.values:
                    agg_funcs[v] = sum
            else:
                agg_funcs[f.name] = 'mean'
        sdf = self.pre_feature_df[self.pre_feature_df['region_id'].isin(rids)].groupby('id').agg(agg_funcs)
        sdf['total'] = 0
        for f in self.features:
            if f.categorical:
                for v in f.values:
                    sdf['total'] += sdf[v]

        sdf = sdf[sdf['total'] != 0]

        for f in self.features:
            if f.categorical:
                sdf[f.values] /= sdf['total']
        row = []
        for f in self.features:
            if f.categorical:
                for v in f.values:
                    row.append(sdf[v].mean())
            else:
                row.append(sdf[f.name].mean())
        return row


    def get_feature_df(self):
        if self.radius == self._last_radius_request:
            return self.feature_df
        buf_regions = self.regions.copy()
        buf_regions.geometry = buf_regions.geometry.to_crs('epsg:27700').buffer(self.radius*1000).to_crs(self.regions.crs)
        op = 'covers' if self.radius == 0 else 'intersects'
        df = gpd.sjoin(self.regions, buf_regions, op=op).reset_index()
        df.rename(columns={'index_right': 'neighbors'}, inplace=True)
        df = df.groupby('index').agg({'neighbors': set})

        cols = []
        for f in self.features:
            if f.categorical:
                for v in f.values:
                    cols.append(v)
            else:
                cols.append(f.name)

        df[cols] = [self._compute_features_for_bsus(x) for x in df['neighbors']]
        df.drop(['neighbors'], axis=1, inplace=True)
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'region_id'}, inplace=True)
        df.fillna({c: 0.0 for c in df.columns}, inplace=True)
        self.feature_df = df
        self._last_radius_request = self.radius
        return df

smap = None
def create_smap(traj_file, region_file, poi_file, features, radius=0, id_field='id', lat='lat', lon='lon', timestamp='daytime'):
    global smap
    smap = Smap(traj_file, region_file, poi_file, features, radius, id_field, lat, lon, timestamp)

def get_smap():
    if smap is None:
        raise ValueError("Please first create a smap object")
    return smap
