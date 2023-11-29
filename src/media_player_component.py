from dash import (
    Dash,
    html,
    dcc,
    Input,
    Output,
    State,
    callback_context,
    no_update,
    callback,
)
import dash_bootstrap_components as dbc
import flask
from pathlib import Path

from config import project_root, media_root, data_root
import media_component
import project_component

component = html.Div(
    [
        photo_player := html.Img(
            width="100%",
        ),
        video_player := html.Video(
            controls=True,
            src=None,
            width="100%",
            autoPlay=True,
        ),
    ]
)


@callback(
    {
        "video": {
            "src": Output(video_player, "src"),
            "hidden": Output(video_player, "hidden"),
        },
        "photo": {
            "src": Output(photo_player, "src"),
            "hidden": Output(photo_player, "hidden"),
        },
    },
    {
        "media_path": media_component.path,
        "use_alt_server": Input("mediaserver:custom", "value"),
        "alt_server_url": Input("mediaserver:url", "value"),
        "project_id": State(project_component.project, "value"),
    },
)
def display_media(media_path, use_alt_server, alt_server_url, project_id):
    if media_path is None:
        return {
            "video": {"src": None, "hidden": True},
            "photo": {"src": None, "hidden": True},
        }
    path = Path(media_path)
    if use_alt_server:
        url = alt_server_url + str(media_path)
    else:
        url = str(Path("/media", str(project_id), media_path))
        print("url", url)
    if path.suffix in [".JPG"]:
        return {
            "video": {"src": None, "hidden": True},
            "photo": {"src": url, "hidden": False},
        }
    else:
        return {
            "video": {"src": url, "hidden": False},
            "photo": {"src": None, "hidden": True},
        }


# encoded_image= base64.b64encode(open(path, 'rb').read())
# return 'data:image/png;base64,{}'.format(encoded_image.decode())
