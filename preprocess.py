import numpy as np
import pandas as pd


def _haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat/2.0)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2.0)**2
    c = 2*np.arcsin(np.sqrt(a))
    km = 6367*c
    return km


def _fill_start_traj(df, id_field: str, default_values: dict[str, float]):
    change_traj = df[id_field] != df[id_field].shift(1).fillna(True)
    for field in default_values:
        df.loc[change_traj, field] = default_values[field]


def compute_distance(df, lat: str, lon: str):
    df['distance'] = _haversine(df[lon], df[lat], df[lon].shift(1).fillna(0), df[lat].shift(1).fillna(0))


def compute_time(df, timestamp: str):
    df['duration'] = (df[timestamp] - df[timestamp].shift(1).fillna(df.loc[0, timestamp]))
    df['duration'] /= np.timedelta64(1, 's')


def compute_velocity(df):
    assert('distance' in df.columns and 'duration' in df.columns)
    df['velocity'] = df['distance'] / df['duration'] * 3600


def add_fields(df, lat='lat', lon='lon', timestamp='daytime'):
    compute_distance(df, lat, lon)
    compute_time(df, timestamp)
    compute_velocity(df)
    _fill_start_traj(df, 'id', {
        'distance': 0,
        'duration': 0,
        'velocity': 0
    })
