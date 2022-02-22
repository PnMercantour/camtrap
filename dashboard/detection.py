import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context
import dash
from metadata import listSites

detection_card = dbc.Card([
    dbc.CardHeader("Détection"),
    dbc.CardBody([
        dcc.Dropdown(
            id="detection:source", clearable=False,
            options=[{'label': 'tous les Media', 'value': 'all'}, {
                'label': 'MegaDetector', 'value': 'megadetector'}], value='all',
        ),
        dbc.Collapse([
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
                marks=None,
                value=0.96,
                tooltip={'placement': 'bottom', 'always_visible': True},
            ),
            dcc.Slider(
                id='detection:megadetector:out_threshold',
                min=0,
                max=1,
                marks=None,
                step=0.02,
                value=0.80,
                tooltip={'placement': 'bottom', 'always_visible': True},
            ),
        ],
            id="detection:megadetector_options",
            is_open=True,
        )
    ])
])


@ dash.callback(
    Output('detection:megadetector_options', 'is_open'),
    Input('detection:source', 'value'),
)
def toggle_detection_options(source):
    return source == 'megadetector'
