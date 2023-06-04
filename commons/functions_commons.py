from pyUFbr.baseuf import ufbr
import pandas as pd
import plotly.express as px
from urllib.request import urlopen
import json
from unidecode import unidecode

def get_data_from(url):
     while(True):
               with urlopen(url) as response:
                    try:
                         state_json = json.load(response)
                         return state_json
                    except:
                         continue
                    
def get_state_number(state):
    url = 'https://servicodados.ibge.gov.br/api/v1/localidades/estados'
    if state == 'BR':
        return 100
    else:
        data = get_data_from(url)
        for uf in data:
                if uf['sigla'] == state:
                    return uf['id']
        
def import_geoJSON(state):
    id = get_state_number(state)
    url = f'https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-{id}-mun.json'
    if (state == 'BR'):
            geoJSON  = json.load(open('commons/brazil_geo.json'))
            return geoJSON
    return get_data_from(url)


def create_state(df,state):
    if state != 'BR':
        UF = df[df['uf']==state]
        UF = UF.groupby(["municipio","id"],as_index=False)["id"].value_counts()
        UF = pd.DataFrame(UF['municipio'].value_counts()).reset_index()
        UF = UF.sort_values('municipio')
    else:
        UF = df
        UF = UF.groupby(["uf","id"],as_index=False)["id"].value_counts()
        UF = pd.DataFrame(UF['uf'].value_counts()).reset_index()
        UF = UF.sort_values('uf')
    return UF



def code_city_df(df,state):
    number =  get_state_number(state)
    url = f'https://servicodados.ibge.gov.br/api/v1/localidades/estados/{number}/municipios'
    data=get_data_from(url)
    cidades = []
    for city in data:
        cidades.append(unidecode(city['nome'].upper()).replace("'",'')) 
    cities_and_code = {}
    for city in df['municipio'].unique():
        city_index = cidades.index(city)
        cities_and_code[city] = int(data[city_index]['id'])
    df['id'] = df['municipio'].apply(lambda x: cities_and_code[x])
    df = df.reset_index()
    del df['index']
    df=df.sort_values('count')
    return df



def create_map(df,state):
    locations_key = 'uf' if state == "BR" else 'id'
    col_key = 'uf' if state == "BR" else 'municipio'
    show_data = {'count':True,col_key:False} if state == 'BR' else {'id':False,'count':True,col_key:False} 
    return px.choropleth_mapbox(
                        df, 
                        geojson= import_geoJSON(state), 
                        locations=locations_key,
                        featureidkey="properties.id" if state != "BR" else None,
                        color='count',
                        range_color=(df['count'].min(),df['count'].max()),
                        hover_data= show_data,
                        mapbox_style = 'open-street-map',
                        center = {'lat': -7.11532,'lon':-34.861},
                        opacity=0.9,
                        color_continuous_scale='Viridis',
                        title = f'Acidentes no estado: {state}',
                        hover_name= col_key,   
                        zoom = 6,
                        labels={'count':'Quantidade de acidentes '}
                        )
