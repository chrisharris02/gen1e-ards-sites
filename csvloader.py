
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

def preprocess_data(county_coordinates, smoking_data, copd_data, covid_data, sepsis_data, drowning_data, vaccination_data, flu_data, pneumonia_data, literacy_rates, incomes, age, seniors, health_insurance):
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

        #CHRIS: Additional Factor 1
    literacy_rates["Literacy Rate"] = literacy_rates["Literacy Rate"].str.replace("%", "").astype(float)
    merged_literacy = pd.merge(county_coordinates, literacy_rates, left_on='state_name', right_on='State', how='left')
    min_literacy, max_literacy = merged_literacy['Literacy Rate'].min(), merged_literacy['Literacy Rate'].max()
    normalized_literacy = merged_literacy.copy()
    normalized_literacy['normalized_literacy'] = (merged_literacy['Literacy Rate'] - min_literacy) / (max_literacy - min_literacy)
    normalized_literacy['normalized_literacy'] = 1 - normalized_literacy['normalized_literacy']

    #CHRIS: Additional factor 2
    merged_seniors = pd.merge(county_coordinates, seniors, left_on='state_name', right_on='State', how='left')
    min_seniors, max_seniors = merged_seniors['Percent'].min(), merged_seniors['Percent'].max()
    normalized_seniors = merged_seniors.copy()
    normalized_seniors['normalized_seniors'] = (merged_seniors['Percent'] - min_seniors) / (max_seniors - min_seniors)
    normalized_seniors['normalized_seniors'] = 1 - normalized_seniors['normalized_seniors']


    #CHRIS: Additional Factor 3
    colnames = incomes.columns.tolist()
    colnames[0] = 'County'
    colnames[1] = 'Income'
    incomes.columns = colnames
    merged_incomes = pd.merge(incomes, county_coordinates, left_on='County', right_on='county')
    merged_incomes.dropna(subset=['lat', 'lng', 'Income','id'], inplace=True)
    merged_incomes['Income'] = merged_incomes['Income'].str.replace(',', '').astype(float)
    filtered_incomes = merged_incomes[(merged_incomes['state_name'] != 'Alaska') & (merged_incomes['state_name'] != 'Hawaii') & (merged_incomes['lat'] < 60)]
    min_incomes, max_incomes = merged_incomes['Income'].min(), merged_incomes['Income'].max()
    normalized_incomes = filtered_incomes.copy()
    normalized_incomes['normalized_incomes'] = (filtered_incomes['Income'] - min_incomes) / (max_incomes - min_incomes)
    normalized_incomes['normalized_incomes'] = 1 - normalized_incomes['normalized_incomes']


    #CHRIS: Additional Factor 4
    normalized_health_insurance = health_insurance.rename(columns={'Percent': 'normalized_health_insurance'})
    min_insurance, max_insurance = normalized_health_insurance['normalized_health_insurance'].min(), normalized_health_insurance['normalized_health_insurance'].max()
    normalized_health_insurance['normalized_health_insurance'] = (normalized_health_insurance['normalized_health_insurance'] - min_insurance)/(max_insurance - min_insurance)

    combined_data = pd.merge(normalized_smoking, normalized_copd, on=['lat', 'lng', 'state_name'], suffixes=('_smoking', '_copd'))
    combined_data = pd.merge(combined_data, normalized_covid, on=['lat', 'lng', 'state_name'])
    combined_data = pd.merge(combined_data, normalized_sepsis[['county_fips', 'normalized_sepsis']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_drowning[['county_fips', 'normalized_drowning']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_vaccination[['county_fips', 'normalized_vaccination']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_flu[['county_fips', 'normalized_flu']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_pneumonia[['county_fips', 'normalized_pneumonia']], on='county_fips')
        #CHRIS: Merging additional factors
    combined_data = pd.merge(combined_data, normalized_literacy[['county_fips', 'normalized_literacy']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_seniors[['county_fips', 'normalized_seniors']], on='county_fips')
    combined_data = pd.merge(combined_data, normalized_incomes, on=['lat', 'lng', 'state_name'])
    combined_data = combined_data[combined_data['date'] == '2023-01-01']
    combined_data = pd.merge(combined_data, normalized_health_insurance, on=["county_full_y", "state_name"], how="left")

    global temp
    temp = combined_data
    return combined_data, temp

def weights(combined_data, weight_toggle):
    weights, r2 = calculate_weights_rf('state_data_2.csv')
    weights = np.append(weights, 0.2)
    weight_toggle_int = [int(i) for i in weight_toggle]
    #weight_toggle_int = [x for x in weight_toggle_int if x not in [8, 9]]
    # if 8 in weights:
    #     weights.remove(8)
    # if 9 in weights:
    #     weights.remove(9)
    storeweights = weights.copy()
    storeweights*=0
    for i in weight_toggle_int:
        storeweights[i] = weights[i]



    #CHRIS: Code to scale
    #CHANGE FOR SCALING
    sum_of_weights = sum(storeweights[i] for i in range(len(storeweights)))
    print('Original sum of weights', sum_of_weights)
    scaling_factor = 1/sum_of_weights
    new_sum = sum_of_weights*scaling_factor
    print('New sum', new_sum)
    storeweights = [i * scaling_factor for i in storeweights]
    mainsum = sum(storeweights[i] for i in range(len(storeweights)))
    print('Main sum', mainsum)
    #End of code to scale
    combined_data['combined_weighted_value'] = (
        storeweights[0] * combined_data['normalized_smoking'] 
        + storeweights[1] * combined_data['normalized_copd']
        + storeweights[2] * combined_data['normalized_covid']
        + storeweights[3] * combined_data['normalized_drowning']
        + storeweights[4] * combined_data['normalized_sepsis']
        + storeweights[5] * combined_data['normalized_flu']
        + storeweights[6] * combined_data['normalized_pneumonia']
        + storeweights[7] * combined_data['normalized_vaccination']
        + storeweights[8] * combined_data['normalized_literacy']
        + storeweights[9] * combined_data['normalized_incomes']
        + storeweights[10] * combined_data['normalized_seniors']
        + storeweights[11] * combined_data['normalized_health_insurance']
    )
    global hold
    hold = combined_data
    heatmap_data = combined_data[['lat', 'lng', 'combined_weighted_value','id']].values.tolist()
    df = pd.read_csv('updated_with_state_icu_normalized.csv')
    df['temp'] = df['Hospital Name'].str.lower()
    df = df.drop_duplicates(subset='temp')
    df = df.drop(columns='temp')
        
    df = df.drop_duplicates(subset='Hospital Name')
    locations = [(row['Latitude'], row['Longitude'], row['Hospital Name']) for _, row in df.iterrows()]
    return combined_data, heatmap_data, locations, hold
    
def main(toggles):
 #CHRIS: Additional factors added
    county_coordinates, smoking_data, copd_data, covid_data, sepsis_data, drowning_data, vaccination_data, flu_data, pneumonia_data, ards_centers, literacy_rates, incomes, age, seniors, health_insurance = load_data()
    combined_data, temp = preprocess_data(county_coordinates, smoking_data, copd_data, covid_data, sepsis_data, drowning_data, vaccination_data, flu_data, pneumonia_data, literacy_rates, incomes, age, seniors, health_insurance)
    temp.to_csv('temp_debug.csv', index=False)
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