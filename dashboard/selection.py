import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, callback_context
import dash
from metadata import listSites, listVisits

selection_card = dbc.Card([
    dbc.CardHeader("Sélection"),
    dbc.CardBody([
        dbc.Label("Site"),
        dcc.Dropdown(
            id='select:site',
            clearable=False,
            options=[{'label': str(i), 'value': i}
                 for i in listSites()],
            value=listSites()[0]
        ),
        dbc.Label("Visite"),
        dcc.Dropdown(
            id='select:visit',
            clearable=False,
            options=[],
        ),
    ])
])


@ dash.callback(
    Output('select:visit', 'options'),
    Output('select:visit', 'value'),
    Input('select:site', 'value'))
def update_visit_dropdown(site_id):
    if site_id is None:
        return [], None
    options = [{'label': d, 'value': d}
               for d in listVisits(site_id)]
    if options is None or len(options) == 0:
        value = None
    else:
        value = options[0]['value']
    return options, value
