import dash_bootstrap_components as dbc
from dash import html

table_header = [
    html.Thead(html.Tr([
        html.Th("Visite"),
        html.Th("Nbre de medias"),
        html.Th("Nbre de fiches"),
        html.Th("% Megadetector"),
        html.Th("Observations de loups"),
    ]))
]

row1 = html.Tr([html.Td("Arthur"), html.Td("Dent")])
row2 = html.Tr([html.Td("Ford"), html.Td("Prefect")])
row3 = html.Tr([html.Td("Zaphod"), html.Td("Beeblebrox")])
row4 = html.Tr([html.Td("Trillian"), html.Td("Astra")])

table_body = [html.Tbody([row1, row2, row3, row4])]

table = dbc.Table(table_header + table_body, bordered=True)
