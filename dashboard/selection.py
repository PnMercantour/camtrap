import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, callback_context
import dash
import random
from metadata import listSites, listVisits, getVisitMetadata

selection_card = dbc.Card([
    dbc.CardHeader("Sélection"),
    dbc.CardBody([
        dbc.Label("Site"),
        dcc.Dropdown(
            id='select:site',
            clearable=False,
            options=[{'label': str(i), 'value': i}
                 for i in listSites()],
        ),
        dbc.Label("Visite"),
        dcc.Store(id='visit:cookie', storage_type='local'),
        dcc.Dropdown(
            id='select:visit',
            clearable=False,
            options=[],
        ),
    ])
])


@ dash.callback(
    Output('select:site', 'value'),
    Output('select:visit', 'options'),
    Output('select:visit', 'value'),
    Input('select:site', 'value'),
    State('visit:cookie', 'data'),
)
def update_selection_dropdown(site_id, visit_cookie):
    if site_id is None:  # init
        sites = listSites()
        if visit_cookie is not None:
            prev_site = visit_cookie.get('site_id')
            if prev_site in listSites():
                site_id = prev_site
                visits = listVisits(site_id)
                prev_visit = visit_cookie.get('visit')
                if prev_visit in visits:
                    visit = prev_visit
                else:
                    visit = visits[0]
            else:
                site_id = random.choice(sites)
                visits = listVisits(site_id)
                visit = random.choice(visits)
        else:
            site_id = random.choice(sites)
            visits = listVisits(site_id)
            visit = random.choice(visits)
    else:  # user input
        visits = listVisits(site_id)
        if len(visits) == 0:
            visit = None
        else:
            visit = visits[0]
        site_id = dash.no_update  # last statement before return
    return site_id, [{'label': d, 'value': d}
                     for d in visits], visit


@ dash.callback(
    Output('visit:cookie', 'data'),
    Input('select:visit', 'value'),
    State('select:site', 'value')
)
def update_visit_cookie(visit, site_id):
    return dict(visit=visit, site_id=site_id)


context = dict(visit=Input('select:visit', 'value'),
               site_id=Input('select:site', 'value'))


def t_selection_context():
    # just check visit, if site has changed ... visit has changed too
    return 'select:visit.value' in [trigger['prop_id'] for trigger in callback_context.triggered]
