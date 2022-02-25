import dash_bootstrap_components as dbc
from dash import dcc, Input, Output
import dash
import megadetector

card = dbc.Card([
    dbc.CardHeader("Filtres"),
    dbc.CardBody([
        dbc.Switch(label='Megadetector', value=True, id='filter:megadetector'),
        dbc.Collapse(
            megadetector.panel,
            id='filter:show_megadetector'
        ),
    ])
])


context = dict(
    megadetector=dict(
        active=Input('filter:megadetector', 'value'),
        parameters=megadetector.parameters
    ))


subfilters = dict(megadetector=megadetector)


def filter(metadata, context, visit, site_id):
    if context['megadetector']['active']:
        return megadetector.filter(metadata, context['megadetector']['parameters'], visit, site_id)
    else:
        print('no filter')
        return metadata


@ dash.callback(
    Output('filter:show_megadetector', 'is_open'),
    Input('filter:megadetector', 'value'),
)
def collapse_options(source):
    return source
