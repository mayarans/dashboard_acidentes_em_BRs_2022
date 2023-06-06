import pandas as pd
import plotly.express as px
from urllib.request import urlopen
import json

states_data = {
    'AC':{
        'cod':12,
        'lat':-9.974,
        'lon':-67.8076
    },
    'AM':{
        'cod':13,
        'lat':-5.62836,
        'lon':-63.1835
    },
    'RR':{
        'cod':14,
        'lat':2.81954,
        'lon':-60.6714  
    },
    'RO' :{
        'cod':11,
        'lat':-8.76183,
        'lon':-63.902 
    },
    'PA' :{
        'cod':15,
        'lat':-1.45502,
        'lon':-48.5024 
    },
    'AP' :{
        'cod':16,
        'lat':-1.45502,
        'lon':-51.0666 
    },
}
def get_data_from(url):
        with urlopen(url) as response:
            state_json=  json.load(response)
        return state_json
          
def import_geoJSON(state):
    if (state == 'BR'):
            geoJSON  = json.load(open('commons/brazil_geo.json'))
            return geoJSON
    id = states_data[state]['cod']
    url = f'https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-{id}-mun.json'
    return get_data_from(url)


def create_state(df,state):
    if state != 'BR':
        UF = df[df['uf']==state]
        UF = UF.groupby(["municipio","id_da_cidade",'id'],as_index=False)["id"].value_counts()
        UF = pd.DataFrame(UF[['municipio','id_da_cidade']].value_counts()).reset_index()
        UF = UF.sort_values('municipio')
    else:
        UF = df
        UF = UF.groupby(["uf","id"],as_index=False)["id"].value_counts()
        UF = pd.DataFrame(UF['uf'].value_counts()).reset_index()
        UF = UF.sort_values('uf')
    return UF


def create_map(df,state):
    locations_key = 'uf' if state == "BR" else 'id_da_cidade'
    col_key = 'uf' if state == "BR" else 'municipio'
    show_data = {'count':True,col_key:False} if state == 'BR' else {'id_da_cidade':False,'count':True,col_key:False} 
    geo_data =  {'lat':-15.7801, 'lon':-47.9292} if state== 'BR' else {'lat': states_data[state] ['lat'],'lon':states_data[state] ['lon']}
    title = "Acidentes nos estados brasileiros" if state == 'BR' else f'Acidentes no estado: {state}'

    return px.choropleth_mapbox(
                        df, 
                        geojson= import_geoJSON(state), 
                        locations=locations_key,
                        featureidkey="properties.id" if state != "BR" else None,
                        color='count',
                        range_color=(df['count'].min(),df['count'].max()),
                        hover_data= show_data,
                        mapbox_style = 'open-street-map',
                        center = geo_data,
                        opacity=0.9,
                        color_continuous_scale='Viridis',
                        title = title,
                        hover_name= col_key,   
                        zoom = 2 if state == 'BR' else 4,
                        labels={'count':'Quantidade de acidentes '}
                        )

def choropleth_map(df,state):
     subseted_df = create_state(df,state)
     return create_map(subseted_df,state)

def subset_df_monthly(df,state):
    df_month = df
    if (state=='BR'):
        df_month['mes'] = pd.to_datetime(df_month['data'],format='mixed').dt.strftime("%m")
        df_month['mes'] = pd.to_datetime(df_month['data'],format='mixed').dt.strftime("%m")
        df_month = df_month.groupby(['mes','id','uf'],as_index=False)['id'].value_counts()
        df_month = df_month['mes'].value_counts().reset_index().sort_values('mes')
        df_month['mes']=df_month['mes'].astype('int64')
        df_month['mes_nome'] = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
        return df_month
    
    df_month['mes'] = pd.to_datetime(df_month['data'],format='mixed').dt.strftime("%m")
    df_month = df_month.groupby(['mes','id','uf'],as_index=False)['id'].value_counts()
    df_month = df_month[['mes','uf']].value_counts().reset_index()
    df_month = df_month[df_month['uf']==state]
    df_month = df_month[['mes','count']].sort_values('mes')
    df_month['mes']=df_month['mes'].astype('int64')
    df_month['mes_nome'] = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    return df_month

def create_line_chart(df,state):
    title = f'Acidentes por mês no estado: {state}' if state !='BR' else f'Acidentes por no mês no Brasil: {state}'
    return px.line(
            df, 
            x='mes_nome', 
            y="count", 
            hover_data={'count':True,'mes_nome':True},
            title=title,
            markers=True,
            labels={'x':'Meses','count':'Quantidade de acidentes','mes_nome':'Mês'},
            range_x=[-0.04,11.04]
            )

def line_chart(df,state):
    state = state.upper()
    subseted_df = subset_df_monthly(df,state)
    return create_line_chart(subseted_df,state)

