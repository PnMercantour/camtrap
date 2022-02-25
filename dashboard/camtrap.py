from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import flask
import dash_bootstrap_components as dbc
from functools import lru_cache

import json
from pathlib import Path

from pandas import options
from dataFinder import *
import stats
from classifierPanel import classifier_panel
import metadata
from metadata import listSites, listVisits, groupMedia
import selection
from selection import selection_card, t_selection_context
from media import to_media_options, o_media_options
import media
import filter
from group import mediaGroup, mediaGroups, group_card

from config import project_root, video_root, data_root
import auth

app = Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
)

print(f"""
camtrap dashboard
project root: {project_root}
video root:{video_root}
data root:{data_root}
{len(auth.users)} user accounts
authentification: {auth.init(app)}
""")


server = app.server


@server.route('/video/<path:path>')
def serve_video(path):
    return flask.send_from_directory(video_root, path)


filter_card = dbc.Card([
    dbc.CardHeader("Filtrer"),
    dbc.CardBody([
        dbc.Label("par date"),
        dcc.DatePickerRange(
            display_format='Y-M-D', start_date_placeholder_text='début', end_date_placeholder_text='fin', clearable=True),
        dbc.Label("par espèce"),
        dcc.Dropdown(
            multi=True,
            options=[
                {'label': 'Loup', 'value': 'loup'},
                {'label': 'sanglier', 'value': 'sanglier'},
                {'label': 'Faune sauvage', 'value': 'faune_sauvage'},
                {'label': 'Faune domestique', 'value': 'faune_domestique'}
            ])
    ])
])


map_tab = dbc.Tab([
    html.H1("Bientôt une carte des sites!")
],
    tab_id='map',
    label='Carte',
)
video_tab = dbc.Tab(
    tab_id='video',
    label='Vidéo',
    children=[
        html.Video(
            controls=True,
            id='movie_player',
            src=None,
            width='100%',
            autoPlay=True
        ),
    ])

image_tab = dbc.Tab([
    html.H1("Bientôt les plus belles images extraites du média!"),
    dbc.Carousel(items=[], style={'height': 500}),
],
    tab_id='image',
    label='Images',
)

stats_tab = dbc.Tab(
    tab_id='stats',
    label='Statistiques',
    children=dbc.Card([
        dbc.CardHeader('Statistiques du site'),
        dbc.CardBody([
            stats.table
        ])
    ])
)

preferences_tab = dbc.Tab(
    tab_id='preferences',
    label='Préférences',
    children=[
        dbc.Card([
            dbc.CardHeader('Sélection'),
            dbc.CardBody([
                dbc.Switch(label='Regrouper les médias',
                           value=True, id='prefs:group_media'),
            ])
        ]),
        dbc.Card([
            dbc.CardHeader('Serveur de vidéos'),
            dbc.CardBody([
                dbc.Switch(label='Télécharger depuis un serveur alternatif',
                           value=False, id='mediaserver:custom'),
                dbc.Input(id='mediaserver:url',
                          value='http://localhost:8000/', type='text')
            ])
        ])
    ]

)

tabs = dbc.Tabs([
    map_tab,
    video_tab,
    image_tab,
    stats_tab,
    preferences_tab,
],
    active_tab='video',
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
                selection_card,
                filter.card,
            ], md=3),
            dbc.Col([tabs, info_string], md=6),
            dbc.Col([
                classifier_panel,
                media.card,
                group_card,
            ], md=3)
        ],
        align="top",
    ),
],
    fluid=True,
)


def group_of_media(groups, media):
    if media:
        # TODO trouver le groupe correspondant au média
        return groups[0]['startTime'] if len(groups) > 0 else None
    else:
        return groups[0]['startTime'] if len(groups) > 0 else None


@lru_cache
def filtered_metadata(filter_s, visit, site_id):
    context = json.loads(filter_s)
    print(context)
    raw = metadata.getVisitMetadataFromCache(visit, site_id)
    filtered = filter.filter(raw, context, visit, site_id)
    return dict(raw=raw, filtered=filtered, context=context, visit=visit, site_id=site_id)


@ app.callback(
    output=[
        o_media_options,
    ],
    inputs=[
        filter.context,
        selection.context,
    ]
)
def filter_media(filter_context, context):
    md_dict = filtered_metadata(json.dumps(
        filter_context), context['visit'], context['site_id'])
    return [to_media_options(md_dict)]


@ app.callback(
    Output('movie_player', 'src'),
    Output('movie_player', 'hidden'),
    Input('select:media', 'value'),
    Input('mediaserver:custom', 'value'),
    Input('mediaserver:url', 'value'),
)
def update_video_player(media_path, custom, url):
    # TODO - send something instead of None
    if media_path is not None:
        if custom:
            path = url + str(media_path)
            print(path)
            return [path, False]
        else:
            return [(str(Path('/video') / media_path)), False]
    else:
        return [None, True]


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0')
