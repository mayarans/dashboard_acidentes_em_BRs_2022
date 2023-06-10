import json

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output, State

from commons.functions_commons import *

external_stylesheets = ['assets/app.css']
app = dash.Dash(__name__, external_stylesheets=[
                external_stylesheets, "https://fonts.googleapis.com/css2?family=Sen:wght@400;700;800&display=swap", dbc.themes.BOOTSTRAP])

df = pd.read_csv('commons/dados_dashboard.csv')
state = 'BR'

states_data = json.load(open('commons/states.json'))

options_state = [{"label": states_data[state]['name'], "value": state}
                 for state in states_data.keys()]

options_cause = df['causa_acidente'].unique()


app.layout = html.Div([
    html.H1("Acidentes em Rodovias Federais 2022", className='title'),
    html.Div(id='alert', className='alert', style={
             'position': 'fixed', 'top': '100px', 'right': '10px', 'zIndex': '9999'}),
    html.Div([
        dcc.Dropdown(id='select_state', options=options_state,
                     value='BR', className='dropdown'), dcc.RadioItems(id='select-graph', options=[' Dispersão', ' Acidentes/Mês', ' Acidentes/Causa', ' Acidentes/Br'], value=' Acidentes/Causa', inline=True)], className='dropdown-state-graph'),
    html.Div(id='input-select-cause',
             children=[dcc.Dropdown(placeholder='Selecione as causas...', id='select_cause', options=options_cause, multi=True)]),
    html.Br(),
    html.Div([html.Div(dcc.Graph(id='map', figure={}, className='map')),
             html.Div(id='graph', children=[dcc.Graph(id='content-graph', figure={})])], className='container')

])


# LADO ESQUERDO
@app.callback(
    [Output(component_id='map', component_property='figure')],
    [Input(component_id='select_state', component_property='value')]
)
def upgrade_map(state_selected):
    global state
    state = state_selected
    fig = choropleth_map(df, state_selected)
    update_layout(fig)
    fig.update_layout(coloraxis_colorbar_x=0)
    return [fig]

# LADO DIREITO


@app.callback(
    [Output(component_id='graph', component_property='children')],
    [Input(component_id='select-graph', component_property='value'),
     Input(component_id='select_state', component_property='value')], State(component_id='select_cause', component_property='value')
)
def update_type_graph(graph_selected, state_selected, cause_selected):
    if graph_selected == ' Dispersão':
        fig = scatter_chart(df, state_selected)
        update_layout(fig)
        fig.update_layout(
            legend=dict(
                orientation="v",
                entrywidth=70,
                yanchor="top",
                y=-0.3,
                xanchor="right",
                x=0.9
            ))
        return [dcc.Graph(id='content-graph', figure=fig, className='scatter')]
    elif graph_selected == ' Acidentes/Mês':
        fig = line_chart(df, state_selected)
        update_layout(fig)
        return [dcc.Graph(id='content-graph', figure=fig, className='line')]
    elif graph_selected == ' Acidentes/Causa':
        fig = bar_chart(df, state_selected, cause_selected)
        update_layout(fig)
        fig.update_layout(
            legend=dict(
                orientation="v",
                entrywidth=70,
                yanchor="top",
                y=-0.1,
                xanchor="right",
                x=0.9
            ))
        return [dcc.Graph(id='content-graph', figure=fig, className='bar')]
    elif graph_selected == ' Acidentes/Br':
        fig = scatter_map(df, state_selected)
        update_layout(fig)
        return [dcc.Graph(id='content-graph', figure=fig, className='scatter-map')]


@app.callback(
    [Output(component_id='input-select-cause', component_property='children')],
    [Input(component_id='select-graph', component_property='value')],
    State(component_id='select_cause', component_property='value')
)
def show_cause(graph_selected, cause_selected):
    if graph_selected == ' Acidentes/Causa':
        return [dcc.Dropdown(placeholder='Selecione as causas...', id='select_cause', options=options_cause, multi=True,
                             value=cause_selected)]
    else:
        return [dcc.Dropdown(style={'display': 'none',  'width': '0px', 'height': '0px'}, value=cause_selected, id='select_cause')]


@app.callback(
    [Output(component_id='content-graph', component_property='figure'),
     Output(component_id='select_cause', component_property='value'),
     Output(component_id='alert', component_property='children')],
    [Input(component_id='select_cause', component_property='value')],
    prevent_initial_callback=True,
    prevent_initial_call=True
)
def upgrade_causes(cause_selected):
    print(cause_selected)
    max_selected = 3  # Maximum number of selected options allowed
    alerts = html.Div(style={'width': '0px', 'height': '0px'})
    if cause_selected is not None:
        if len(cause_selected) > max_selected:
            cause_selected.pop()
            alerts = dbc.Alert(f"Você só pode selecionar {max_selected} causas!",
                               color="warning", duration=4000)
    fig = bar_chart(df, state, cause_selected)
    update_layout(fig)
    fig.update_layout(
        legend=dict(
            orientation="v",
            entrywidth=70,
            yanchor="top",
            y=-0.1,
            xanchor="right",
            x=0.5
        ))

    return [fig, cause_selected, alerts]


def update_layout(fig):
    fig.update_layout({"plot_bgcolor": "rgba(0,0,0,0)",
                       "paper_bgcolor": "rgba(0,0,0,0)", "font": {"color": "#FFFFFF"}})


if __name__ == '__main__':
    app.run_server(debug=True)
