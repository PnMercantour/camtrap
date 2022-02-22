from dash import dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import dash
import dash_bootstrap_components as dbc
from pathlib import Path
from classifier import loadClassifier, dumpClassifier


classifier_panel = dbc.Card([
    dbc.CardHeader('Classifier'),
    dbc.CardBody([
        dbc.Switch(label='Appliquer au groupe',
                   id='classifier:group', value=True),
        dbc.Switch(label='Donnée validée', id='classifier:valid', value=False),
        dbc.Row([
            dbc.Col('Espèce', md=5, sm=12),
            dbc.Col(dcc.Dropdown(
                id="classifier:tag",
                placeholder='Espèce',
                clearable=True,
                options=[
                            {'label': 'loup', 'value': 'loup'},
                            {'label': 'vache', 'value': 'vache'},
                ]
            ), md=7, sm=12),
            dbc.Col('Population', md=5, sm=12),
            dbc.Col(
                dbc.Input(
                    id="classifier:population",
                    placeholder="Nombre d'individus",
                    type="number"), md=7),
            dbc.Col('Notes', md=5, sm=12),
            dbc.Col(
                dbc.Input(
                    id="classifier:comment",
                    placeholder="Commentaire...",
                    type="text"), md=7),
        ]),
    ]),
    dbc.CardFooter([
        dbc.Button('Supprimer', id='classifier:reset', title='Supprimer les annotations',
                   size='sm', className="me-md-2"),
        dbc.Button('Restaurer', id='classifier:abort', title='Annuler la saisie en cours',
                   size='sm', className="me-md-2"),
        dbc.Button('Enregistrer',
                   id='classifier:commit', title='Enregistrer la saisie', size='sm', color='success'),
        dcc.Store(id='classifier:store'),
    ]),
])


@ dash.callback(
    Output('classifier:valid', 'value'),
    Output('classifier:tag', 'value'),
    Output('classifier:population', 'value'),
    Output('classifier:comment', 'value'),
    Output('classifier:store', 'data'),
    Input('select:media', 'value'),
    State('select:visit', 'value'),
    State('select:site', 'value'),
    State('classifier:valid', 'value'),
    State('classifier:tag', 'value'),
    State('classifier:population', "value"),
    State('classifier:comment', 'value'),
    Input('classifier:group', 'value'),
    Input('classifier:reset', 'n_clicks'),
    Input('classifier:abort', 'n_clicks'),
    Input('classifier:commit', 'n_clicks'),
    State('classifier:store', 'data'),
)
def classifier_logic(media, visit, site_id, valid, tag, population, comment, group, delete, abort, commit, store):
    print(store)
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if group:
        if changed_id in ['classifier:group.value', 'select:media.value', 'classifier:abort.n_clicks']:
            print('load group properties and compare')
            raise PreventUpdate
        if changed_id in ['classifier:reset.n_clicks']:
            print('reset group properties')
            raise PreventUpdate
        if changed_id in ['classifier:commit.n_clicks']:
            print('commit group edition')
            raise PreventUpdate
        else:
            print('unhandled changed_id while in group mode', changed_id)
            return [
                valid,
                tag,
                population,
                comment,
                store,
            ]
    else:
        if changed_id in ['classifier:group.value', 'select:media.value', 'classifier:abort.n_clicks']:
            print('load media properties')
            classifier = loadClassifier(
                site_id, visit, Path(media).name)
            return[
                classifier.get('valid'),
                classifier.get('tag'),
                classifier.get('population'),
                classifier.get('comment'),
                classifier,
            ]
        if changed_id == 'classifier:reset.n_clicks':
            print('reset media properties')
            raise PreventUpdate
        if changed_id == 'classifier:commit.n_clicks':
            print('commit media properties')
            store['tag'] = tag
            store['population'] = population
            store['comment'] = comment
            store['valid'] = valid
            success = dumpClassifier(
                store, site_id, visit, Path(media).name)
            store['serial'] = store['serial'] + 1  # hack
            return [
                valid,
                tag,
                population,
                comment,
                store
            ]
