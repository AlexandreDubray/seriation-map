import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output

import argparse

from smap.features.defaults import TimeUsage

from smap.ordering.OLOSeriation import OLOSeriation
from smap.ordering.SOMClustering import SOMClustering
from smap.ordering.TSPSeriation import TSPSeriation

from smap.smap import create_smap, get_smap

from smap.maps import get_seriation_map


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

@app.callback(
    Output('map', 'figure'),
    Output('heatmap', 'figure'),
    Input('radius-input', 'value'),
    Input('method-dropdown', 'value'))
def update_map(radius, method):
    smap = get_smap()
    smap.radius = radius
    fig_map, fig_hm = get_seriation_map(ordering_methods[method])
    return fig_map, fig_hm

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('traj_file', help='Filepath to the trajectory file')
    parser.add_argument('region_file', help='Filepath to the file with regions')
    parser.add_argument('--poi_file', help='Filepath to the POI file')

    args = parser.parse_args()
    create_smap(args.traj_file, args.region_file, args.poi_file, [TimeUsage()])
    smap = get_smap()

    # Does not work now :(
    #ordering_methods = [cls() for cls in OrderingMethod.__subclasses__()]

    ordering_methods = [OLOSeriation(), SOMClustering(), TSPSeriation()]
    ordering_methods = {x.name: x for x in ordering_methods}


    app.layout = html.Div([
        html.H1(children='Seriation map'),
        dbc.Row([
            dbc.Col(['Radius: ', dcc.Input(id='radius-input', value=10, type='number')],
                    width=4),
            dbc.Col(
                dcc.Dropdown(
                    id='method-dropdown',
                    options=[{'label': x, 'value': x} for x in ordering_methods],
                    value=OLOSeriation().name
                )
            )
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='heatmap'), className='col-6'),
            dbc.Col(dcc.Graph(id='map'), className='col-6')
        ]),
    ])

    app.run_server(debug=True)
