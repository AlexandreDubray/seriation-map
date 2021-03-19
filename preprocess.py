import numpy as np
import geopandas as gpd

def _haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat/2.0)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2.0)**2
    c = 2*np.arcsin(np.sqrt(a))
    km = 6367*c
    return km


def _fill_start_traj(df, id_field, default_values):
    change_traj = df[id_field] != df[id_field].shift(1).fillna(True)
    for field in default_values:
        df.loc[change_traj, field] = default_values[field]


def compute_distance(df, lat, lon):
    df['distance'] = _haversine(df[lon], df[lat], df[lon].shift(1).fillna(df.loc[0, lon]), df[lat].shift(1).fillna(df.loc[0, lat]))


def compute_time(df, timestamp: str):
    df['duration'] = (df[timestamp] - df[timestamp].shift(1).fillna(df.loc[0, timestamp]))
    df['duration'] /= np.timedelta64(1, 's')


def compute_velocity(df):
    assert('distance' in df.columns and 'duration' in df.columns)
    df['velocity'] = df['distance'] / df['duration'] * 3600


def compute_type(df, has_lb_regions):
    assert('distance' in df.columns and 'velocity' in df.columns)

    def _get_type(row):
        velocity = row['velocity']
        duration = row['duration']
        if velocity < 15:
            # We have a stop
            if has_lb_regions and row['label'] != 'tbd':
                return row['label']
            if duration <= 300:
                return 'congestion'
            return 'work'
        return 'driving'

    df['type'] = df.apply(_get_type, axis=1)


def add_fields(df, labelized_regions, lat='lat', lon='lon', timestamp='daytime'):
    compute_distance(df, lat, lon)
    compute_time(df, timestamp)
    compute_velocity(df)
    has_lb_regions = labelized_regions is not None
    if has_lb_regions:
        df = gpd.sjoin(df, labelized_regions, op='within', how='left')
        df.drop(['index_right'], axis=1, inplace=True)
        df['label'] = df['label'].fillna('tbd')
    compute_type(df, has_lb_regions)
    _fill_start_traj(df, 'id', {
        'distance': 0,
        'duration': 0,
        'velocity': 0,
        'type': 'driving'
    })
    return df

def get_unormalized_feature_dataframe(df_traj, df_regions, labelized_regions):
    """Return the df of feature where the feature are not normalized and computed per cell"""
    df_traj = add_fields(df_traj, labelized_regions)
    df_traj = gpd.sjoin(df_traj, df_regions, op='within')
    df_traj.rename(columns={'index_right': 'region_id'}, inplace=True)
    df_traj['region_id'] = df_traj['region_id'].fillna(-1)
    df_traj = df_traj[df_traj['region_id'] != -1]

    df_feature = df_traj.groupby(['region_id', 'id', 'type']).agg({'duration': sum}).reset_index().set_index(['region_id', 'id'])
    df_feature = df_feature.pivot_table(values='duration', index=df_feature.index, columns='type', aggfunc='first')
    df_feature.fillna({c: 0.0 for c in df_feature.columns}, inplace=True)
    df_feature['total'] = df_feature.loc[:,:].sum(axis=1)
    df_feature['rid'], df_feature['tid'] = zip(*df_feature.index)
    return df_feature
