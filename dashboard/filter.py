import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback_context
import dash
import megadetector
import metadata
import observationData
from functools import lru_cache
import json
import config

observation_filter_switch = dbc.Switch(
    label="Filtre Observation",
    value=False,
    id='filter:observation',
)

processed = dbc.Switch(
    label="Média non contrôlé/contrôlé",
    value=False,
    id='filter:processed'
)

species = dcc.Dropdown(
    id='filter:species',
    placeholder='Espèce sauvage',
    clearable=True,
    multi=True,
    options=config.species_options,
)

valid = dbc.Switch(
    label="Validée",
    value=False,
    id='filter:valid'
)

not_valid = dbc.Switch(
    label="Non validée",
    value=False,
    id='filter:not_valid'
)

notify = dbc.Switch(
    label="Signalée",
    value=False,
    id='filter:notify'
)

not_notify = dbc.Switch(
    label="Non signalée",
    value=False,
    id='filter:not_notify'
)
empty = dbc.Switch(
    label="Vide",
    value=False,
    id='filter:empty'
)

not_empty = dbc.Switch(
    label="Non vide",
    value=False,
    id='filter:not_empty'
)


def three_state_layout(a, b):
    return dbc.Row([
        dbc.Col('', md=1),
        dbc.Col(a, md=5),
        dbc.Col(b, md=6)
    ])


observation_subfilter = dbc.Collapse([
    species,
    three_state_layout(valid, not_valid),
    three_state_layout(notify, not_notify),
    three_state_layout(empty, not_empty),
])

refresh = dbc.Button(
    'Rafraîchir', title='Rafraîchir le filtre Observation', size='sm', className="me-md-2")

collapsible_refresh = dbc.Collapse(refresh)
observation_filter = dbc.Collapse([
    processed,
    observation_subfilter,
])

card = dbc.Card([
    dbc.CardHeader("Filtres"),
    dbc.CardBody([
        dbc.Switch(label='Filtre Megadetector',
                   value=True, id='filter:megadetector'),
        dbc.Collapse(
            megadetector.panel,
            id='filter:show_megadetector'
        ),
        html.Hr(),
        dbc.Row([
            dbc.Col(observation_filter_switch, md=8),
            dbc.Col(collapsible_refresh, md=4),
        ], align='baseline'),
        observation_filter,
    ])
])


context = dict(
    megadetector=dict(
        active=Input('filter:megadetector', 'value'),
        parameters=megadetector.parameters
    ),
    observation=dict(
        active=Input(observation_filter_switch, 'value'),
        refresh=Input(refresh, 'n_clicks'),
        parameters=dict(
            processed=Input(processed, 'value'),
            subparameters=dict(
                species=Input(species, "value"),
                valid=Input(valid, 'value'),
                not_valid=Input(not_valid, 'value'),
                notify=Input(notify, 'value'),
                not_notify=Input(not_notify, 'value'),
                empty=Input(empty, 'value'),
                not_empty=Input(not_empty, 'value'),
            ),
        ),
    ),
)


# subfilters = dict(megadetector=megadetector)

# megadetector filter is called first (and does not depend on observation filter)
# observation filter is called after. Detector parameters are included to invalidate
# results cached with a different set of input values


def filter(metadata, context, visit, site_id):
    if context['megadetector']['active']:
        metadata = megadetector.filter(
            metadata, context['megadetector']['parameters'], visit, site_id)
    if context['observation']['active']:
        metadata = observationData.filter(
            metadata, context['observation']['parameters'], visit, site_id)
    return metadata


@lru_cache(maxsize=64)
def filterMetadata(visit, site_id, filter_s):
    context = json.loads(filter_s)
    raw_metadata = metadata.getVisitMetadataFromCache(visit, site_id)
    filtered = filter(raw_metadata, context, visit, site_id)
    return dict(raw_metadata=raw_metadata, metadata=filtered, context=context, visit=visit, site_id=site_id)


@ dash.callback(
    Output('filter:show_megadetector', 'is_open'),
    Input('filter:megadetector', 'value'),
)
def collapse_options(source):
    return source


@ dash.callback(
    Output(observation_filter, 'is_open'),
    Output(collapsible_refresh, 'is_open'),
    Input(observation_filter_switch, 'value'),
)
def collapse_obs_filter(source):
    return source, source


@ dash.callback(
    Output(observation_subfilter, 'is_open'),
    Input(processed, 'value'),
)
def collapse_obs_subfilter(source):
    return source


def gen_callback(a, b):
    @ dash.callback(
        Output(a, 'value'),
        Output(b, 'value'),
        Input(a, 'value'),
        Input(b, 'value'),
    )
    def cb(x, y):
        triggers = [trigger['prop_id']
                    for trigger in callback_context.triggered]
        if a.id in triggers[0]:
            return x, False
        elif b.id in triggers[0]:
            return False, y
        else:
            return False, False
    return cb


gen_callback(valid, not_valid)
gen_callback(notify, not_notify)
gen_callback(empty, not_empty)
