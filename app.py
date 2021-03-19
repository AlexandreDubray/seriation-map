import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output

import argparse

from maps import get_seriation_map, get_possible_grouping, get_default_grouping
from utils import create_config, get_config


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

@app.callback(
    Output('map', 'figure'),
    Output('heatmap', 'figure'),
    Input('radius-input', 'value'),
    Input('method-dropdown', 'value'))
def update_map(radius, method):
    config = get_config()
    config.radius = radius
    fig_map, fig_hm = get_seriation_map(method)
    return fig_map, fig_hm

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('traj_file', help='Filepath to the trajectory file')
    parser.add_argument('region_file', help='Filepath to the file with regions')
    parser.add_argument('--poi_file', help='Filepath to the POI file')

    args = parser.parse_args()
    create_config(args.traj_file, args.region_file, args.poi_file)
    config = get_config()

    app.layout = html.Div([
        html.H1(children='Seriation map'),
        dbc.Row([
            dbc.Col(['Radius: ', dcc.Input(id='radius-input', value=15, type='number')],
                    width=4),
            dbc.Col(
                dcc.Dropdown(
                    id='method-dropdown',
                    options=[{'label': x.name, 'value': x.name} for x in get_possible_grouping()],
                    value=get_default_grouping().name
                )
            )
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='heatmap'), className='col-6'),
            dbc.Col(dcc.Graph(id='map'), className='col-6')
        ]),
    ])

    app.run_server(debug=True)
