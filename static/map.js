// Initialize the map with options for smoother (fractional) zoom
let map = L.map('map', {
    zoomSnap: 0,        // Disable snapping to integer zoom levels
    zoomDelta: 0.25,    // Use smaller increments for each zoom event
    wheelPxPerZoomLevel: 5,
    zoomAnimation: true,
    fadeAnimation: true
  }).setView([20, 0], 2);
  
  // Use CartoDB Positron tile layer for English labels
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
  }).addTo(map);
  
  let guessMarker = null;    // Marker for the user's guess
  let correctMarker = null;  // Marker for the actual event location
  let guessLat = null;       // To store the guessed latitude
  let guessLon = null;       // To store the guessed longitude
  
  // Listen for clicks on the map to place/update the guess marker
  map.on('click', function (e) {
    // Remove previous guess marker if one exists
    if (guessMarker) {
      map.removeLayer(guessMarker);
    }
    // Save the clicked coordinates
    guessLat = e.latlng.lat;
    guessLon = e.latlng.lng;
    
    // Place a marker at the clicked location
    guessMarker = L.marker(e.latlng).addTo(map);
    
    // Show the Confirm Guess button once a guess has been placed
    document.getElementById("confirmBtn").style.display = "block";
  });
  
  // Function to confirm the guess and send the data to the Flask backend
  function confirmGuess() {
    // Retrieve the game year from the HTML element
    let gameYear = parseInt(document.getElementById("gameYear").innerText);
    
    // Send the guess via a POST request to the /submit_guess route
    fetch('/submit_guess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lat: guessLat,
        lon: guessLon,
        year: gameYear
      })
    })
    .then(response => response.json())
    .then(data => {
      // Display the result from the backend
      document.getElementById("result").innerHTML = `
        <h2>Result</h2>
        <p><strong>Event:</strong> ${data.event}</p>
        <p><strong>Hint:</strong> ${data.hint}</p>
        <p><strong>Distance:</strong> ${data.distance} km</p>
        <p><strong>Actual Location:</strong> ${data.actual_location.lat}, ${data.actual_location.lon}</p>
      `;
      
      // Remove any previous correct marker if it exists
      if (correctMarker) {
        map.removeLayer(correctMarker);
      }
      
      // Create a custom image icon for the correct guess marker
      const correctIcon = L.icon({
        iconUrl: '/static/images/correct-marker.png',      // Ensure this file exists in your static/images/ folder
        iconSize: [40, 40],      // Adjust these values as needed for your design
        iconAnchor: [20, 40],    // Anchor the bottom center of the icon at the marker's coordinate
        popupAnchor: [0, -40]
      });
      
      // Create a new marker using the custom icon at the actual event location
      correctMarker = L.marker([data.actual_location.lat, data.actual_location.lon], {
        icon: correctIcon
      }).addTo(map);
      
      // Trigger effects based on the accuracy of the guess
      if (data.distance < 50) { // Threshold for a close guess
        triggerConfetti();
      } else if (data.distance > 500) { // Threshold for a really bad guess
        triggerBadGuessEffect();
      }
      
      // Optionally, disable further map clicks after confirming the guess
      map.off('click');
      
      // Hide the confirm button now that the guess is confirmed
      document.getElementById("confirmBtn").style.display = "none";
      
      // Show the slider container so the user can select a different year to play
      document.getElementById("slider-container").style.display = "block";
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }
  
  // --- New functions for the slider and manual year input ---
  
  // Sync the number input when the slider value changes
  function syncYearInput(val) {
    document.getElementById("yearInput").value = val;
  }
  
  // Sync the slider when the number input changes
  function syncYearSlider(val) {
    document.getElementById("yearSlider").value = val;
  }
  
  // Redirect to play the game with the selected year
  function playSelectedYear() {
    const selectedYear = document.getElementById("yearSlider").value;
    window.location.href = `/play?year=${selectedYear}`;
  }
  
  // Trigger confetti effect using the canvas-confetti library
  function triggerConfetti() {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
  }
  
  // Trigger a bad guess effect by shaking the map container
  function triggerBadGuessEffect() {
    let mapContainer = document.getElementById("map");
    mapContainer.classList.add("shake");
    setTimeout(() => {
      mapContainer.classList.remove("shake");
    }, 500);
  }
  