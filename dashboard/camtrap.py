from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import flask
import dash_bootstrap_components as dbc

import json
from pathlib import Path
from dataFinder import *
import megaFilter
from classifierPanel import classifier_panel
from metadata import listSites, listVisits, getMetadata, groupMedia

from config import project_root, video_root, data_root, camtrap_users

print(f"""
camtrap dashboard
project root: {project_root}
video root:{video_root}
data root:{data_root}
{len(camtrap_users)} registered user(s)
""")

app = Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
)

server = app.server


@server.route('/video/<path:path>')
def serve_video(path):
    return flask.send_from_directory(video_root, path)


detection_card = dbc.Card([
    dbc.CardHeader("Détecter"),
    dbc.CardBody([
        dcc.Dropdown(
            id="detection:source", clearable=False,
            options=[{'label': 'tous les Media', 'value': 'all'}, {
                'label': 'MegaDetector', 'value': 'megadetector'}], value='all',
        ),
        dbc.Collapse([
            dcc.Dropdown(
                id="detection:megadetector",
                clearable=False,
                value='pass',
                options=[
                    {'label': "Toutes les vidéos", "value": 'all'},
                    {'label': 'Auto détection', 'value': 'pass'},
                    {'label': 'Corbeille', 'value': 'reject'},
                ]),
            dbc.Label('Seuils de détection'),
            dcc.Slider(
                id='detection:megadetector:in_threshold',
                min=0,
                max=1,
                step=0.02,
                marks=None,
                value=0.96,
                tooltip={'placement': 'bottom', 'always_visible': True},
            ),
            dcc.Slider(
                id='detection:megadetector:out_threshold',
                min=0,
                max=1,
                marks=None,
                step=0.02,
                value=0.80,
                tooltip={'placement': 'bottom', 'always_visible': True},
            ),
        ],
            id="detection:megadetector_options",
            is_open=True,
        )
    ])
])


media_card = dbc.Card([
    dbc.CardHeader("Sélectionner"),
    dbc.CardBody([
        dbc.Label("Site"),
        dcc.Dropdown(
            id='select:site',
            clearable=False,
            options=[{'label': str(i), 'value': i}
                 for i in listSites(data_root)],
            value=listSites(data_root)[0]
        ),
        dbc.Label("Visite"),
        dcc.Dropdown(
            id='select:visit',
            clearable=False,
            options=[],
        ),
        dbc.Label('Regroupement'),
        dcc.Dropdown(id='select:group', clearable=True, options=[]),
        dcc.Slider(
            id='group:interval',
            min=0,
            max=600,
            step=10,
            marks=None,
            value=300,
            tooltip={'placement': 'bottom', 'always_visible': True},
        ),
        dbc.Label('Media'),
        dcc.Dropdown(
            id='select:media',
            clearable=False,
            options=[]
        ),
    ])
])

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


media_controls = dbc.ButtonGroup([
    dbc.Button(html.I(className="fas fa-solid fa-fast-backward"),
               id='group_control:previous', title='Groupe précédent'),
    dbc.Button(html.I(className="fas fa-solid fa-step-backward"),
               id='media_control:first', title='Premier média du groupe'),
    dbc.Button(html.I(className="fas fa-solid fa-backward"),
               id='media_control:previous', title='Média précédent'),
    dbc.Button(html.I(className="fas fa-solid fa-forward"),
               id='media_control:next', title='Média suivant'),
    dbc.Button(html.I(className="fas fa-solid fa-step-forward"),
               id='media_control:last', title='dernier média du groupe'),
    dbc.Button(html.I(className="fas fa-solid fa-fast-forward"),
               id='group_control:next', title='Groupe suivant'),
], size='lg')

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
        dbc.Row([
            dbc.Col(media_controls, width='auto'),
        ], justify='between'),
    ])

image_tab = dbc.Tab(
    tab_id='image',
    label='Images',
    children=dbc.Carousel(items=[], style={'height': 500})
)

stats_tab = dbc.Tab(
    tab_id='stats',
    label='Statistiques'
)

preferences_tab = dbc.Tab(
    tab_id='preferences',
    label='Préférences',
    children=dbc.Card([
        dbc.CardHeader('Serveur de vidéos'),
        dbc.CardBody([
            dbc.Switch(label='Télécharger depuis un serveur alternatif',
                       value=False, id='mediaserver:custom'),
            dbc.Input(id='mediaserver:url',
                      value='http://localhost:8000/', type='text')
        ])
    ])
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
    html.H1("Camtrap - Pièges photos du Parc national du Mercantour"),
    html.Hr(),
    dbc.Row(
        [
            dbc.Col([
                media_card,
                # filter_card,
                detection_card,
            ], md=3),
            dbc.Col([tabs, info_string], md=6),
            dbc.Col(classifier_panel, md=3)
        ],
        align="top",
    ),
],
    fluid=True,
)


@ app.callback(
    Output('select:visit', 'options'),
    Output('select:visit', 'value'),
    Input('select:site', 'value'))
def update_visit_dropdown(site_id):
    if site_id is None:
        return [], None
    options = [{'label': d, 'value': d}
               for d in listVisits(site_id, data_root)]
    if options is None or len(options) == 0:
        value = None
    else:
        value = options[0]['value']
    return options, value


@ app.callback(
    Output('select:group', 'options'),
    Output('select:group', 'value'),
    Input('group:interval', 'value'),
    Input('select:visit', 'value'),
    State('select:site', 'value'),
    State('select:group', 'options'),
    State('select:group', 'value'),
    Input('group_control:previous', 'n_clicks'),
    Input('group_control:next', 'n_clicks'),
    # Input('group_control:first', 'n_clicks'),
    # Input('group_control:last', 'n_clicks'),
)
def update_group_dropdown(interval, date, site_id, options, value, _1, _2):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'select:visit' in changed_id or 'group:interval' in changed_id:
        groups = groupMedia(getMetadata(site_id, date, data_root), interval)
        return [{
            'label': f"{group['startTime']} ({len(group['metadata'])})",
            'value': group['startTime']
        } for group in groups], groups[0]['startTime'] if len(groups) > 0 else None
    values = [item['value'] for item in options]
    if len(values) == 0:
        return [no_update, no_update]
    if 'group_control' in changed_id:
        if value is None:
            value = values[0]
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
    Output('select:media', 'options'),
    Output('file_info', 'children'),
    Input('select:group', 'value'),
    Input('select:visit', 'value'),
    State('group:interval', 'value'),
    State('select:site', 'value'),
    Input('detection:source', 'value'),
    Input('detection:megadetector', 'value'),
    Input('detection:megadetector:in_threshold', 'value'),
    Input('detection:megadetector:out_threshold', 'value')
)
def update_media_dropdown(group_start_time, date, interval, site_id, source, megadetector, in_threshold, out_threshold):
    media_metadata = getMetadata(site_id, date, data_root)
    if group_start_time is not None:
        groups = groupMedia(media_metadata, interval)
        selected_group = next(
            (group for group in groups if group['startTime'] == group_start_time), None)
        full_media_options = [{'label': media['startTime'], 'value': media['path']}
                              for media in selected_group['metadata']]
    else:
        full_media_options = [{'label': media['startTime'],
                               'value': media['path']} for media in media_metadata]

    if source == 'all':
        return [full_media_options, f'{len(full_media_options)} vidéos']

    if source == 'megadetector':
        if megadetector == 'all':
            l = megaFilter.processed(
                data_root / 'detection'/'visits', site_id, date)
            options = [option for option in full_media_options if Path(
                option['value']).name in l]
            return [options, f'{len(options)} vidéos analysées sur {len(full_media_options)}']
        if megadetector in ['pass', 'reject']:
            l_pass, l_rejected = megaFilter.filter(
                data_root / 'detection' / 'visits', site_id, date, in_threshold, out_threshold)
            video_count = len(full_media_options)
            if megadetector == 'pass':
                l_out = l_pass
                message = 'vidéos retenues'
            else:
                l_out = l_rejected
                message = 'vidéos rejetées'
            options = [option for option in full_media_options if Path(
                option['value']).name in l_out]
            return [options, f'{len(options)} {message} sur {len(full_media_options)}']
    print('something wrong with source', source, megadetector)
    raise ValueError(source)


@ app.callback(
    Output('select:media', 'value'),
    Input('select:media', 'options'),
    State('select:media', 'value'),
    State('select:visit', 'value'),
    State('select:site', 'value'),
    Input('media_control:first', 'n_clicks'),
    Input('media_control:previous', 'n_clicks'),
    Input('media_control:next', 'n_clicks'),
    Input('media_control:last', 'n_clicks'),
)
def set_file_value(options, value, date, site_id, first, previous, next, last):
    if options is None or len(options) == 0:
        return None
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'media_control:first' in changed_id:
        return options[0]['value']
    if 'media_control:next' in changed_id:
        values = [item['value'] for item in options]
        return values[min(values.index(value) + 1, len(values) - 1)]
    if 'media_control:previous' in changed_id:
        values = [item['value'] for item in options]
        return values[max(values.index(value) - 1, 0)]
    if 'media_control:last' in changed_id:
        return options[-1]['value']
    return options[0]['value']


@ app.callback(
    Output('detection:megadetector_options', 'is_open'),
    Input('detection:source', 'value'),
)
def toggle_detection_options(source):
    return source == 'megadetector'


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
