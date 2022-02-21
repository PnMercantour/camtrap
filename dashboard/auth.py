from config import project_root
import dash
import dash_auth
from dash import html, Input, Output
import flask
import json

basicAuth = False

users = []

if basicAuth:
    try:
        with (project_root / "config/users.json").open() as f:
            users = json.load(f)
    except:
        if (project_root / "config/users.json").exists():
            print(
                'ERROR: config/users.json could not be parsed, please fix this file')
        else:
            print('ERROR: config/users.json not found')
        exit(1)


def init(app):
    "app est nécessaire pour BasicAuth"
    if basicAuth:
        dash_auth.BasicAuth(
            app,
            users
        )
        return 'basicAuth'
    else:
        return 'no Auth'


component = html.H2(id="auth:user_name")

default_user = 'PNM'


@ dash.callback(
    Output('auth:user_name', 'children'),
    # fake input to trigger callback at startup
    Input('auth:user_name', 'children')
)
def set_user_name(any):
    if basicAuth:
        return flask.request.authorization['username']
    else:
        return default_user
