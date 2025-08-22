// Global variables for current selections
let currentDisease = 'flu';
let currentMonth = '';

// Leaflet Marker Icons
const redIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const greenIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const blueIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Function to generate random points around a center
function generateRandomPoints(centerLat, centerLng, count, radius = 0.01) {
  const points = [];
  for (let i = 0; i < count; i++) {
    // Generate random offset within radius
    const latOffset = (Math.random() - 0.5) * radius;
    const lngOffset = (Math.random() - 0.5) * radius;
    
    // Generate random intensity between 0.2 and 1.0
    const intensity = 0.2 + Math.random() * 0.8;
    
    points.push({
      lat: centerLat + latOffset,
      lng: centerLng + lngOffset,
      intensity: intensity
    });
  }
  return points;
}

// Generate sample data for each disease and month combination
const sampleData = {
  // FLU - All 12 months
  'flu-January': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 0.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.4),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'flu-February': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'flu-March': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'flu-April': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2),
  ],
  'flu-May': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 0.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.4),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'flu-June': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'flu-July': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'flu-August': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.5),
  ],
  'flu-September': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.2),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.2),
  ],
  'flu-October': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3.2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.8),
  ],
  'flu-November': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.9),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.5),
  ],
  'flu-December': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.4),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.9),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.8),
  ],

  // COLD - All 12 months
  'cold-January': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'cold-February': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'cold-March': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'cold-April': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2),
  ],
  'cold-May': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'cold-June': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'cold-July': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'cold-August': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.2),
  ],
  'cold-September': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5.1),
  ],
  'cold-October': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 4.2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.6),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5.5),
  ],
  'cold-November': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.8),
  ],
  'cold-December': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.9),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.0),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.1),
  ],

  // RESPIRATORY - All 12 months
  'respiratory-January': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2),
  ],
  'respiratory-February': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 0.9),
  ],
  'respiratory-March': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.6),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'respiratory-April': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2),
  ],
  'respiratory-May': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2),
  ],
  'respiratory-June': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 0.9),
  ],
  'respiratory-July': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.6),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'respiratory-August': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.7),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2.8),
  ],
  'respiratory-September': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.6),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.9),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.2),
  ],
  'respiratory-October': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3.1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.8),
  ],
  'respiratory-November': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.7),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.5),
  ],
  'respiratory-December': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.9),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2.9),
  ],

  // GASTROINTESTINAL - All 12 months
  'gastrointestinal-January': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 0.4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'gastrointestinal-February': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.7),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'gastrointestinal-March': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'gastrointestinal-April': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 0.4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'gastrointestinal-May': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 0.4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'gastrointestinal-June': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.7),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'gastrointestinal-July': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'gastrointestinal-August': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.9),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.6),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.8),
  ],
  'gastrointestinal-September': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.2),
  ],
  'gastrointestinal-October': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.6),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.9),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.5),
  ],
  'gastrointestinal-November': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.9),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.4),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.7),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.1),
  ],
  'gastrointestinal-December': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.0),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.6),
  ],
};

// Function to fetch facilities from backend
async function fetchFacilities() {
  try {
    const response = await fetch('/facilities/api/facilities/');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const facilities = await response.json();
    console.log('Fetched facilities:', facilities);
    return facilities;
  } catch (error) {
    console.error('Error fetching facilities:', error);
    return [];
  }
}

// Plot facility markers
async function plotFacilityMarkers() {
  const facilities = await fetchFacilities();
  
  facilities.forEach((facility) => {
    let popupContent = `<strong>${facility.name}</strong><br>`;
    
    if (facility.assigned_bhw) {
      popupContent += `<strong>BHW:</strong> ${facility.assigned_bhw}<br>`;
    } else {
      popupContent += "No BHWS available<br>";
    }

    // Determine icon color based on facility type
    let icon = redIcon;
    if (facility.name.includes("MHO")) {
      icon = greenIcon;
    } else if (facility.name.includes("BHC")) {
      icon = blueIcon;
    }

    L.marker([facility.latitude, facility.longitude], { icon })
      .addTo(map)
      .bindPopup(popupContent);
  });
}

// Initialize the map
const map = L.map('map').setView([7.587429855100546, 125.82881651697123], 12);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Initialize heat layer with enhanced visibility
let heat = L.heatLayer([], {
  radius: 35,
  blur: 20,
  maxZoom: 10,
  max: 1.0,
  gradient: {
    0.2: 'blue',
    0.4: 'cyan',
    0.6: 'lime',
    0.8: 'yellow',
    1.0: 'red'
  }
}).addTo(map);

// Add legend with enhanced colors
const legend = L.control({ position: 'bottomright' });
legend.onAdd = function(map) {
  const div = L.DomUtil.create('div', 'legend');
  div.innerHTML = `
    <h4>Case Intensity</h4>
    <div><span class="heat-intensity" style="background: blue"></span>Very Low</div>
    <div><span class="heat-intensity" style="background: cyan"></span>Low</div>
    <div><span class="heat-intensity" style="background: lime"></span>Medium</div>
    <div><span class="heat-intensity" style="background: yellow"></span>High</div>
    <div><span class="heat-intensity" style="background: red"></span>Very High</div>
  `;
  return div;
};
legend.addTo(map);

// Function to update heat map based on selected disease and month with animation
function updateHeatMap() {
  const key = `${currentDisease}-${currentMonth}`;
  const heatData = sampleData[key] ? sampleData[key].map(point => [point.lat, point.lng, point.intensity]) : [];
  
  // Fade out current heat
  heat.setOptions({ opacity: 0 });
  
  // Update data and fade in
  setTimeout(() => {
    heat.setLatLngs(heatData);
    heat.setOptions({ opacity: 1 });
  }, 300);
}

function getCurrentMonth(){
  const monthContainer = document.getElementById('month-container');
  
  // Debug: Check if container exists
  if (!monthContainer) {
    console.error('Month container not found!');
    return;
  }
  
  console.log('Month container found, generating month badges...');
  
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  const currentDate = new Date();
  
  // Clear existing month badges
  monthContainer.innerHTML = '';
  
  // Generate next 6 months
  for (let i = 0; i <= 6; i++){
    let newDate = new Date(
      currentDate.getFullYear(),
      currentDate.getMonth() + i,
      1
    );
    let monthDate = months[newDate.getMonth()];
    let year = newDate.getFullYear();
    let monthKey = monthDate;

    let monthBadge = document.createElement("span");
    monthBadge.className = "disease-badge month-badge";
    monthBadge.textContent = `${monthDate} ${year}`;
    monthBadge.dataset.month = monthKey;
    
    // Set first month as active by default
    if (i === 0) {
      monthBadge.classList.add('active');
      currentMonth = monthKey;
    }
    
    // Add click event listener
    monthBadge.addEventListener('click', function() {
      // Remove active class from all month badges
      document.querySelectorAll('.month-badge').forEach(badge => {
        badge.classList.remove('active');
        badge.style.transform = 'scale(1)';
      });
      
      // Add active class to clicked badge
      this.classList.add('active');
      this.style.transform = 'scale(1.05)';
      
      // Update current month and refresh map
      currentMonth = this.dataset.month;
      console.log('Month selected:', currentMonth);
      updateHeatMap();
    });
    
    monthContainer.appendChild(monthBadge);
    console.log('Added month badge:', monthBadge.textContent);
  }
}



// Call plotFacilityMarkers after map initialization
plotFacilityMarkers();

// Initialize with current month data (will be set by getCurrentMonth)
// updateHeatMap() will be called after getCurrentMonth() in DOMContentLoaded

// Add click handlers for disease filters with enhanced feedback
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM Content Loaded - Initializing heatmap...');
  
  // Initialize month badges
  getCurrentMonth();
  
  // Initialize heat map with current selections
  updateHeatMap();
  
  // Disease filter handlers
  document.querySelectorAll('.disease-badge[data-disease]').forEach(badge => {
    badge.addEventListener('click', function() {
      // Toggle active state for disease badges only
      document.querySelectorAll('.disease-badge[data-disease]').forEach(b => {
        b.classList.remove('active');
        b.style.transform = 'scale(1)';
      });
      this.classList.add('active');
      this.style.transform = 'scale(1.05)';
      
      // Update current disease and refresh map
      currentDisease = this.dataset.disease;
      updateHeatMap();
    });
  }); 
}); 