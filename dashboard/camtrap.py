import dash
from dash import html, dcc, Input, Output, State, callback_context
import flask
import base64
from os import getenv
import argparse
from pathlib import Path
from dataFinder import *
import analyse_simple

app = dash.Dash(__name__, external_stylesheets=[
                'https://codepen.io/chriddyp/pen/bWLwgP.css'])

server = app.server
camtrap_root = Path(getenv('CAMTRAP_ROOT'))
data_root = Path('data/detection/frames')  # FIXME


@server.route('/video/<path:path>')
def serve_video(path):
    return flask.send_from_directory(camtrap_root, path)


list_of_images = [
    'img_1.png',
    'img_2.png'
]


def recently_updated_maille(root):
    "TODO: Returns the most recently visited Maille"
    ids = df_ids(camtrap_root)
    if ids is not None and len(ids) > 0:
        return ids[0]
    else:
        return None


app.layout = html.Div([
    dcc.RadioItems(
        id='ia-filter',
        options=[
            {'label': 'Toutes les vidéos', 'value': 'no'},
            {'label': 'Détection automatique', 'value': 'analyse_simple'},
            {'label': 'Vidéos rejetées (contrôle)',
             'value': 'analyse_simple_control'}
        ],
        value='no'
    ),
    dcc.Slider(
        id='threshold_slider',
        min=0,
        max=1,
        step=0.02,
        value=0.9,
        tooltip={'placement': 'bottom', 'always_visible': True},
    ),
    dcc.Dropdown(
        id='maille-dropdown',
        options=[{'label': f'{i}: descripteur', 'value': i}
                 for i in df_ids(camtrap_root)],
        clearable=False,
        value=recently_updated_maille(camtrap_root)),
    dcc.Dropdown(
        id='date-dropdown',
        clearable=False,
        options=[]
    ),
    html.Div([dcc.Dropdown(
        id='file-dropdown',
        clearable=False,
        options=[]
    ),
        html.Button('Précédent', id='previous-file'),
        html.Button('Suivant', id='next-file'),
    ]),
    html.Div(id='video_counter'),
    html.Video(
        controls=True,
        id='movie_player',
        #src = "https://www.w3schools.com/html/mov_bbb.mp4",
        # src='/video/Maille 6/2020-03-11/IMG_0001.MP4',
        src=None,
        width=800,
        height=450,
        autoPlay=True
    ),
    dcc.Dropdown(
        id='image-dropdown',
        options=[{'label': i, 'value': 'dashboard/' + i}
                 for i in list_of_images],
        # initially display the first entry in the list
        value='dashboard/' + list_of_images[0]
    ),
    html.Img(id='image'),
])


@app.callback(
    Output('date-dropdown', 'options'),
    Input('maille-dropdown', 'value'))
def update_date_dropdown(maille_id):
    if maille_id is None:
        return []
    return [{'label': d, 'value': d} for d in df_dates(df_id_path(maille_id, camtrap_root))]


@app.callback(
    Output('date-dropdown', 'value'),
    Input('date-dropdown', 'options'))
def set_date_value(options):
    if options is None or len(options) == 0:
        return None
    return options[0]['value']


@app.callback(
    Output('file-dropdown', 'options'),
    Input('date-dropdown', 'value'),
    State('maille-dropdown', 'value'),
    Input('ia-filter', 'value'),
    Input('threshold_slider', 'value')
)
def update_file_dropdown(date, maille_id, ia_filter, threshold):
    if ia_filter == 'no':
        return [{'label': d, 'value': d} for d in df_assets(df_date_path(date, df_id_path(maille_id, camtrap_root)))]
    if ia_filter == 'analyse_simple':
        return [{'label': d, 'value': d} for d in analyse_simple.assets(df_date_path(date, df_id_path(maille_id, data_root)), threshold=threshold)]
    if ia_filter == 'analyse_simple_control':
        return [{'label': d, 'value': d} for d in analyse_simple.assets(df_date_path(date, df_id_path(maille_id, data_root)), threshold=threshold, control=True)]


@app.callback(
    Output('video_counter', 'children'),
    Input('file-dropdown', 'options')
)
def set_counter_value(options):
    if options is not None:
        return [f'{len(options)} vidéos sélectionnées']
    else:
        return None


@app.callback(
    Output('file-dropdown', 'value'),
    Input('file-dropdown', 'options'),
    State('file-dropdown', 'value'),
    Input('previous-file', 'n_clicks'),
    Input('next-file', 'n_clicks'),
)
def set_file_value(options, value, previous, next):
    if options is None or len(options) == 0:
        return None
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'next-file' in changed_id:
        values = [item['value'] for item in options]
        return values[min(values.index(value) + 1, len(values) - 1)]
    if 'previous-file' in changed_id:
        values = [item['value'] for item in options]
        return values[max(values.index(value) - 1, 0)]
    return options[0]['value']


@app.callback(
    Output('movie_player', 'src'),
    Input('file-dropdown', 'value'),
    State('date-dropdown', 'value'),
    State('maille-dropdown', 'value'))
def update_video_player(name, date, maille_id):
    if name is not None and date is not None and maille_id is not None:
        return str(Path('/video') / df_asset_path(name, df_date_path(date, df_id_path(maille_id, camtrap_root))).relative_to(camtrap_root))
    else:
        return None


@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('image-dropdown', 'value')])
def update_image_src(image_path):
    # print the image_path to confirm the selection is as expected
    print('current image_path = {}'.format(image_path))
    encoded_image = base64.b64encode(open(image_path, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded_image.decode())


if __name__ == '__main__':
    app.run_server(debug=True)
