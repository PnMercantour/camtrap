from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import flask
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
from os import getenv
import json
from pathlib import Path
from dataFinder import *
import megaFilter
from classifier import loadClassifier, storeClassifier
from metadata import listSites, listVisits, getMetadata, groupMedia

project_root = Path(__file__).parent.parent.resolve()
load_dotenv(project_root / '.env')
load_dotenv(project_root / 'config/default_config')

data_root = project_root / getenv('CAMTRAP_DATA')
"Location of processed files"

video_root = project_root / getenv('CAMTRAP_VIDEO')
"Location of raw video files"

try:
    with (project_root / "config/users.json").open() as f:
        camtrap_users = json.load(f)
except:
    if (project_root / "config/users.json").exists():
        print(
            'ERROR: config/users.json could not be parsed, either remove or fix this file')
        exit(1)
    else:
        print('WARNING: config/users.json not found')
    camtrap_users = []
camtrap_users.append({"label": "Invité", "value": "guest"})

print(f"""
camtrap dashboard
project root: {project_root}
video root:{video_root}
data root:{data_root}
{len(camtrap_users)} registered user(s)
""")

app = Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

server = app.server


@server.route('/video/<path:path>')
def serve_video(path):
    return flask.send_from_directory(video_root, path)


video_filter = [dbc.RadioItems(
    options=[
        {'label': 'toutes les vidéos', 'value': 'classifier:all'},
        {'label': 'vidéos non classifiées', 'value': 'classifier:false'},
        {'label': "vidéos classifiées", "value": 'classifier:true'}]),
    dcc.Dropdown(
        multi=True,
        options=[
            {'label': 'Loup', 'value': 'loup'},
            {'label': 'sanglier', 'value': 'sanglier'},
            {'label': 'Faune sauvage', 'value': 'faune_sauvage'},
            {'label': 'Faune domestique', 'value': 'faune_domestique'}
        ])]

detection_card = dbc.Card([
    dbc.CardHeader("Détecter"),
    dbc.CardBody([
        dcc.Dropdown(
            id="detection:source", clearable=False,
            options=[{'label': 'Toutes les vidéos', 'value': 'all'}, {
                'label': 'MegaDetector', 'value': 'megadetector'}], value='megadetector',
        ),
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


control_panel = [
    media_card,
    # filter_card,
    detection_card,
]

media_controls = dbc.Row([
    dbc.Col('Media'),
    dbc.Col(html.Button('Premier', id='media_control:first'), width=2),
    dbc.Col(html.Button('Précédent', id='media_control:previous'), width=2),
    dbc.Col(html.Button('Suivant', id='media_control:next'), width=2),
    dbc.Col(html.Button('Dernier', id='media_control:last'), width=2),
    dbc.Col(html.Button('Loup', id='media_control:loup'), width=2),

], justify="left",
)

group_controls = dbc.Row([
    dbc.Col('Regroupement'),
    dbc.Col(html.Button('Premier', id='group_control:first'), width=2),
    dbc.Col(html.Button('Précédent', id='group_control:previous'), width=2),
    dbc.Col(html.Button('Suivant', id='group_control:next'), width=2),
    dbc.Col(html.Button('Dernier', id='group_control:last'), width=2),
], justify="left",
)

map_tab = dbc.Tab(
    tab_id='map',
    label='Carte',
)
video_tab = dbc.Tab(
    tab_id='video',
    label='Vidéo',
    style={'height': 700},
    children=[
        html.Video(
            controls=True,
            id='movie_player',
            src=None,
            # width=960,
            height=500,
            autoPlay=True
        ),
        media_controls, group_controls
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

parameters_tab = dbc.Tab(
    tab_id='params',
    label='Paramètres'
)

tabs = dbc.Tabs([
    map_tab,
    video_tab,
    image_tab,
    stats_tab,
    parameters_tab,
],
    active_tab='video',
)

info_string = html.Div(id='file_info')

app.layout = dbc.Container([
    html.H1("Camtrap - Pièges photos du Parc national du Mercantour"),
    html.Hr(),
    dbc.Row(
        [
            dbc.Col(control_panel, md=2),
            dbc.Col([info_string, tabs], md=10),
        ],
        align="top",
    ),
],
    fluid=True,
)


@app.callback(
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


@app.callback(
    Output('select:group', 'options'),
    Output('select:group', 'value'),
    Input('select:visit', 'value'),
    State('select:site', 'value'),
    State('select:group', 'options'),
    State('select:group', 'value'),
    Input('group_control:previous', 'n_clicks'),
    Input('group_control:next', 'n_clicks'),
    Input('group_control:first', 'n_clicks'),
    Input('group_control:last', 'n_clicks'),
)
def update_group_dropdown(date, site_id, options, value, _1, _2, _3, _4):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'select:visit' in changed_id:
        groups = groupMedia(getMetadata(site_id, date, data_root), 60)
        return [{
            'label': f"{group['startTime']} ({len(group['metadata'])})",
            'value': group['startTime']
        } for group in groups], None
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
    State('select:site', 'value'),
    Input('detection:source', 'value'),
    Input('detection:megadetector', 'value'),
    Input('detection:megadetector:in_threshold', 'value'),
    Input('detection:megadetector:out_threshold', 'value')
)
def update_media_dropdown(group_start_time, date, site_id, source, megadetector, in_threshold, out_threshold):
    media_metadata = getMetadata(site_id, date, data_root)
    if group_start_time is not None:
        groups = groupMedia(media_metadata, 60)
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
    Input('media_control:loup', 'n_clicks'),
)
def set_file_value(options, value, date, site_id, first, previous, next, last, loup):
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
    if 'media_control:loup' in changed_id:
        path = data_root / 'classification' / 'video'
        classif = loadClassifier(path, site_id, date, value)
        classif['loup'] = True,
        storeClassifier(classif, path, site_id, date, value),
        values = [item['value'] for item in options]
        return values[min(values.index(value) + 1, len(values) - 1)]
    return options[0]['value']


@ app.callback(
    Output('movie_player', 'src'),
    Input('select:media', 'value'),
)
def update_video_player(media_path):
    # TODO - send something instead of None
    if media_path is not None:
        return str(Path('/video') / media_path)
    else:
        return None


if __name__ == "__main__":
    app.run_server(debug=True)
