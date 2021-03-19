from utils import get_config

import plotly.express as px
import plotly.graph_objects as go

from scipy.spatial.distance import pdist
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize, QuantileTransformer

from seriate import seriate
from minisom import MiniSom


def named_function(name):
    def wrapper(f):
        f.name = name
        return f
    return wrapper


def cached_function(f):
    @named_function(f.name)
    def wrapper():
        config = get_config()
        sol = config.get_cache_solution(f.name)
        if sol is not None:
            return sol
        sol = f()
        config.cache_solution(f.name, sol)
        return sol
    return wrapper


@cached_function
@named_function("Seriation")
def seriation_color():
    config = get_config()
    data = normalize(config.get_data(), norm='l1')
    dist = pdist(data)
    order = seriate(dist, timeout=0)

    colors = [0 for _ in range(config.nb_regions)]
    for rank, rid in enumerate(order):
        colors[rid] = rank
    return colors

@cached_function
@named_function("Self-organizing map")
def som_color():
    config = get_config()
    data = config.get_data().values.tolist()
    som = MiniSom(20, 1, len(data[0]), sigma=0.6)
    som.train(data, 1000)

    return [str(som.winner(x)) for x in data]

@cached_function
@named_function("PCA")
def pca_color():
    config = get_config()
    data = config.get_data()
    pca = PCA(n_components=1)
    new_data = sorted([(value, idx) for idx, value in enumerate(pca.fit_transform(data))])

    colors = [0 for _ in range(config.nb_regions)]
    for rank, (_, rid) in enumerate(new_data):
        colors[rid] = rank
    return colors


def get_possible_grouping():
    return [seriation_color, som_color, pca_color]

def get_default_grouping():
    return seriation_color

methods = {x.name: x for x in get_possible_grouping()}

def get_grouping_method(name):
    return methods[name]

def get_seriation_map(grouping):
    config = get_config()
    df = config.get_feature_df()
    colors = get_grouping_method(grouping)()

    df['group'] = colors
    df_sort = df.sort_values(by='group')
    df.drop(['group'], axis=1, inplace=True)
    df_sort.drop(['group'], axis=1, inplace=True)

    fig = px.choropleth_mapbox(df, geojson=config.regions, locations='rid',
                               color=colors, mapbox_style='carto-positron',
                               opacity=0.5, center={'lat': 50.798872, 'lon': 4.441393},
                               color_continuous_scale='rainbow', height=700, zoom=7)

    hm = go.Figure(go.Heatmap(z=config.scaler.fit_transform(df_sort[config.features]),
                              x=config.features,
                              colorscale='Greys'))
    return fig, hm

