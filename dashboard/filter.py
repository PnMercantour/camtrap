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

# filter_card = dbc.Card([
#     dbc.CardHeader("Filtrer"),
#     dbc.CardBody([
#         dbc.Label("par date"),
#         dcc.DatePickerRange(
#             display_format='Y-M-D', start_date_placeholder_text='début', end_date_placeholder_text='fin', clearable=True),
#         dbc.Label("par espèce"),
#         dcc.Dropdown(
#             multi=True,
#             options=[
#                 {'label': 'Loup', 'value': 'loup'},
#                 {'label': 'sanglier', 'value': 'sanglier'},
#                 {'label': 'Faune sauvage', 'value': 'faune_sauvage'},
#                 {'label': 'Faune domestique', 'value': 'faune_domestique'}
#             ])
#     ])
# ])

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
