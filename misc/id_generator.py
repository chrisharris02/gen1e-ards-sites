import csv
import geojson
from shapely.geometry import shape, Point
import io

# Load the GeoJSON file with county polygons
with open('misc/us_counties.json', encoding='latin-1') as file:
    county_data = geojson.load(file)

county_polygons = [shape(feature['geometry']) for feature in county_data['features']]

# Open the CSV file and create a list to store matching features
matching_features = []

with open('ards_data/uscounties.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        latitude = float(row['lat'])
        longitude = float(row['lng'])
        point = Point(longitude, latitude)
        feature_props = {'ID': str(row['id']) + '.0'}
        is_within_county = False

        for county_polygon in county_polygons:
            if county_polygon.contains(point):
                matching_feature = geojson.Feature(geometry=county_polygon, properties=feature_props)
                matching_features.append(matching_feature)
                is_within_county = True
                break

        if not is_within_county:
            print(f"Point ({latitude}, {longitude}) does not fall within any county.")

# Create a FeatureCollection from the matching features
feature_collection = geojson.FeatureCollection(matching_features)

# Write the FeatureCollection to a new GeoJSON file
with open('output.geojson', 'w') as outfile:
    geojson.dump(feature_collection, outfile)

print("GeoJSON file with matching features has been created: output.geojson")