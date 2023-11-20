from config import project_root
from os import getenv
import dash
import dash_auth
from dash import html, Input, Output
import flask
import json

auth = getenv('CAMTRAP_AUTH')

users = []

if auth == 'BasicAuth':
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
    if auth == 'BasicAuth':
        dash_auth.BasicAuth(
            app,
            users
        )
    return auth


component = html.H5(id="auth:user_name")

default_user = 'PNM'


@ dash.callback(
    Output('auth:user_name', 'children'),
    # fake input to trigger callback at startup
    Input('auth:user_name', 'children')
)
def set_user_name(any):
    if auth == 'BasicAuth':
        return flask.request.authorization['username']
    else:
        return default_user


def trusted_user():
    "to be called within a callback environment"
    if auth == 'BasicAuth':
        return flask.request.authorization['username']
    else:
        return default_user
