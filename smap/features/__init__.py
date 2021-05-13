import os
import pandas as pd
import geopandas as gpd

from abc import ABCMeta, abstractmethod


class Feature(metaclass=ABCMeta):

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print(f'Creating object {cls}')
            cls._instance = super(Feature, cls).__new__(cls)
        return cls._instance

    def add_dependencies(self, data, **kwargs):
        for f in self.dependencies:
            f.compute(data, **kwargs)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def categorical(self) -> bool:
        pass

    @property
    @abstractmethod
    def dependencies(self) -> list:
        pass

    @abstractmethod
    def compute(self, data: pd.DataFrame, **kwargs):
        pass


class NumericalFeature(Feature):

    categorical = False


class CategoricalFeature(Feature):

    categorical = True

    @property
    @abstractmethod
    def values(self) -> list:
        pass


def register_feature(config, function):
    config.features_functions.append(function)


def compute_feature_dataframe(config, force=False):
    cache_file = config.get_cache_feature_df_name()
    #print(cache_file)
    if not force and os.path.exists(cache_file):
        df = pd.read_csv(cache_file)
        config.features = []
        for c in df.columns:
            if c not in {'total', 'tid', 'rid'}:
                config.add_feature(c)
        return df

    df = pd.read_csv(config.traj_file, parse_dates=[config.timestamp])
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[config.lon], df[config.lat]))
    df = gpd.sjoin(df, config.regions, op='within')
    for f in config.features:
        print(f"Computing {f.name}")
        f(df)

    df.drop(df.columns.difference(['id', 'duration', 'type']), axis=1, inplace=True)
    df.rename(columns={'index_right': 'region_id'}, inplace=True)

    df = df.groupby(['region_id', 'id', 'type']).agg({'duration': sum}).reset_index().set_index(['region_id', 'id'])

    df = df.pivot_table(values='duration', index=df.index, columns='type', aggfunc='first')
    df.fillna({c: 0.0 for c in df.columns}, inplace=True)
    df['total'] = df.loc[:,:].sum(axis=1)
    df['rid'], df['tid'] = zip(*df.index)
    return df
