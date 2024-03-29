from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update, callback
import dash_bootstrap_components as dbc
import flask
from pathlib import Path

from config import project_root, media_root, data_root
import media


component = html.Div([
    html.Img(
        id='photo_player',
        width='100%',
    ),
    html.Video(
        controls=True,
        id='video_player',
        src=None,
        width='100%',
        autoPlay=True,
    ),
])


@ callback({
    "video": {
        "src": Output('video_player', 'src'),
        "hidden": Output('video_player', 'hidden'),
    },
    "photo": {
        'src': Output('photo_player', 'src'),
        "hidden": Output('photo_player', 'hidden'),
    },
}, {
    "media_path": media.path,
    "use_alt_server": Input('mediaserver:custom', 'value'),
    "alt_server_url": Input('mediaserver:url', 'value'),
})
def display_media(media_path, use_alt_server, alt_server_url):
    if media_path is None:
        return ({"video": {'src': None, 'hidden': True}, "photo": {'src': None, 'hidden': True}})
    path = Path(media_path)
    if use_alt_server:
        url = alt_server_url + str(media_path)
    else:
        url = str(Path('/media', media_path))
    if path.suffix in ['.JPG']:
        return({"video": {'src': None, 'hidden': True}, "photo": {'src': url, 'hidden': False}})
    else:
        return({"video": {'src': url, 'hidden': False}, "photo": {'src': None, 'hidden': True}})


# encoded_image= base64.b64encode(open(path, 'rb').read())
# return 'data:image/png;base64,{}'.format(encoded_image.decode())
