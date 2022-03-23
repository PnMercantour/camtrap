import config
import auth
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

digitizer_info = html.Div('vide', id='observation:digitizer')

group_mode = dbc.Switch(label='Appliquer au groupe',
                        id='observation:group_mode', value=False)
valid = dbc.Switch(label='Valider',
                   id='observation:valid', value=False)
notify = dbc.Switch(label='Signaler',
                    id='observation:notify', value=False)
multispecies = dbc.Switch(label='Plusieurs espèces',
                          id='observation:multispecies', value=False)
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
    placeholder='Espèce sauvage',
    clearable=True,
    options=config.species_options,
)

domestic = dcc.Dropdown(
    id='observation:attribute:domestic',
    placeholder='Espèce domestique',
    clearable=True,
    options=config.domestic_options,
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
    dbc.CardHeader(dbc.Row([
        dbc.Col('Observation', md=5, sm=12),
        dbc.Col(digitizer_info, md=7, sm=12),
    ])),
    dbc.CardBody([
        group_mode,
        valid, notify,
        multispecies,
        dbc.Row([
            dbc.Col('Faune sauvage', md=5, sm=12),
            dbc.Col(species, md=7, sm=12),
            dbc.Col('Faune domestique', md=5, sm=12),
            dbc.Col(domestic, md=7, sm=12),
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

dummy_attributes = {
    'valid': False,
    'notify': False,
    'multispecies': False,
    'species': None,
    'domestic': None,
    'population': None,
    'comments': None,

}


def normalize_obs(media, visit, site_id):
    "Normalize observation attributes"
    obs = observationData.getObservation(media, visit, site_id)
    attributes = obs['attributes']
    return {
        'user': obs.get('user'),
        'attributes': {
            'valid': attributes.get('valid'),
            'notify': attributes.get('notify'),
            'multispecies': attributes.get('multispecies'),
            'species': attributes.get('species'),
            'domestic': attributes.get('domestic'),
            'population': attributes.get('population'),
            'comments': attributes.get('comments'),
        }
    }


@ dash.callback(
    output=dict(
        digitizer_info=Output(digitizer_info, 'children'),
        group_mode=Output(group_mode, 'value'),
        attributes={
            'valid': Output(valid, 'value'),
            'notify': Output(notify, 'value'),
            'multispecies': Output(multispecies, 'value'),
            'species': Output(species, 'value'),
            'domestic': Output(domestic, 'value'),
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
            'multispecies': State(multispecies, 'value'),
            'species': State(species, 'value'),
            'domestic': State(domestic, 'value'),
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
    if media_index is None:
        return({
            'attributes': dummy_attributes,
            'digitizer_info': 'Aucun média',
            'group_mode': False,
            'cookie': {'attributes': dummy_attributes, 'group_mode': False},
            'disable_commit': True,
            'disable_cancel': True
        })
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
            'digitizer_info': obs['user'],
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
            return(initialize())
        if action == 'commit':
            if group_mode:
                for file_name in medias:
                    observationData.putObservation({
                        'user': auth.trusted_user(),
                        'attributes': attributes,
                    },
                        file_name, visit, site_id)
            else:
                observationData.putObservation({
                    'user': auth.trusted_user(),
                    'attributes': attributes,
                },
                    file_name, visit, site_id)
            return(initialize())
    return initialize()
