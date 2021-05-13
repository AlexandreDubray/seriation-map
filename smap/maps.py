import plotly.express as px
import plotly.graph_objects as go

import json
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import QuantileTransformer

from smap.coloring.Colorscale import get_colorscale
from smap.coloring.Colors import str_to_rgb
from smap.smap import get_smap


def get_seriation_map(order_method):
    smap = get_smap()
    df = smap.get_feature_df()

    order = order_method.get_order(df)
    df['order'] = order
    df = df.sort_values(by='order')
    df.drop(['order'], axis=1, inplace=True)

    bsu_order = [0 for _ in range(len(order))]
    for idx, bsu in enumerate(order):
        bsu_order[bsu] = idx

    geojson = json.loads(smap.regions.to_json())

    fig = go.Figure()

    if order_method.clustering:
        z = [str(x) for x in order]
        colorbar = {
            'title': 'Cluster',
        }
    else:
        colorscheme = px.colors.sequential.Rainbow
        colorscheme = [str_to_rgb(x) for i, x in enumerate(colorscheme) if i not in {1,3,6}]
        distances = [0.0] + [euclidean(df.iloc[order[i-1]], df.iloc[order[i]]) for i in range(1, len(bsu_order))]
        colorscale = get_colorscale(distances, colorscheme)
        colorbar = {
            'title': 'Order'
        }

    fig.add_trace(go.Choroplethmapbox(geojson=geojson, locations=df.region_id,
                                      z=order,
                                      colorscale=colorscale,
                                      marker_opacity=0.8, marker_line_width=0,
                                      colorbar=colorbar))
    fig.update_layout(mapbox={
        'accesstoken': open('./mapbox.tk').read(),
        'style': 'mapbox://styles/aldubray/ckkmt2c1x52bj17qt3kqtlxi8',
        'center': {
            'lat': 50.50000,
            'lon': 4.441393
        },
    },
                      mapbox_zoom=7,
                      height=800,
                      width=1000,
                      )


    scaler = QuantileTransformer()
    feats = []
    for f in smap.features:
        if f.categorical:
            for v in f.values:
                feats.append(v)
        else:
            feats.append(f.name)
    hm = go.Figure(go.Heatmap(z=scaler.fit_transform(df[feats]),
                              x=feats,
                              colorscale='Greys'))
    return fig, hm
