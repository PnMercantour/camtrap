from dash import Dash, html, dcc, Input, Output, State, callback_context
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


def recently_updated_maille(root):
    "TODO: Returns the most recently visited Maille"
    ids = df_ids(root)
    if ids is not None and len(ids) > 0:
        return ids[0]
    else:
        return None


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
            value=0.96,
            tooltip={'placement': 'bottom', 'always_visible': True},
        ),
        dcc.Slider(
            id='detection:megadetector:out_threshold',
            min=0,
            max=1,
            step=0.02,
            value=0.80,
            tooltip={'placement': 'bottom', 'always_visible': True},
        ),
    ])
])


media_card = dbc.Card([
    dbc.CardHeader("Sélectionner"),
    dbc.CardBody([
        dbc.Label("Maille"),
        dcc.Dropdown(
            id='select:maille',
            clearable=False,
            options=[{'label': f'{i}: descripteur', 'value': i}
                 for i in df_ids(data_root / 'detection' / 'frames')],
            value=recently_updated_maille(data_root / 'detection' / 'frames')
        ),
        dbc.Label("Visite"),
        dcc.Dropdown(
            id='select:visit',
            clearable=False,
            options=[],
        ),
        dbc.Label('Vidéo'),
        dcc.Dropdown(
            id='select:file',
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


params = [
    media_card,
    filter_card,
    detection_card,
]

video_controls = dbc.Row([
    dbc.Col(html.Button('Précédent', id='video_control:previous'), width=2),
    dbc.Col(html.Button('Suivant', id='video_control:next'), width=2),
    dbc.Col(html.Button('Loup', id='video_control:loup'), width=2),

], justify="center",
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
        video_controls,
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

tabs = dbc.Tabs([
    map_tab,
    video_tab,
    image_tab,
    stats_tab,
],
    active_tab='video',
)

info_string = html.Div(id='file_info')

app.layout = dbc.Container([
    html.H1("Camtrap - Pièges photos du Parc national du Mercantour"),
    html.Hr(),
    dbc.Row(
        [
            dbc.Col(params, md=2),
            dbc.Col([info_string, tabs], md=10),
        ],
        align="top",
    ),
],
    fluid=True,
)


@app.callback(
    Output('select:visit', 'options'),
    Input('select:maille', 'value'))
def update_visit_dropdown(maille_id):
    if maille_id is None:
        return []
    return [{'label': d, 'value': d} for d in df_dates(df_id_path(maille_id, data_root / 'detection' / 'frames'))]


@app.callback(
    Output('select:visit', 'value'),
    Input('select:visit', 'options'))
def set_visit_value(options):
    if options is None or len(options) == 0:
        return None
    return options[0]['value']


@app.callback(
    Output('select:file', 'options'),
    Output('file_info', 'children'),
    Input('select:visit', 'value'),
    State('select:maille', 'value'),
    Input('detection:source', 'value'),
    Input('detection:megadetector', 'value'),
    Input('detection:megadetector:in_threshold', 'value'),
    Input('detection:megadetector:out_threshold', 'value')
)
def update_file_dropdown(date, maille_id, source, megadetector, in_threshold, out_threshold):
    if source == 'all':
        options = [{'label': d, 'value': d} for d in df_assets(
            df_date_path(date, df_id_path(maille_id, video_root)))]
        return [options, f'{len(options)} vidéos']
    if source == 'megadetector':
        if megadetector == 'all':
            l = megaFilter.processed(
                data_root / 'detection'/'visits', maille_id, date)
            return [[{'label': name, 'value': name} for name in l], f'{len(l)} vidéos analysées']
        if megadetector in ['pass', 'reject']:
            l_pass, l_rejected = megaFilter.filter(
                data_root / 'detection' / 'visits', maille_id, date, in_threshold, out_threshold)
            video_count = len(l_pass) + len(l_rejected)
            if megadetector == 'pass':
                l_out = l_pass
                message = f'{len(l_out)} vidéos retenues sur {video_count}'
            else:
                l_out = l_rejected
                message = f'{len(l_out)} vidéos rejetées sur {video_count}'
            return [[{'label': d, 'value': d} for d in l_out], message]
    print('something wrong with source', source, megadetector)
    raise ValueError(source)


@ app.callback(
    Output('select:file', 'value'),
    Input('select:file', 'options'),
    State('select:file', 'value'),
    State('select:visit', 'value'),
    State('select:maille', 'value'),
    Input('video_control:previous', 'n_clicks'),
    Input('video_control:next', 'n_clicks'),
    Input('video_control:loup', 'n_clicks'),
)
def set_file_value(options, value, date, maille_id, previous, next, loup):
    if options is None or len(options) == 0:
        return None
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'video_control:next' in changed_id:
        values = [item['value'] for item in options]
        return values[min(values.index(value) + 1, len(values) - 1)]
    if 'video_control:previous' in changed_id:
        values = [item['value'] for item in options]
        return values[max(values.index(value) - 1, 0)]

    if 'video_control:loup' in changed_id:
        path = data_root / 'classification' / 'video'
        classif = loadClassifier(path, maille_id, date, value)
        classif['loup'] = True,
        storeClassifier(classif, path, maille_id, date, value),
        values = [item['value'] for item in options]
        return values[min(values.index(value) + 1, len(values) - 1)]
    return options[0]['value']


@ app.callback(
    Output('movie_player', 'src'),
    Input('select:file', 'value'),
    State('select:visit', 'value'),
    State('select:maille', 'value'))
def update_video_player(name, date, maille_id):
    if name is not None and date is not None and maille_id is not None:
        return str(Path('/video') / df_asset_path(name, df_date_path(date, df_id_path(maille_id, video_root))).relative_to(video_root))
    else:
        return None


if __name__ == "__main__":
    app.run_server(debug=True)
