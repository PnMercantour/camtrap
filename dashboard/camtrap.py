from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import flask
import dash_bootstrap_components as dbc

import json
from pathlib import Path
from dataFinder import *
import stats
from classifierPanel import classifier_panel
from metadata import listSites, listVisits, getVisitMetadata, groupMedia
from selection import selection_card
from media import media_card
from detection import detection_card
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


with (project_root / "config/tags.json").open() as f:
    tags = json.load(f)
tag_controls = dbc.RadioItems(
    options=[{"label": tag["label"], "value":tag["value"]} for tag in tags])

map_tab = dbc.Tab(
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

image_tab = dbc.Tab(
    tab_id='image',
    label='Images',
    children=dbc.Carousel(items=[], style={'height': 500})
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
                dbc.Switch(label='Regrouper les media',
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
                html.H2("Camtrap - Pièges photos du Parc national du Mercantour"), md=10),
            dbc.Col(auth.component, md=2)
            ], justify='between'),
    html.Hr(),
    dbc.Row(
        [
            dbc.Col([
                selection_card,
                detection_card,
                media_card,
                # filter_card,
                group_card,
            ], md=3),
            dbc.Col([tabs, info_string], md=6),
            dbc.Col(classifier_panel, md=3)
        ],
        align="top",
    ),
],
    fluid=True,
)


def group_of_media(groups, media):
    if media:
        # TODO trouver le groupe correspondant au media
        return groups[0]['startTime'] if len(groups) > 0 else None
    else:
        return groups[0]['startTime'] if len(groups) > 0 else None


@ app.callback(
    Output('group:select', 'options'),
    Output('group:select', 'value'),
    Input('group:interval', 'value'),
    Input('select:visit', 'value'),
    State('select:site', 'value'),
    State('group:select', 'options'),
    State('group:select', 'value'),
    State('prefs:group_media', 'value'),
    Input('group_control:previous', 'n_clicks'),
    Input('group_control:next', 'n_clicks'),
    # Input('group_control:first', 'n_clicks'),
    # Input('group_control:last', 'n_clicks'),
)
def update_group_dropdown(interval, date, site_id, options, value, group_media, _1, _2):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'group_media' in changed_id or 'group:interval' in changed_id:
        if group_media:
            groups = groupMedia(getVisitMetadata(
                date, site_id), interval)
            # TODO passer les metadonnées du media
            current_group = group_of_media(groups, None)
            return [options, current_group]
        elif 'group:interval' in changed_id:
            groups = groupMedia(getVisitMetadata(
                date, site_id), interval)
            return [groups, None]
        else:
            return [options, None]
    if 'select:visit' in changed_id:
        groups = groupMedia(getVisitMetadata(
            date, site_id), interval)
        options = [{
            'label': f"{group['startTime']} ({len(group['metadata'])})",
            'value': group['startTime']
        } for group in groups]
        value = groups[0]['startTime'] if len(
            groups) > 0 and group_media else None
        return [options, value]
    values = [item['value'] for item in options]
    if len(values) == 0:
        return [no_update, no_update]
    if 'group_control' in changed_id:
        if value is None:
            # TODO mettre en cache les metadonnées du groupe
            groups = groupMedia(getVisitMetadata(
                date, site_id), interval)
            # TODO passer les metadonnées du media
            value = group_of_media(groups, None)
        if 'first' in changed_id:
            return [no_update, values[0]]
        if 'last' in changed_id:
            return [no_update, values[-1]]
        if 'previous' in changed_id:
            return [no_update, values[max(values.index(value) - 1, 0)]]
        if 'next' in changed_id:
            return [no_update, values[min(values.index(value) + 1, len(values) - 1)]]
    else:
        return [no_update, no_update]


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
