// Show the loader overlay
function showLoader() {
    document.getElementById('loader_overlay').style.display = 'flex';
}

// Hide the loader overlay
function hideLoader() {
    document.getElementById('loader_overlay').style.display = 'none';
}

function fadeIn(element) {
    element.style.opacity = 0;
    element.style.display = 'flex';
    var opacity = 0;
  
    var animationInterval = setInterval(function() {
      opacity += 0.1;
      element.style.opacity = opacity;
  
      if (opacity >= 1) {
        clearInterval(animationInterval);
      }
    }, 30);
  }
  
  // Usage
  function showTopLocations() {
    var topLocationsDiv = document.getElementById('top_locations_div');
    fadeIn(topLocationsDiv);
  }

  function hideTopLocations() {
    const topLocationsDiv = document.getElementById('top_locations_div');
    topLocationsDiv.style.opacity = '0';
  
    // Add transition effect
    topLocationsDiv.style.transition = 'opacity 0.5s';
  
    // Delay hiding the element to allow the fade-out effect to be visible
    setTimeout(function() {
      topLocationsDiv.style.display = 'none';
      topLocationsDiv.style.opacity = '1'; // Reset opacity for future use
    }, 500); // Delay for 0.5 seconds (500 milliseconds)
  
    document.getElementById('top_locations_toggle').checked = false;
  }

mapboxgl.accessToken = 'pk.eyJ1IjoiY2hyaXNoYXJyaXMwMiIsImEiOiJjbGl0M3hraTYwMDIwM3N0OHVheXVoN244In0.ZC-Q0v5TpgSTyJdQb5gP8g';

var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/chrisharris02/clit4a96z00c501pw454t1e6n',
    center: [-98.5795, 39.8283], 
    zoom: 2.0, 
});

map.on('load', function () {

    
    //Adding nav control in bottom left
    const nav = new mapboxgl.NavigationControl();
    map.addControl(nav, 'bottom-left');

    const toggleSwitch = document.getElementById('ards_trial_locations_toggle');

    const layerId = 'updated-with-state-icu-normalize';
    map.setLayoutProperty(layerId, 'visibility', 'none');
   
   

    map.addSource('heat', {
        type: 'geojson',
        data: '/generate-data' 
    });
    map.addSource('counties', {
        type: 'geojson',
        data: '/misc/us_counties.json'
      });


      map.addLayer({
        id: 'counties-outline',
        type: 'line',
        source: 'counties',
        paint: {
          'line-color': '#2596be', // Set the outline color
          'line-width': 0.45 // Set the outline width
        }
      });
    const topLocationsToggle = document.getElementById("top_locations_toggle")
    toggleSwitch.addEventListener('change', function() {
        const layer = map.getLayer(layerId);
    
        if (this.checked) {
            // Show the layer
            map.setLayoutProperty(layerId, 'visibility', 'visible');
        } else {
            // Hide the layer
            map.setLayoutProperty(layerId, 'visibility', 'none');
        }
    });
    

    topLocationsToggle.addEventListener('change', function() {
          if (this.checked) {
            // Show the layer
           showTopLocations();
        } else {
            // Hide the layer
           hideTopLocations();
        }
    });

    map.addLayer({
        id: 'heat-layer',
        type: 'fill',
        source: 'heat',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', 'Score'], // Use the 'Score' property for interpolation
            0.0, '#00A3F9', 
            0.1, '#00D09D',  
            0.4, '#E7FF00',  
            0.54, '#FFED00', 
            0.7, '#FF7800',
            1.0, '#FF4E2F'    
          ],
          'fill-opacity': 0.8 // Adjust the fill opacity as needed
        }
      });
    map.moveLayer(layerId);
  //  Add a hover effect and popup
    map.on('mouseenter', layerId, (e) => {
        map.getCanvas().style.cursor = 'pointer';
        const coordinates = e.features[0].geometry.coordinates.slice();
        const hospitalName = e.features[0].properties['Hospital Name'];
        const totalSuccessfulTrials = e.features[0].properties['Total Successful Trials'];
        const icuBeds = e.features[0].properties['ICU Beds true'];
        const normalizedCompositeScores = e.features[0].properties['Normalized Composite Scores'];
        const currentStudy = e.features[0].properties['Current/Most Recent Study'];
        const status = e.features[0].properties['Status'];
        const studyResults = e.features[0].properties['Study Results'];
        const interventions = e.features[0].properties['Interventions'];
        const outcomeMeasures = e.features[0].properties['Outcome Measures'];
        const age = e.features[0].properties['Age'];
        const phases = e.features[0].properties['Phases'];
        const enrollment = e.features[0].properties['Enrollment'];
        const studyType = e.features[0].properties['Study Type'];
        const studyDesigns = e.features[0].properties['Study Designs'];
        const completionDate = e.features[0].properties['Completion Date'];
        const url = e.features[0].properties['URL'];
        const principalInvestigator = e.features[0].properties['Principal Investigator'];
    
        // Create the popup
        popup = new mapboxgl.Popup({
            closeButton: false,
            closeOnClick: false,
            offset: 10,
            anchor: 'top-left',
            offset: [0, -15], // Adjust the offset to control distance from marker
            className: 'popup-style'
        })
            .setLngLat(coordinates)
            .setHTML(`
            <p><strong>${hospitalName}</strong></p>
            <p><strong>Total Successful Trials:</strong> ${totalSuccessfulTrials}</p>
            <p><strong>ICU Beds:</strong> ${icuBeds}</p>
            <p><strong>Normalized Composite Scores:</strong> ${normalizedCompositeScores}</p>
            <p><strong>Current/Most Recent Study:</strong> ${currentStudy}</p>
            <p><strong>Status:</strong> ${status}</p>
            <p><strong>Study Results:</strong> ${studyResults}</p>
            <p><strong>Interventions:</strong> ${interventions}</p>
            <p><strong>Outcome Measures:</strong> ${outcomeMeasures}</p>
            <p><strong>Age:</strong> ${age}</p>
            <p><strong>Phases:</strong> ${phases}</p>
            <p><strong>Enrollment:</strong> ${enrollment}</p>
            <p><strong>Study Type:</strong> ${studyType}</p>
            <p><strong>Study Designs:</strong> ${studyDesigns}</p>
            <p><strong>Completion Date:</strong> ${completionDate}</p>
            <p><strong>URL:</strong> ${url}</p>
            <p><strong>Principal Investigator:</strong> ${principalInvestigator}</p>
        `)
            .addTo(map);
    });

    map.on('mouseleave', layerId, () => {
        map.getCanvas().style.cursor = '';
        popup.remove();
    });
});

document.getElementById('submit').addEventListener('click', function () {
    showLoader();

    var toggles = [];
    var checkboxes = document.querySelectorAll('input[type=checkbox]:checked');
    
    for (var i = 0; i < checkboxes.length; i++) {
        toggles.push(parseInt(checkboxes[i].value));
    }
    
    // Remove values of 8 or 9 if they exist
    toggles = toggles.filter(function(value) {
        return value !== 11 && value !== 12;
    });
    

    fetch('/generate-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(toggles)
    })
    .then(response => response.json())
    .then(data => {
        hideLoader();

        map.getSource('heat').setData(data.main); 
          // Assign county information to each data point
        
        if (data.cluster !== null) {
            // Add the cluster source and layer to the map
            // Use data.cluster as the data for the source
            // Be sure to check if the cluster source and layer already exist before adding them,
            // and if they do, don't add them again
            // map.addSource
        } else {
            // Remove the cluster source and layer from the map if they exist
        }
        // if (toggles.includes(9)) 
        // Add that side panel list
        // else
        // Remove the side panel list if it exists
    });
});
