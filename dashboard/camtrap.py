import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import flask
import base64
from os import getenv
import argparse
from pathlib import Path
from dataFinder import *

app = dash.Dash()

server = app.server
camtrap_root = Path(getenv('CAMTRAP_ROOT'))

@server.route('/video/<path:path>')
def serve_video(path):
    print( f'Serving {camtrap_root/path}')
    return flask.send_from_directory(camtrap_root, path)

list_of_images = [
    'img_1.png',
    'img_2.png'
]

app.layout = html.Div([
    dcc.Dropdown(
        id='image-dropdown',
        options=[{'label': i, 'value': 'dashboard/' + i} for i in list_of_images],
        # initially display the first entry in the list
        value='dashboard/' + list_of_images[0]
    ),
    html.Img(id='image'),
    dcc.Dropdown(
        id='mailles-dropdown',
        options=[{'label': f'{i}: descripteur', 'value': i} for i in df_ids(camtrap_root)]
    ),
    dcc.Dropdown(
        id='date-dropdown',
        options=[]
    ),
    dcc.Dropdown(
        id='file-dropdown',
        options=[]
    ),
    html.Video(
            controls = True,
            id = 'movie_player',
            #src = "https://www.w3schools.com/html/mov_bbb.mp4",
            src = '/video/Maille 6/2020-03-11/IMG_0001.MP4',
            width = 800,
            autoPlay=True
        ),
])


@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('image-dropdown', 'value')])
def update_image_src(image_path):
    # print the image_path to confirm the selection is as expected
    print('current image_path = {}'.format(image_path))
    encoded_image = base64.b64encode(open(image_path, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded_image.decode())

@app.callback(
    Output('date-dropdown', 'options'),
    Input('mailles-dropdown', 'value'))
def update_date_dropdown(maille_id):
    print('update_date_dropdown', maille_id)
    return [{'label':d, 'value': d} for d in df_dates(df_id_path(maille_id, camtrap_root))]

@app.callback(
    Output('file-dropdown', 'options'),
    Input('date-dropdown', 'value'),
    State('mailles-dropdown', 'value'))
def update_video_dropdown(date, maille_id):
    print('update_video_dropdown', date, type(date), maille_id)
    print(df_date_path(date, df_id_path(maille_id, camtrap_root)))
    return [{'label':d, 'value': d} for d in df_assets(df_date_path(date, df_id_path(maille_id, camtrap_root)))]

if __name__ == '__main__':
    app.run_server(debug=True)
