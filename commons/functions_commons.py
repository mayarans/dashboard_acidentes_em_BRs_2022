import json
from urllib.request import urlopen

import pandas as pd
import plotly.express as px
import plotly.io as io

io.templates.default = 'plotly_dark'
px.colors.qualitative

states_data = json.load(open('commons/states.json'))


def get_data_from(url):
    with urlopen(url) as response:
        state_json = json.load(response)
    return state_json


def import_geoJSON(state):
    if (state == 'BR'):
        geoJSON = json.load(open('commons/brazil_geo.json'))
        return geoJSON
    id = states_data[state]['cod']
    url = f'https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-{id}-mun.json'
    return get_data_from(url)


def create_state(df, state):
    if state != 'BR':
        UF = df[df['uf'] == state]
        UF = UF.groupby(["municipio", "id_da_cidade", 'id'],
                        as_index=False)["id"].value_counts()
        UF = pd.DataFrame(UF[['municipio', 'id_da_cidade']
                             ].value_counts()).reset_index()
        UF = UF.sort_values('municipio')
    else:
        UF = df
        UF = UF.groupby(["uf", "id"], as_index=False)["id"].value_counts()
        UF = pd.DataFrame(UF['uf'].value_counts()).reset_index()
        UF = UF.sort_values('uf')
    return UF


def create_map(df, state):
    locations_key = 'uf' if state == "BR" else 'id_da_cidade'
    col_key = 'uf' if state == "BR" else 'municipio'
    show_data = {'count': True, col_key: False} if state == 'BR' else {
        'id_da_cidade': False, 'count': True, col_key: False}
    geo_data = {'lat': states_data[state]
                ['lat'], 'lon': states_data[state]['lon']}
    title = "Acidentes nos estados brasileiros" if state == 'BR' else f'Acidentes no estado: {state}'

    return px.choropleth_mapbox(
        df,
        geojson=import_geoJSON(state),
        locations=locations_key,
        featureidkey="properties.id" if state != "BR" else None,
        color='count',
        range_color=(df['count'].min(), df['count'].max()),
        hover_data=show_data,
        mapbox_style='open-street-map',
        center=geo_data,
        opacity=0.9,
        color_continuous_scale='darkmint',
        title=title,
        hover_name=col_key,
        zoom=states_data[state]['zoom'],
        height=600

    )


def choropleth_map(df, state):
    subseted_df = create_state(df, state)
    return create_map(subseted_df, state)


def subset_df_monthly(df, state):
    df_month = df
    if (state == 'BR'):
        df_month['mes'] = pd.to_datetime(
            df_month['data'], format='mixed').dt.strftime("%m")
        df_month = df_month.groupby(['mes', 'id', 'uf'], as_index=False)[
            'id'].value_counts()
        df_month = df_month['mes'].value_counts(
        ).reset_index().sort_values('mes')
        df_month['mes'] = df_month['mes'].astype('int64')
        df_month['mes_nome'] = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai',
                                'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        return df_month

    df_month['mes'] = pd.to_datetime(
        df_month['data'], format='mixed').dt.strftime("%m")
    df_month = df_month.groupby(['mes', 'id', 'uf'], as_index=False)[
        'id'].value_counts()
    df_month = df_month[['mes', 'uf']].value_counts().reset_index()
    df_month = df_month[df_month['uf'] == state]
    df_month = df_month[['mes', 'count']].sort_values('mes')
    df_month['mes'] = df_month['mes'].astype('int64')
    df_month['mes_nome'] = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai',
                            'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    return df_month


def create_line_chart(df, state):
    title = f'Acidentes por mês no estado: {state}' if state != 'BR' else f'Acidentes por mês no Brasil'
    return px.line(
        df,
        x='mes_nome',
        y="count",
        hover_data={'count': True, 'mes_nome': True},
        title=title,
        markers=True,
        labels={'x': 'Meses', 'count': 'Quantidade de acidentes',
                'mes_nome': 'Mês'},
        range_x=[-0.04, 11.04],
        height=600
    )


def line_chart(df, state):
    state = state.upper()
    subseted_df = subset_df_monthly(df, state)
    return create_line_chart(subseted_df, state)


def subset_df_by_deaths_and_climate_conditions(df, state):
    df_subseted_by_state = df[df['uf'] == state] if state != 'BR' else df
    df_subseted = df_subseted_by_state.groupby(
        ['condicao_metereologica', 'fase_dia'])['mortos'].sum()
    df_subseted = pd.DataFrame(df_subseted)
    df_subseted = df_subseted.reset_index()

    df_subseted_climate = df_subseted_by_state[[
        'condicao_metereologica', 'id', 'fase_dia']].drop_duplicates()
    final_df = pd.DataFrame(df_subseted_climate[[
                            'condicao_metereologica', 'fase_dia']].value_counts()).reset_index()
    final_df = pd.merge(df_subseted, final_df, on=[
                        'condicao_metereologica', 'fase_dia'], how='left')
    final_df = final_df[final_df['condicao_metereologica'] != 'Ignorado']
    final_df = final_df.sort_values('count')
    sort_dict = {'Amanhecer': 0, 'Pleno dia': 1,
                 'Anoitecer': 2, 'Plena Noite': 3}
    final_df['ref'] = final_df['fase_dia'].apply(lambda x: sort_dict[x])
    final_df = final_df.sort_values('ref')
    return final_df


def create_scatter(df):
    df = df.rename(columns={'fase_dia': 'turno'})
    return px.scatter(
        df,
        x='mortos',
        y='count',
        color='condicao_metereologica',
        facet_col='turno',
        log_y=True,
        log_x=True,
        height=600,
    )


def scatter_chart(df, state):
    state = state.upper()
    subseted_df = subset_df_by_deaths_and_climate_conditions(df, state)
    return create_scatter(subseted_df)


def subset_df_by_accident(df, state):
    subseted_df = df[df['uf'] == state] if state != 'BR' else df
    df = subseted_df.groupby(["municipio", 'id', 'latitude', 'longitude', 'condicao_metereologica', 'br',
                             'fase_dia', 'classificacao_acidente', 'causa_acidente', 'data', 'km'], as_index=False)["id"].value_counts()
    df['br'] = df['br'].astype(str)
    df['br'] = df['br'].apply(lambda x: x.replace('.0', ''))
    df[df['br'] == '0'] = df[df['br'] == '0'].apply(
        lambda x: x.replace('0', 'Não identificado'))
    df['mes'] = pd.to_datetime(df['data'], format='mixed').dt.strftime("%m")
    df = df.sort_values('mes')
    df['mes'] = df['mes'].astype('int64')
    sort_dict = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai',
                 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    df['mes_nome'] = df['mes'].apply(lambda x: sort_dict[x])
    return df


def create_scatter_map(df, state):
    return px.scatter_mapbox(
        df,
        lat='latitude',
        lon='longitude',
        color='br',
        hover_data={'municipio': True, 'id': False, 'latitude': False, 'longitude': False, 'condicao_metereologica': True, 'br': True,
                    'classificacao_acidente': True, 'count': True, 'causa_acidente': True, 'mes': False, "mes_nome": True, 'km': True},
        mapbox_style='open-street-map',
        color_discrete_sequence=px.colors.qualitative.Prism,
        size='count',
        zoom=states_data[state]['zoom'] if state != 'BR' else 1.2
    )


def scatter_map(df, state):
    state = state.upper()
    subseted_df = subset_df_by_accident(df, state)
    return create_scatter_map(subseted_df, state)


def subset_df_by_cause_of__accident_and_climate_conditions(df, state, list_of_causes):
    subset_df = df[df['uf'] == state] if state != 'BR' else df
    subset_df = subset_df.groupby(
        ['causa_acidente', 'condicao_metereologica'], as_index=False)['id'].value_counts()
    subset_df = pd.DataFrame(
        subset_df[['causa_acidente', 'condicao_metereologica']]).value_counts().reset_index()
    subset_df = subset_df[subset_df['causa_acidente'].isin(
        list_of_causes)] if list_of_causes else subset_df[subset_df['causa_acidente'] == 'abc']
    subset_df = subset_df.sort_values(['count', 'condicao_metereologica'])
    return subset_df


def create_bar_chart(df, state):
    return px.bar(
        df,
        x='count',
        y='condicao_metereologica',
        color='causa_acidente',
        log_x=True,
        orientation='h',
        text='count',
        color_discrete_sequence=px.colors.qualitative.Prism,
        height=600,
    )


def bar_chart(df, state, list_of_causes):
    state = state.upper()
    subseted_df = subset_df_by_cause_of__accident_and_climate_conditions(
        df, state, list_of_causes)
    return create_bar_chart(subseted_df, state)


def get_accidents_causes_array(df, state):
    subset_df = df[df['uf'] == state] if state != 'BR' else df
    subset_df = subset_df.groupby(
        ['causa_acidente', 'condicao_metereologica'], as_index=False)['id'].value_counts()
    subset_df = pd.DataFrame(
        subset_df[['causa_acidente', 'condicao_metereologica']]).value_counts().reset_index()
    final_df = subset_df.sort_values('count', ascending=False)
    final_df = final_df.head(3)
    return final_df['causa_acidente'].unique()
