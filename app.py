from commons.functions_commons import *
from dash.dependencies import Input, Output, State
from dash import html
from dash import dcc
import dash
import plotly.express as px
import pandas as pd
import json
import dash_bootstrap_components as dbc


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
                     value='BR', className='dropdown'), dcc.RadioItems(id='select-graph', options=[' Dispersão', ' Linha', ' Barra'], value=' Barra', inline=True)], className='dropdown-state-graph'),
    html.Div(id='input-select-cause',
             children=[dcc.Dropdown(id='select_cause', options=options_cause, multi=True, value=['Chuva'])]),
    html.Br(),
    html.Div([html.Div(dcc.Graph(id='map', figure={}, className='map')),
             html.Div(id='graph', children=[dcc.Graph(id='bar')])], className='container')

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
     Input(component_id='select_state', component_property='value')]
)
def update_type_graph(graph_selected, state_selected):
    if graph_selected == ' Dispersão':
        fig = scatter_chart(df, state_selected)
        update_layout(fig)
        fig.update_layout(
            legend=dict(
                orientation="h",
                entrywidth=70,
                yanchor="top",
                y=-0.1,
                xanchor="right",
                x=0.9
            ))
        return [dcc.Graph(id='scatter', figure=fig, className='scatter')]
    elif graph_selected == ' Linha':
        fig = line_chart(df, state_selected)
        update_layout(fig)
        return [dcc.Graph(id='line', figure=fig, className='line')]
    elif graph_selected == ' Barra':
        fig = bar_chart(df, state_selected, ['Chuva'])
        update_layout(fig)
        fig.update_layout(
            legend=dict(
                orientation="h",
                entrywidth=70,
                yanchor="top",
                y=-0.1,
                xanchor="right",
                x=0.9
            ))
        return [dcc.Graph(id='bar', figure=fig, className='bar')]


@app.callback(
    [Output(component_id='input-select-cause', component_property='children')],
    [Input(component_id='select-graph', component_property='value')]
)
def show_cause(graph_selected):
    if graph_selected == ' Barra':
        return [dcc.Dropdown(id='select_cause', options=options_cause, multi=True,
                             value=['Chuva'])]
    else:
        return [html.Div(style={'width': '0px', 'height': '0px'})]


@app.callback(
    [Output(component_id='bar', component_property='figure'), Output(
        component_id='select_cause', component_property='value'), Output(component_id='alert', component_property='children')],
    [Input(component_id='select_cause', component_property='value')],
    prevent_initial_callback=True,
    prevent_initial_call=True
)
def upgrade_causes(cause_selected):
    print('contando')
    if cause_selected == ['Chuva']:
        print('aqui')
        raise dash.exceptions.PreventUpdate
    print('bo')
    max_selected = 3  # Maximum number of selected options allowed
    alerts = html.Div(style={'width': '0px', 'height': '0px'})
    if len(cause_selected) > max_selected:
        cause_selected.pop()
        alerts = dbc.Alert("This is a warning alert... be careful...",
                           color="warning", duration=4000)
    fig = bar_chart(df, state, cause_selected)
    update_layout(fig)
    fig.update_layout(
        legend=dict(
            orientation="h",
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
