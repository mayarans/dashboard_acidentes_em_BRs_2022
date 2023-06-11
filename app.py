import json  # biblioteca para trabalhar com arquivos json
from enum import Enum  # biblioteca para criar enums

import dash  # biblioteca para criar a aplicação
# biblioteca para criar componentes bootstrap no Dash
import dash_bootstrap_components as dbc
import pandas as pd  # biblioteca para trabalhar com dataframes
from dash import dcc, html  # biblioteca para criar componentes html no Dash
from dash.dependencies import (  # biblioteca para criar callbacks no Dash
    Input, Output, State)

# importa todas as funções do arquivo functions_commons.py
from commons.functions_commons import *

# import plotly.express as px


class GraphType(Enum):
    """
    Classe para criar um Enum com os tipos de gráficos
    """
    SCATTER = ' Análise sobre óbitos'
    LINE = ' Acidentes/Mês'
    BAR = ' Acidentes/Causa'
    SCATTER_MAP = " Acidentes/Br's"


# Configuração do Dash
external_stylesheets = [
    'assets/app.css',  # CSS customizado
    # Fonte Sen utilizada
    'https://fonts.googleapis.com/css2?family=Sen:wght@400;700;800&display=swap',
    dbc.themes.BOOTSTRAP  # Tema Bootstrap do DashBootstrapComponents
]


df = pd.read_csv('commons/dados_dashboard.csv')
states_data = json.load(open('commons/states.json'))

options_state = [{"label": states_data[state]['name'], "value": state}
                 for state in states_data.keys()]

options_cause = df['causa_acidente'].unique()


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1("Acidentes em Rodovias Federais 2022", className='title'),
    html.Div(id='alert', className='alert', style={
             'position': 'fixed', 'top': '100px', 'right': '10px', 'zIndex': '9999'}),
    html.Div([
        dcc.Dropdown(id='select_state', options=options_state,
                     value='BR', className='dropdown'),
        dcc.RadioItems(id='select-graph', options=[type.value for type in GraphType], value=GraphType.BAR.value)],
        className='dropdown-state-graph'),
    html.Div(id='input-select-cause', children=[
        dcc.Dropdown(
            placeholder='Selecione as causas...',
            id='select_cause',
            options=options_cause,
            multi=True,
            value=list(get_accidents_causes_array(df, 'BR')))
    ]),
    html.Br(),
    html.Div([
        dcc.Loading(children=[html.Div(
            dcc.Graph(id='map', figure={}, className='map'))], type="circle"),
        dcc.Loading(children=[html.Div(id='graph', children=[
                    dcc.Graph(id='content-graph', figure={})])], type="graph")
    ], className='container'),
    html.Br()
])


''' Lado esquerdo do dashboard '''


@app.callback(
    [Output(component_id='map', component_property='figure')],
    [Input(component_id='select_state', component_property='value')]
)
def update_primary_map(state_selected):
    """
    Atualiza o mapa principal

    Args:
        state_selected (str): Estado selecionado
    Returns:
        list: Componente Graph com o mapa principal atualizado
    """
    global df
    # Atualiza o mapa principal com o estado selecionado
    fig = choropleth_map(df, state_selected)
    update_graph_layout(fig)
    fig.update_layout(coloraxis_colorbar_x=0)
    fig.update_coloraxes(colorbar_tickfont_color='#000',
                         colorbar_title_font_color='#000',
                         colorbar_title_font_size=12,
                         colorbar_tickfont_size=12,
                         colorbar_title_font_family='Sen',
                         colorbar_tickfont_family='Sen',
                         colorbar_bgcolor='rgba(255,255,255,0.2)')

    return [fig]


''' Lado direito do dashboard '''


@ app.callback(
    [Output(component_id='graph', component_property='children')],
    [Input(component_id='select-graph', component_property='value'),
     Input(component_id='select_state', component_property='value')],
    allow_duplicate=True
)
def update_graph_type(graph_selected, state_selected):
    """
    Atualiza o gráfico secundário de acordo com o tipo selecionado

    Args:
        graph_selected (str): Tipo de gráfico selecionado
        state_selected (str): Estado selecionado
    Returns:
        list: Componente Graph com o respectivo gráfico do tipo selecionado
    """
    # Caso o gráfico selecionado seja de dispersão
    if graph_selected == GraphType.SCATTER.value:
        fig = scatter_chart(df, state_selected)
        update_graph_layout(fig)
        fig.update_layout(
            legend=dict(
                orientation="v",
                entrywidth=70,
                yanchor="top",
                y=-0.3,
                xanchor="right",
                x=0.3
            ))
        graph_type = 'scatter'
    # Caso o gráfico selecionado seja de acidentes por mês, será criado um gráfico de linha
    elif graph_selected == GraphType.LINE.value:
        fig = line_chart(df, state_selected)
        update_graph_layout(fig)
        graph_type = 'line'
    # Caso o gráfico selecionado seja de acidentes por causa, será criado um gráfico de barras
    elif graph_selected == GraphType.BAR.value:
        fig = bar_chart(df, state_selected, list(
            get_accidents_causes_array(df, state_selected)))
        update_graph_layout(fig)
        fig.update_layout(
            legend=dict(
                orientation="v",
                entrywidth=70,
                yanchor="top",
                y=-0.1,
                xanchor="left",
                x=0
            ))
        return [dcc.Graph(id='content-graph', figure=fig, className='bar')]
    # Caso o gráfico selecionado seja de acidentes por BR, será criado um mapa de dispersão
    elif graph_selected == GraphType.SCATTER_MAP.value:
        fig = scatter_map(df, state_selected)
        update_graph_layout(fig)
        fig.update_layout(
            legend=dict(
                orientation="h",
                entrywidth=70,
                yanchor="top",
                y=-0.1,
                xanchor="right",
                x=0.5
            ))
        graph_type = 'scatter-map'
    return [dcc.Graph(id='content-graph', figure=fig, className=graph_type)]


@ app.callback(
    [Output(component_id='input-select-cause', component_property='children')],
    [Input(component_id='select-graph', component_property='value'),
     Input(component_id='select_state', component_property='value')]
)
def show_selected_causes(graph_selected, state_selected):
    """
    Atualiza o dropdown de causas de acidente

    Args:
        graph_selected (str): Tipo de gráfico selecionado
        state_selected (str): Estado selecionado
    Returns:
        list: Dropdown de causas
    """
    # Caso o gráfico selecionado seja de acidentes por causa
    if graph_selected == GraphType.BAR.value:
        return [dcc.Dropdown(placeholder='Selecione as causas...', id='select_cause', options=options_cause, multi=True,
                             value=list(get_accidents_causes_array(df, state_selected)))]
    # Caso contrário, o dropdown de causas é ocultado
    return [dcc.Dropdown(style={'display': 'none',  'width': '0px', 'height': '0px'}, value=list(get_accidents_causes_array(df, state_selected)), id='select_cause')]


@app.callback(
    [Output(component_id='content-graph', component_property='figure'),
     Output(component_id='select_cause', component_property='value'),
     Output(component_id='alert', component_property='children')],
    [Input(component_id='select_cause', component_property='value')],
    [State(component_id='select_state', component_property='value'),
     State(component_id='select-graph', component_property='value')],
    prevent_initial_callback=True,
    prevent_initial_call=True,
    allow_duplicate=True
)
def update_causes(cause_selected, state_selected, graph_selected):
    """
    Atualiza o gráfico secundário de acordo com as causas selecionadas

    Args:
        cause_selected (list): Lista de causas selecionadas
        state_selected (str): Estado selecionado
        graph_selected (str): Tipo de gráfico selecionado
    Returns:
        list: Gráfico secundário, lista de causas selecionadas e alerta
    """
    if graph_selected != GraphType.BAR.value:
        return [dash.no_update, dash.no_update, dash.no_update]
    # Número máximo de causas selecionadas
    max_selected = 3
    # Alerta de número máximo de causas selecionadas
    alerts = html.Div(style={'width': '0px', 'height': '0px'})
    if cause_selected is not None:
        if len(cause_selected) > max_selected:
            cause_selected.pop()
            alerts = dbc.Alert(f"Você só pode selecionar {max_selected} causas!",
                               color="warning", duration=4000)
            return [dash.no_update, cause_selected, alerts]
    # Atualiza o gráfico de barras com as causas selecionadas
    fig = bar_chart(df, state_selected, cause_selected)
    update_graph_layout(fig)
    fig.update_layout(
        legend=dict(
            orientation="v",
            entrywidth=70,
            yanchor="top",
            y=-0.1,
            xanchor="left",
            x=0
        ))

    return [fig, cause_selected, alerts]


def update_graph_layout(fig):
    """
    Atualiza o layout dos gráficos

    Args:
        fig (plotly.graph_objects.Figure): Gráfico para atualizar o layout
    """
    fig.update_layout({"title_font_family": 'Sen', "plot_bgcolor": "rgba(0,0,0,0)",
                       "paper_bgcolor": "rgba(0,0,0,0)", "font": {"color": "#FFFFFF"}})


# Inicia o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
