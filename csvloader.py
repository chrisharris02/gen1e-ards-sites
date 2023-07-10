
import pandas as pd
import folium
from folium.plugins import HeatMap
from folium.plugins import MarkerCluster
import numpy as np
from weight_optimization import calculate_weights
from dataloader import load_data
from weight_optimization_rf import calculate_weights_rf
from branca.element import Template, MacroElement
import json

global grabber

def preprocess_data(county_coordinates, smoking_data, copd_data, covid_data, sepsis_data, drowning_data, vaccination_data, flu_data, pneumonia_data):
    state_abbreviations = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
    }
    merged_covid = pd.merge(covid_data, county_coordinates, left_on='fips', right_on='county_fips')
    merged_covid['cases_per_population'] = merged_covid['cases'] / merged_covid['population']
    merged_covid.dropna(subset=['lat', 'lng', 'cases_per_population','id'], inplace=True)
    filtered_covid = merged_covid[(merged_covid['state_name'] != 'Alaska') & (merged_covid['state_name'] != 'Hawaii') & (merged_covid['lat'] < 60)]
    min_covid, max_covid = filtered_covid['cases_per_population'].min(), filtered_covid['cases_per_population'].max()
    normalized_covid = filtered_covid.copy()
    normalized_covid['normalized_covid'] = (filtered_covid['cases_per_population'] - min_covid) / (max_covid - min_covid)

    merged_smoking = pd.merge(county_coordinates, smoking_data, left_on='state_name', right_on='LocationDesc', how='left')
    merged_smoking['Data_Value'].fillna(merged_smoking.groupby('state_name')['Data_Value'].transform('mean'), inplace=True)
    filtered_smoking = merged_smoking[(merged_smoking['state_name'] != 'Alaska') & (merged_smoking['state_name'] != 'Hawaii') & (merged_smoking['lat'] < 60)]
    min_smoking, max_smoking = filtered_smoking['Data_Value'].min(), filtered_smoking['Data_Value'].max()
    normalized_smoking = filtered_smoking.copy()
    normalized_smoking['normalized_smoking'] = (filtered_smoking['Data_Value'] - min_smoking) / (max_smoking - min_smoking)

    merged_copd = pd.merge(copd_data, county_coordinates, left_on='LocationID', right_on='county_fips')
    merged_copd.dropna(subset=['lat', 'lng', 'Percent_COPD','id'], inplace=True)
    filtered_copd = merged_copd[(merged_copd['state_name'] != 'Alaska') & (merged_copd['state_name'] != 'Hawaii') & (merged_copd['lat'] < 60)]
    min_copd, max_copd = 3.2, 15.5
    normalized_copd = filtered_copd.copy()
    normalized_copd['normalized_copd'] = (filtered_copd['Percent_COPD'] - min_copd) / (max_copd - min_copd)

    sepsis_data['STATE_FULL'] = sepsis_data['STATE'].apply(lambda x: state_abbreviations.get(x))
    merged_sepsis = pd.merge(county_coordinates, sepsis_data, left_on='state_name', right_on='STATE_FULL', how='left')
    min_sepsis, max_sepsis = merged_sepsis['RATE'].min(), merged_sepsis['RATE'].max()
    normalized_sepsis = merged_sepsis.copy()
    normalized_sepsis['normalized_sepsis'] = (merged_sepsis['RATE'] - min_sepsis) / (max_sepsis - min_sepsis)

    drowning_data['STATE_FULL'] = drowning_data['State'].apply(lambda x: state_abbreviations.get(x))
    merged_drowning = pd.merge(county_coordinates, drowning_data, left_on='state_name', right_on='STATE_FULL', how='left')
    min_drowning, max_drowning = merged_drowning['Dd'].min(), merged_drowning['Dd'].max()
    normalized_drowning = merged_drowning.copy()
    normalized_drowning['normalized_drowning'] = (merged_drowning['Dd'] - min_drowning) / (max_drowning - min_drowning)

    merged_vaccination = pd.merge(county_coordinates, vaccination_data, left_on='state_name', right_on='Location', how='left')
    min_vaccination, max_vaccination = merged_vaccination['Flu Vaccination Rate'].min(), merged_vaccination['Flu Vaccination Rate'].max()
    normalized_vaccination = merged_vaccination.copy()
    normalized_vaccination['normalized_vaccination'] = (merged_vaccination['Flu Vaccination Rate'] - min_vaccination) / (max_vaccination - min_vaccination)

    merged_flu = pd.merge(county_coordinates, flu_data, left_on='state_name', right_on='STATENAME', how='left')
    min_flu, max_flu = merged_flu['ACTIVITY_LEVEL'].min(), merged_flu['ACTIVITY_LEVEL'].max()
    normalized_flu = merged_flu.copy()
    normalized_flu['normalized_flu'] = (merged_flu['ACTIVITY_LEVEL'] - min_flu) / (max_flu - min_flu)

    pneumonia_data['state_name'] = pneumonia_data['STATE'].apply(lambda x: state_abbreviations.get(x))
    merged_pneumonia = pd.merge(county_coordinates, pneumonia_data, on='state_name', how='left')
    min_pneumonia, max_pneumonia = merged_pneumonia['RATE'].min(), merged_pneumonia['RATE'].max()
    normalized_pneumonia = merged_pneumonia.copy()
    normalized_pneumonia['normalized_pneumonia'] = (merged_pneumonia['RATE'] - min_pneumonia) / (max_pneumonia - min_pneumonia)

    combined_data = pd.merge(normalized_smoking, normalized_copd, on=['lat', 'lng', 'state_name'], suffixes=('_smoking', '_copd'))
    combined_data = pd.merge(combined_data, normalized_covid, on=['lat', 'lng', 'state_name'])
    combined_data = pd.merge(combined_data, normalized_sepsis[['county_fips', 'normalized_sepsis']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_drowning[['county_fips', 'normalized_drowning']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_vaccination[['county_fips', 'normalized_vaccination']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_flu[['county_fips', 'normalized_flu']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_pneumonia[['county_fips', 'normalized_pneumonia']], on='county_fips')
    return combined_data

def weights(combined_data, weight_toggle):
    weights, r2 = calculate_weights_rf('state_data_1.csv')
    weight_toggle_int = [int(i) for i in weight_toggle]
    #weight_toggle_int = [x for x in weight_toggle_int if x not in [8, 9]]
    if 8 in weights:
        weights.remove(8)
    if 9 in weights:
        weights.remove(9)
    storeweights = weights.copy()
    storeweights*=0
    for i in weight_toggle_int:
        storeweights[i] = weights[i]
        
    combined_data['combined_weighted_value'] = (
        storeweights[0] * combined_data['normalized_smoking'] 
        + storeweights[1] * combined_data['normalized_copd']
        + storeweights[2] * combined_data['normalized_covid']
        + storeweights[3] * combined_data['normalized_drowning']
        + storeweights[4] * combined_data['normalized_sepsis']
        + storeweights[5] * combined_data['normalized_flu']
        + storeweights[6] * combined_data['normalized_pneumonia']
        + storeweights[7] * combined_data['normalized_vaccination']
    )
    global hold
    hold = combined_data
    combined_data.dropna(subset=['lat', 'lng', 'combined_weighted_value','id'], inplace=True)
    heatmap_data = combined_data[['lat', 'lng', 'combined_weighted_value','id']].values.tolist()
    df = pd.read_csv('updated_with_state_icu_normalized.csv')
    df['temp'] = df['Hospital Name'].str.lower()
    df = df.drop_duplicates(subset='temp')
    df = df.drop(columns='temp')
        
    df = df.drop_duplicates(subset='Hospital Name')
    locations = [(row['Latitude'], row['Longitude'], row['Hospital Name']) for _, row in df.iterrows()]
    return combined_data, heatmap_data, locations, hold
    
def main(toggles):
    county_coordinates, smoking_data, copd_data, covid_data, sepsis_data, drowning_data, vaccination_data, flu_data, pneumonia_data, ards_centers = load_data()
    combined_data = preprocess_data(county_coordinates, smoking_data, copd_data, covid_data, sepsis_data, drowning_data, vaccination_data, flu_data, pneumonia_data)

    data, heatmap_data, locations, hold = weights(combined_data, toggles)
    grabber = heatmap_data
    list_of_lists = grabber
    seen = {}
    result = []
    for lst in list_of_lists:
        lat_lng = tuple(lst[:2])
        if lat_lng not in seen:
            result.append(lst)
            seen[lat_lng] = True
    df = pd.DataFrame(result, columns=['Latitude', 'Longitude', 'Score', 'ID'])
    df.to_csv('heatmap_coordinate_data.csv', index=False)
    return df