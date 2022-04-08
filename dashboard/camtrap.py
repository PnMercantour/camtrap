from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import flask
import dash_bootstrap_components as dbc
from functools import lru_cache

import json
from pathlib import Path

import stats
import observation
import selection
from selection import t_selection_context
import media
import media_player
import filter

from config import project_root, media_root, data_root
import auth

app = Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
)

print(f"""
camtrap dashboard
project root: {project_root}
media root:{media_root}
data root:{data_root}
{len(auth.users)} user accounts
authentification: {auth.init(app)}""")


server = app.server


@server.route('/media/<path:path>')
def serve_media(path):
    return flask.send_from_directory(media_root, path)


map_tab = dbc.Tab([
    html.H1("Bientôt une carte des sites!")
],
    tab_id='map',
    label='Carte',
)
media_tab = dbc.Tab(
    tab_id='media_tab',
    label='Media',
    children=[
        media_player.component,
    ])

image_tab = dbc.Tab([
    html.H1("Bientôt les plus belles images extraites du média!"),
    dbc.Carousel(items=[], style={'height': 500}),
],
    tab_id='image',
    label='Images',
)

stats_tab = dbc.Tab(
    html.H1("Bientôt des rapports d'exploitation des données de camtrap!"),
    tab_id='stats',
    label='Statistiques',
    # children=dbc.Card([
    #     dbc.CardHeader('Statistiques du site'),
    #     dbc.CardBody([
    #         stats.table
    #     ])
    # ])
)

preferences_tab = dbc.Tab(
    tab_id='preferences',
    label='Préférences',
    children=[

        dbc.Card([
            dbc.CardHeader('Serveur de vidéos'),
            dbc.CardBody([
                dbc.Switch(label='Télécharger depuis un serveur alternatif',
                           value=False, id='mediaserver:custom'),
                dbc.Input(id='mediaserver:url',
                          value='http://localhost:8000/', type='text')
            ])
        ]),
        observation.preferences,
    ]

)

tabs = dbc.Tabs([
    map_tab,
    media_tab,
    image_tab,
    stats_tab,
    preferences_tab,
],
    active_tab='media_tab',
)

info_string = html.Div(id='file_info')

app.layout = dbc.Container([
    dbc.Row([
            dbc.Col(
                html.H2("Camtrap - Pièges photos du Parc national du Mercantour"), md=9),
            dbc.Col(auth.component, md=3),
            ],),
    html.Hr(),
    dbc.Row(
        [
            dbc.Col([
                selection.card,
                filter.card,
            ], md=2),
            dbc.Col([tabs, info_string], md=6),
            dbc.Col([
                observation.card,
                media.card,
            ], md=4)
        ],
        align="top",
    ),
],
    fluid=True,
)


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0')
