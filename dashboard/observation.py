from sqlite3 import SQLITE_DROP_TEMP_INDEX
from dash import dcc, html, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import dash
import dash_bootstrap_components as dbc
import json
from pathlib import Path
import media
import selection
import filter
import observationData

from numpy import False_
from observationData import loadClassifier, dumpClassifier

group_mode = dbc.Switch(label='Appliquer au groupe',
                        id='observation:group_mode', value=False)
valid = dbc.Switch(label='Valider',
                   id='observation:valid', value=False)
notify = dbc.Switch(label='Signaler',
                    id='observation:notify', value=False)
copy = dbc.Button('Copier', id='observation:copy',
                  title="Copier l'observation", disabled=True, size='sm', className="me-md-2")
paste = dbc.Button('Coller', id='observation:paste',
                   title="Coller l'observation mémorisée",  disabled=True, size='sm', className="me-md-2")
commit = dbc.Button('Enregistrer',
                    id='observation:commit', title='Enregistrer la saisie', size='sm', color='success')
cancel = dbc.Button('Annuler', id='observation:cancel', title='Annuler la saisie en cours',
                    size='sm', className="me-md-2")

cookie = dcc.Store(id='observation:cookie', storage_type='local')

prefer_group_media = dbc.Switch(label='Regrouper les médias',
                                value=True, id='observation:prefer_group_media')
preferences = dbc.Card([
    dbc.CardHeader('Observation'),
    dbc.CardBody([prefer_group_media,
                  ])
])

species = dcc.Dropdown(
    id='observation:attribute:species',
    placeholder='Espèce',
    clearable=True,
    options=[
        {'label': 'loup', 'value': 'loup'},
        {'label': 'vache', 'value': 'vache'},
    ]
)

population = dbc.Input(
    id='observation:attribute:population',
    placeholder="Nombre d'individus",
    type='number',
)

comments = dbc.Input(
    id="observation:attribute:comment",
    placeholder="Commentaire...",
    type="text")

card = dbc.Card([
    dbc.CardHeader('Observation'),
    dbc.CardBody([
        group_mode,
        valid, notify,
        dbc.Row([
            dbc.Col('Espèce', md=5, sm=12),
            dbc.Col(species, md=7, sm=12),
            dbc.Col('Population', md=5, sm=12),
            dbc.Col(population, md=7),
            dbc.Col('Notes', md=5, sm=12),
            dbc.Col(comments, md=7),
        ]),
    ]),
    dbc.CardFooter([
        copy, paste,
        cancel, commit,
        cookie,
    ]),
])


def normalize_obs(media, visit, site_id):
    "Normalize observation attributes"
    obs = observationData.getObservation(media, visit, site_id)
    attributes = obs['attributes']
    return {
        'user': obs.get('user'),
        'attributes': {
            'valid': attributes.get('valid'),
            'notify': attributes.get('notify'),
            'species': attributes.get('species'),
            'population': attributes.get('population'),
            'comments': attributes.get('comments'),
        }
    }


@ dash.callback(
    output=dict(
        group_mode=Output(group_mode, 'value'),
        attributes={
            'valid': Output(valid, 'value'),
            'notify': Output(notify, 'value'),
            'species': Output(species, 'value'),
            'population': Output(population, 'value'),
            'comments': Output(comments, 'value'),
        },
        cookie=Output(cookie, 'data'),
        disable_commit=Output(commit, "disabled"),
        disable_cancel=Output(cancel, 'disabled'),
    ),
    inputs=dict(
        group_mode=State(group_mode, 'value'),
        attributes={
            'valid': State(valid, 'value'),
            'notify': State(notify, 'value'),
            'species': State(species, 'value'),
            'population': State(population, 'value'),
            'comments': State(comments, 'value'),
        },
        cookie=State(cookie, 'data'),
        context={
            'selection': selection.context,
            'filter': filter.context,
            'interval': media.interval,
            'media_index': Input('media:index', 'value'),
            'group_index': State('media:group_index', 'value'),
        },
        preferences={
            'prefer_group_media': State(prefer_group_media, 'value')
        },
        other={
            'commit': Input(commit, 'n_clicks'),
            'cancel': Input(cancel, 'n_clicks'),
            'copy': Input(copy, 'n_clicks'),
            'paste': Input(paste, 'n_clicks'),
        }
    ),
)
def update_observation(group_mode,  attributes, cookie, context, preferences, other):
    media_index = context['media_index']
    group_index = context['group_index']
    visit = context['selection']['visit']
    site_id = context['selection']['site_id']
    md_dict = media.build_groups(
        context['interval'], visit, site_id, json.dumps(context['filter']))
    metadata = md_dict['metadata']
    groups = md_dict['groups']
    group_md = groups[group_index - 1]
    medias = [md['fileName']
              for md in metadata][group_md['start']:group_md['end'] + 1]
    file_name = metadata[media_index - 1]['fileName']

    def initialize():
        obs = normalize_obs(file_name, visit, site_id)
        group_obs = [normalize_obs(
            media, visit, site_id) for media in medias]
        attributes = obs['attributes']
        group_mode_enabled = preferences['prefer_group_media'] and all([attributes == o['attributes']
                                                                        for o in group_obs])
        return ({
            'attributes': attributes,
            'group_mode': group_mode_enabled,
            'cookie': {'attributes': attributes, 'group_mode': group_mode},
            'disable_commit': False,
            'disable_cancel': False,
        })

    triggers = [trigger['prop_id']
                for trigger in callback_context.triggered]
    if 'observation' in triggers[0]:
        action = triggers[0].split(':')[1].split('.')[0]
        if action == 'cancel':
            print('cancel')
            return(initialize())
        if action == 'commit':
            if group_mode:
                print('group mode commit')
                for file_name in medias:
                    observationData.putObservation({
                        'user': 'foo',
                        'attributes': attributes,
                    },
                        file_name, visit, site_id)
            else:
                print('single commit')
                observationData.putObservation({
                    'user': 'foo',
                    'attributes': attributes,
                },
                    file_name, visit, site_id)
            return(initialize())
    print(triggers)
    return initialize()


# @ dash.callback(
#     Output('classifier:valid', 'value'),
#     Output('classifier:tag', 'value'),
#     Output('classifier:population', 'value'),
#     Output('classifier:comment', 'value'),
#     Output('classifier:store', 'data'),
#     Input('select:media', 'value'),
#     State('select:visit', 'value'),
#     State('select:site', 'value'),
#     State('classifier:valid', 'value'),
#     State('classifier:tag', 'value'),
#     State('classifier:population', "value"),
#     State('classifier:comment', 'value'),
#     Input('classifier:group', 'value'),
#     Input('classifier:reset', 'n_clicks'),
#     Input('classifier:abort', 'n_clicks'),
#     Input('classifier:commit', 'n_clicks'),
#     State('classifier:store', 'data'),
# )
# def classifier_logic(media, visit, site_id, valid, tag, population, comment, group, delete, abort, commit, store):
#     print(store)
#     changed_id = [p['prop_id'] for p in callback_context.triggered][0]
#     if group:
#         if changed_id in ['classifier:group.value', 'select:media.value', 'classifier:abort.n_clicks']:
#             print('load group properties and compare')
#             raise PreventUpdate
#         if changed_id in ['classifier:reset.n_clicks']:
#             print('reset group properties')
#             raise PreventUpdate
#         if changed_id in ['classifier:commit.n_clicks']:
#             print('commit group edition')
#             raise PreventUpdate
#         else:
#             print('unhandled changed_id while in group mode', changed_id)
#             return [
#                 valid,
#                 tag,
#                 population,
#                 comment,
#                 store,
#             ]
#     else:
#         if changed_id in ['classifier:group.value', 'select:media.value', 'classifier:abort.n_clicks']:
#             print('load media properties')
#             classifier = loadClassifier(
#                 site_id, visit, Path(media).name)
#             return[
#                 classifier.get('valid'),
#                 classifier.get('tag'),
#                 classifier.get('population'),
#                 classifier.get('comment'),
#                 classifier,
#             ]
#         if changed_id == 'classifier:reset.n_clicks':
#             print('reset media properties')
#             raise PreventUpdate
#         if changed_id == 'classifier:commit.n_clicks':
#             print('commit media properties')
#             store['tag'] = tag
#             store['population'] = population
#             store['comment'] = comment
#             store['valid'] = valid
#             success = dumpClassifier(
#                 store, site_id, visit, Path(media).name)
#             store['serial'] = store['serial'] + 1  # hack
#             return [
#                 valid,
#                 tag,
#                 population,
#                 comment,
#                 store
#             ]
