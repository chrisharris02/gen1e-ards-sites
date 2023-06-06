#Adding a top 10 list to the side
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
from flask import Flask, request, redirect, send_from_directory
import time
import json
from flask import Flask, request, render_template
from flask import Flask, render_template, request, session, redirect, url_for


def preprocess_data(county_coordinates, smoking_data, copd_data, covid_data, sepsis_data, drowning_data, vaccination_data, flu_data, pneumonia_data):
    state_abbreviations = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
    }
    merged_covid = pd.merge(covid_data, county_coordinates, left_on='fips', right_on='county_fips')
    merged_covid['cases_per_population'] = merged_covid['cases'] / merged_covid['population']
    merged_covid.dropna(subset=['lat', 'lng', 'cases_per_population'], inplace=True)
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
    merged_copd.dropna(subset=['lat', 'lng', 'Percent_COPD'], inplace=True)
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
    weight_toggle_int = [x for x in weight_toggle_int if x not in [8, 9]]
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
    combined_data.dropna(subset=['lat', 'lng', 'combined_weighted_value'], inplace=True)
    heatmap_data = combined_data[['lat', 'lng', 'combined_weighted_value']].values.tolist()
    df = pd.read_csv('updated_with_state_icu_normalized.csv')
    df['temp'] = df['Hospital Name'].str.lower()
    df = df.drop_duplicates(subset='temp')
    df = df.drop(columns='temp')
        
    df = df.drop_duplicates(subset='Hospital Name')
    locations = [(row['Latitude'], row['Longitude'], row['Hospital Name']) for _, row in df.iterrows()]
    return combined_data, heatmap_data, locations, hold
    

def create_usa_map():
    usa_center_latitude = 40
    usa_center_longitude = -98
    usa_map = folium.Map(location=[usa_center_latitude, usa_center_longitude], zoom_start=4)
    return usa_map

def state_data(combined_data):
    state_data = combined_data.groupby('state_name').mean().reset_index()
    sd = state_data[['state_name','normalized_sepsis', 'normalized_drowning', 'normalized_vaccination', 'normalized_flu', 'normalized_pneumonia', 'normalized_smoking', 'normalized_copd', 'normalized_covid']]
    vals = pd.read_csv('vals.csv')
    sd.to_csv('state_data.csv', index=False)
    sd['vals'] = df_vals['vals']
    return sd


def add_heatmap(usa_map, heatmap_data):
    custom_gradient = {
        0.0: '#0000FF', 
        0.7: '#3399FF',  
        0.89: '#66FF66',  
        0.94: '#FFFF00', 
        1.0: '#FF0000'    
    }
    HeatMap(heatmap_data, gradient=custom_gradient).add_to(usa_map)

def add_marker_cluster(usa_map, locations, data):
    marker_cluster = MarkerCluster().add_to(usa_map)
    for lat, lon, name in locations:
        row = data[data['Hospital Name'] == name]
        if len(row) > 0:
            popup_text = f"<h4>{name}</h4>"
            if pd.notnull(row['URL'].iloc[0]):
                popup_text += f"""
                    <div style="width: 300px;">
                        <strong>Total Successful Studies - Historically:</strong> {row['Total Successful Trials'].iloc[0]}<br>
                        <strong>ICU Beds in the County:</strong> {row['ICU Beds true'].iloc[0]}<br>
                        <strong>Normalized Overall score:</strong> {row['Normalized Composite Scores'].iloc[0]}<br>
                        <strong>Current/Most Recent Study:</strong> {row['Current/Most Recent Study'].iloc[0]}<br>
                        <strong>Status:</strong> {row['Status'].iloc[0]}<br>
                        <strong>Study Results:</strong> {row['Study Results'].iloc[0]}<br>
                        <strong>Interventions:</strong> {row['Interventions'].iloc[0]}<br>
                        <strong>Outcome Measures:</strong> {row['Outcome Measures'].iloc[0]}<br>
                        <strong>Age:</strong> {row['Age'].iloc[0]}<br>
                        <strong>Phases:</strong> {row['Phases'].iloc[0]}<br>
                        <strong>Enrollment:</strong> {row['Enrollment'].iloc[0]}<br>
                        <strong>Study Type:</strong> {row['Study Type'].iloc[0]}<br>
                        <strong>Study Designs:</strong> {row['Study Designs'].iloc[0]}<br>
                        <strong>Completion Date:</strong> {row['Completion Date'].iloc[0]}<br>
                        <strong>URL:</strong> <a href="{row['URL'].iloc[0]}" target="_blank">Link</a><br>
                        <strong>Hospital Name:</strong> {row['Hospital Name'].iloc[0]}<br>
                        <strong>Principal Investigator:</strong> {row['Principal Investigator'].iloc[0]}
                    </div>
                """
            else:
                popup_text += f"""
                    <div style="width: 300px;">
                        <strong>Hospital Name:</strong> {row['Hospital Name'].iloc[0]}<br>
                """
                if pd.notnull(row['Principal Investigator'].iloc[0]):
                    popup_text += f"""
                        <strong>Principal Investigator:</strong> {row['Principal Investigator'].iloc[0]}
                    """
                popup_text += "</div>"
                
            folium.Marker(location=[lat, lon], popup=popup_text).add_to(marker_cluster)



import json
import requests

def add_state_borders_and_labels(usa_map):
    # Url to the raw geojson file
    url = 'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json'

    # Load the geojson file
    geo_json_data = json.loads(requests.get(url).text)

    # Add the state boundaries to the map
    folium.GeoJson(
        geo_json_data,
        name='geojson'
    ).add_to(usa_map)

    # Add the state labels to the map
    style_function = lambda x: {'fillColor': '#ffffff', 
                                'color':'#000000', 
                                'fillOpacity': 0.0, 
                                'weight': 0.0}
    highlight_function = lambda x: {'fillColor': '#000000', 
                                    'color':'#000000', 
                                    'fillOpacity': 0.20, 
                                    'weight': 0.1}
    state_labels = folium.features.GeoJson(
        geo_json_data,
        style_function=style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=['name'],
            aliases=['State:'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"),
            sticky=True
        )
    )
    usa_map.add_child(state_labels)
    usa_map.keep_in_front(state_labels)



def main(weight_toggle, marker_cluster_toggle, list_toggle):
    county_coordinates, smoking_data, copd_data, covid_data, sepsis_data, drowning_data, vaccination_data, flu_data, pneumonia_data, ards_centers = load_data()
    combined_data = preprocess_data(county_coordinates, smoking_data, copd_data, covid_data, sepsis_data, drowning_data, vaccination_data, flu_data, pneumonia_data)

    data, heatmap_data, locations, hold = weights(combined_data, weight_toggle)
    usa_map = create_usa_map()
    add_heatmap(usa_map, heatmap_data)
    merged_final_with_investigator = pd.read_csv('updated_with_state_icu_normalized.csv')

    weight_toggle_list = [int(i) for i in weight_toggle]
    marker_cluster_toggle_list = 8 in weight_toggle_list
    list_toggle_list = 9 in weight_toggle_list
    #weight_toggle_list = [x for x in weight_toggle_list if x not in [8, 9]]
    if marker_cluster_toggle_list:
        add_marker_cluster(usa_map, locations, merged_final_with_investigator)
    add_state_borders_and_labels(usa_map)
    
    
    class CustomMacroElement(MacroElement):
        def __init__(self, html, script, css):
            super().__init__()
            self._template = Template("""
                {% macro header(this, kwargs) %}
                    <style>
                    """ + css + """
                    </style>
                {% endmacro %}
                {% macro html(this, kwargs) %}
                    """ + html + """
                {% endmacro %}
                {% macro script(this, kwargs) %}
                    """ + script + """
                {% endmacro %}
            """)
    if list_toggle_list:
    # Define HTML, CSS and Javascript
        html = """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">

        <div style="position: absolute; top: 10px; right: 10px; z-index: 9999; background-color: #fff; padding: 10px; border: 1px solid #ccc;">

        <img src="https://uploads-ssl.webflow.com/608bbb52742675860410dd77/608bbc12518ab6a69ad28a56_GEn1E%20Logo%20horizontal.png" alt="Logo" style="width: 125px; display: block; margin-left: auto; margin-right: auto;">
        <form id="checkbox-form">
            <fieldset>
                <label>
                    <input class="cb cb1" type="checkbox" name="check" value=0 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Smoking Data</span> 
                </label>
                <label>
                    <input class="cb cb2" type="checkbox" name="check" value=1 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>COPD Data</span> 
                </label>
                <label>
                    <input class="cb cb3" type="checkbox" name="check" value=2 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>COVID-19 Data</span> 
                </label>
                <label>
                    <input class="cb cb4" type="checkbox" name="check" value=3 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Drowning Data</span> 
                </label>
                <label>
                    <input class="cb cb5" type="checkbox" name="check" value=4 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Sepsis Data</span> 
                </label>
                <label>
                    <input class="cb cb6" type="checkbox" name="check" value=5 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Flu Data</span> 
                </label>
                <label>
                    <input class="cb cb7" type="checkbox" name="check" value=6 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Pneumonia Data</span> 
                </label>
                <label>
                    <input class="cb cb8" type="checkbox" name="check" value=7 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Vaccination Data</span> 
                </label>
                <label>
                    <input class="cb cb9" type="checkbox" name="check" value=8 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>ARDS Trial Locations</span> 
                </label>
                <label>
                    <input class="cb cb10" type="checkbox" name="check" value=9 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Top Locations</span> 
                </label>
            </fieldset>
        <div class="submit-area">
            <button type="submit">Compute</button>
        </div>
        <div id="loading-text" style="text-align: center; font-size: 16px; display: none;">GEn1E Ridge Processor</div>
        </form>

    </div> 
    <div style="position: fixed; bottom: 30px; right: 10px; z-index: 9999;">
    <img src="https://uploads-ssl.webflow.com/608bbb52742675860410dd77/647f8bf9ce5c07118bcd4b1e_County%20level%20scoring%20card%20LEGEND.png" alt="Logo" style="width: 214px;">
</div>

    </div> 

    <div id="sidebar">
    <button id="close" onclick="this.parentElement.style.display='none'">×</button>
        <h2>Top Ranked Locations</h2>
<ul id="myList">
    <li>
        <h3>University of Alabama at Birmingham</h3>
        <p>Score: 100 | PI: Carlo Waldemar et al. | Alabama</p>
        <p>6 previous successful trials | 471 ICU Beds</p>
    </li>
    <li>
        <h3>University of Kentucky Chandler Medical Center</h3>
        <p>Score: 98.38 | PI: Hubert Ballard | Kentucky</p>
        <p>3 previous successful trials | 260 ICU Beds</p>
    </li>
    <li>
        <h3>Helen Keller Hospital</h3>
        <p>Score: 92.56 | PI: Amy Lightner | Alabama</p>
        <p>1 previous successful trial | 22 ICU Beds</p>
    </li>
    <li>
        <h3>USA Women and Children’s Hospital</h3>
        <p>Score: 91.62 | PI: James Cummings | Alabama</p>
        <p>1 previous successful trial | 157 ICU Beds</p>
    </li>
    <li>
        <h3>Rockefeller Neuroscience Institute</h3>
        <p>Score: 90.74 | PI: Ali Rezai | West Virginia</p>
        <p>1 previous successful trial | 119 ICU Beds</p>
    </li>
    <li>
        <h3>Medical Affiliated Research Center</h3>
        <p>Score: 86.61 | PI: R Swerdloff | Alabama</p>
        <p>2 previous successful trials | 100 ICU Beds</p>
    </li>
</ul>
    </div>



    <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
        """
        script = """
        
        var checked_values = JSON.parse('""" + json.dumps(weight_toggle_list) + """');
        var initial_selected = [...checked_values];  // copy of the initial checked_values

        $('.cb').each(function() {
            var value = parseInt($(this).val());
            if (checked_values.includes(value)) {
                $(this).prop('checked', true);
            } else {
                $(this).prop('checked', false);
            }
        });

        // Disable the submit button initially
        $('#checkbox-form button[type="submit"]').prop('disabled', true);

        $('.cb').change(function() {
            // When a checkbox changes state, check if the selected checkboxes have changed
            var current_selected = [];
            $("input[type='checkbox']:checked").each(function(){
                current_selected.push(parseInt($(this).val()));
            });

            // If selected checkboxes have changed, enable the submit button. If not, disable it.
            if (JSON.stringify(current_selected.sort()) != JSON.stringify(initial_selected.sort())) {
                $('#checkbox-form button[type="submit"]').prop('disabled', false);
            } else {
                $('#checkbox-form button[type="submit"]').prop('disabled', true);
            }
        });

   var counter = 0;

    function loadingAnimation() {
        var dots = window.setInterval( function() {
            var wait = document.getElementById("loading-text");

            wait.innerHTML = "GEn1E Ridge Processor" + ".".repeat(counter+1);
            counter = (counter + 1) % 3;
        }, 1000);
        return dots;
    };


$('#checkbox-form').submit(function(e){
    e.preventDefault();
    var selected = [];
    $("input[type='checkbox']:checked").each(function(){
        selected.push($(this).val());
    });
    // Show loading text and start the animation
    $("#loading-text").css("display", "block");
    var dots = loadingAnimation(); // Start the loading animation
    $.ajax({
        url: '/checkboxes',
        type: 'post',
        contentType: 'application/json',
        data : JSON.stringify(selected),
        success: function(){
            window.location.href = "/result";
        },
        complete: function(){
            // Hide loading text and stop the animation
            $("#loading-text").css("display", "none");
            clearInterval(dots);
        }
    });
});

        """


        css = """
        *, *:before, *:after {
            box-sizing: border-box; 
        }

        html {
            font-size: 13.5px;
        }

        fieldset {
            display: block;
        }

        label {
            font-family: "Montserrat", sans-serif;
            font-size: 0.9rem;
            cursor: pointer;
            display: block;
            margin: 0.75em;
        }

        label > input {
            display: none;
        }

        label span {
            color: #6A759B;
        }

        label i {
            display: inline-block;
            width: 48px;
            height: 30px;
            border-radius: 15px;
            vertical-align: middle;
            transition: .25s .09s;
            position: relative;
            background: #deeff7;
        }

        label i:after {
            content: " ";
            display: block;
            width: 22.5px;
            height: 22.5px;
            top: 3.75px;
            left: 3.75px;
            border-radius: 50%;
            background: #fff;
            position: absolute;
            box-shadow: 1px 2px 4px 0 rgba(#000, .4);
            transition: .15s;
        }

        label > input:checked + i {
            background: #1094fb;
        }

        label > input:checked + i + span {
            color: #29316b;
        }

        label > input:checked + i:after {
            transform: translateX(18.75px);
        }

        button {
            font-family: "Montserrat", sans-serif;
            font-size: 0.9rem;
            color: #ffffff;
            background-color: #1094fb;
            border: none;
            padding: 10px;
            border-radius: 5px;
            cursor: pointer;
            display: block;
            margin: 10px auto;
        }
        #checkbox-form button[type="submit"]:disabled {
            background-color: lightgrey;
            cursor: not-allowed;
        }

    #sidebar {
        position: absolute;
        top: 10px;
        left: 10px;
        z-index: 9999;
        background: linear-gradient(135deg, #81d4fa 0%, #0288d1 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px 0 rgba(129, 212, 250, 0.4);
        width: 382.5px; 
    }

    h2 {
        color: #fff;
        font-size: 24px;
        font-weight: 500;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    }

    #myList {
        list-style: none;
        padding-left: 0;
    }

    #myList li {
        padding: 15px 15px 15px; /* Reduced top padding */
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 0.8);
        margin-bottom: 10px;
        transition: transform .2s;
    }

    #myList li:hover {
        transform: scale(1.02);
    }

    #myList li h3 {
        margin: 0 0 5px 0; 
        color: #0288d1;
        font-size: 18px;
    }

    #myList li p {
        margin: 0;
        color: #333;
        font-size: 14px;
    }
    #close {
    position: absolute;
    right: 10px;
    top: 10px;
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #fff;
}
        """
    else:
        html = """
        <div style="position: absolute; top: 10px; right: 10px; z-index: 9999; background-color: #fff; padding: 10px; border: 1px solid #ccc;">

        <img src="https://uploads-ssl.webflow.com/608bbb52742675860410dd77/608bbc12518ab6a69ad28a56_GEn1E%20Logo%20horizontal.png" alt="Logo" style="width: 125px; display: block; margin-left: auto; margin-right: auto;">
        <form id="checkbox-form">
            <fieldset>
                <label>
                    <input class="cb cb1" type="checkbox" name="check" value=0 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Smoking Data</span> 
                </label>
                <label>
                    <input class="cb cb2" type="checkbox" name="check" value=1 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>COPD Data</span> 
                </label>
                <label>
                    <input class="cb cb3" type="checkbox" name="check" value=2 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>COVID-19 Data</span> 
                </label>
                <label>
                    <input class="cb cb4" type="checkbox" name="check" value=3 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Drowning Data</span> 
                </label>
                <label>
                    <input class="cb cb5" type="checkbox" name="check" value=4 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Sepsis Data</span> 
                </label>
                <label>
                    <input class="cb cb6" type="checkbox" name="check" value=5 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Flu Data</span> 
                </label>
                <label>
                    <input class="cb cb7" type="checkbox" name="check" value=6 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Pneumonia Data</span> 
                </label>
                <label>
                    <input class="cb cb8" type="checkbox" name="check" value=7 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Vaccination Data</span> 
                </label>
                <label>
                    <input class="cb cb9" type="checkbox" name="check" value=8 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>ARDS Trial Locations</span> 
                </label>
                <label>
                    <input class="cb cb10" type="checkbox" name="check" value=9 onclick="cbChange(this)"/>
                    <i></i> 
                    <span>Top Locations</span> 
                </label>
            </fieldset>
        <div class="submit-area">
            <button type="submit">Compute</button>
        </div>
        <div id="loading-text" style="text-align: center; font-size: 16px; display: none;">GEn1E Ridge Processor</div>
        
        </form>
    </div> 
    <div style="position: fixed; bottom: 30px; right: 10px; z-index: 9999;">
    <img src="https://uploads-ssl.webflow.com/608bbb52742675860410dd77/647f8bf9ce5c07118bcd4b1e_County%20level%20scoring%20card%20LEGEND.png" alt="Logo" style="width: 214px;">
</div>
        """
        script = """
        
        var checked_values = JSON.parse('""" + json.dumps(weight_toggle_list) + """');
        var initial_selected = [...checked_values];  // copy of the initial checked_values

        $('.cb').each(function() {
            var value = parseInt($(this).val());
            if (checked_values.includes(value)) {
                $(this).prop('checked', true);
            } else {
                $(this).prop('checked', false);
            }
        });

        // Disable the submit button initially
        $('#checkbox-form button[type="submit"]').prop('disabled', true);

        $('.cb').change(function() {
            // When a checkbox changes state, check if the selected checkboxes have changed
            var current_selected = [];
            $("input[type='checkbox']:checked").each(function(){
                current_selected.push(parseInt($(this).val()));
            });

            // If selected checkboxes have changed, enable the submit button. If not, disable it.
            if (JSON.stringify(current_selected.sort()) != JSON.stringify(initial_selected.sort())) {
                $('#checkbox-form button[type="submit"]').prop('disabled', false);
            } else {
                $('#checkbox-form button[type="submit"]').prop('disabled', true);
            }
        });

    var counter = 0;

    function loadingAnimation() {
        var dots = window.setInterval( function() {
            var wait = document.getElementById("loading-text");

            wait.innerHTML = "GEn1E Ridge Processor" + ".".repeat(counter+1);
            counter = (counter + 1) % 3;
        }, 1000);
        return dots;
    };


$('#checkbox-form').submit(function(e){
    e.preventDefault();
    var selected = [];
    $("input[type='checkbox']:checked").each(function(){
        selected.push($(this).val());
    });
    // Show loading text and start the animation
    $("#loading-text").css("display", "block");
    var dots = loadingAnimation(); // Start the loading animation
    $.ajax({
        url: '/checkboxes',
        type: 'post',
        contentType: 'application/json',
        data : JSON.stringify(selected),
        success: function(){
            window.location.href = "/result";
        },
        complete: function(){
            // Hide loading text and stop the animation
            $("#loading-text").css("display", "none");
            clearInterval(dots);
        }
    });
});


        """


        css = """
        *, *:before, *:after {
            box-sizing: border-box; 
        }

        html {
            font-size: 13.5px;
        }

        fieldset {
            display: block;
        }

        label {
            font-family: "Montserrat", sans-serif;
            font-size: 0.9rem;
            cursor: pointer;
            display: block;
            margin: 0.75em;
        }

        label > input {
            display: none;
        }

        label span {
            color: #6A759B;
        }

        label i {
            display: inline-block;
            width: 48px;
            height: 30px;
            border-radius: 15px;
            vertical-align: middle;
            transition: .25s .09s;
            position: relative;
            background: #deeff7;
        }

        label i:after {
            content: " ";
            display: block;
            width: 22.5px;
            height: 22.5px;
            top: 3.75px;
            left: 3.75px;
            border-radius: 50%;
            background: #fff;
            position: absolute;
            box-shadow: 1px 2px 4px 0 rgba(#000, .4);
            transition: .15s;
        }

        label > input:checked + i {
            background: #1094fb;
        }

        label > input:checked + i + span {
            color: #29316b;
        }

        label > input:checked + i:after {
            transform: translateX(18.75px);
        }

        button {
            font-family: "Montserrat", sans-serif;
            font-size: 0.9rem;
            color: #ffffff;
            background-color: #1094fb;
            border: none;
            padding: 10px;
            border-radius: 5px;
            cursor: pointer;
            display: block;
            margin: 10px auto;
        }
        #checkbox-form button[type="submit"]:disabled {
            background-color: lightgrey;
            cursor: not-allowed;
        }
        
        """        

    # Create custom Macro Element
    macro = CustomMacroElement(html, script, css)

    # Add custom Macro Element to map
    usa_map.get_root().add_child(macro)

    usa_map.save('togglenow3.html')

app = Flask(__name__, template_folder='/app')
app.secret_key = 'your_secret_key'  # Set a secret key for session encryption

PASSWORD = 'test'  # Set your desired password here

def authenticate(password):
    return password == PASSWORD

@app.route('/')
def index():
    if 'authenticated' in session and session['authenticated']:
        return render_template('starting_map_loader_revamped.html')
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if authenticate(password):
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message='Invalid password')
    else:
        return render_template('login.html', message='')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('index'))

@app.route('/checkboxes', methods=['POST'])
def checkboxes():
    if 'authenticated' not in session or not session['authenticated']:
        return redirect(url_for('login'))
    indexes = request.get_json()
    print(indexes)  # print out the received indexes
    time.sleep(10)  # pause for 10 seconds


    main(indexes, indexes, indexes)  # assuming you have a function named 'create_html' that creates the new HTML file
    #time.sleep(10)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

    # Rest of your code

@app.route('/result')
def result():
    if 'authenticated' not in session or not session['authenticated']:
        return redirect(url_for('login'))
    return send_from_directory('/app', 'togglenow3.html')  # send the file from the server
    # Rest of your code
import threading

def run_app():
    app.run(threaded=True, host="0.0.0.0", port=80)


if __name__ == "__main__":
    t = threading.Thread(target=run_app)
    t.start()