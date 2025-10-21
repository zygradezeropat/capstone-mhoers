// Global variables for current selections
let currentDisease = 'flu';
let currentMonth = '';
// Cache of facilities and markers for quick lookup and filtering
let facilityCache = [];
let facilityIdToMarker = new Map();
let selectedFacilityId = null;

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

// Function: fetchFacilities
// Purpose: Retrieve facilities from the backend API for plotting and filtering
// Returns: Array of facility objects with id, name, assigned_bhw, latitude, longitude, user_id
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

// Function: updateFacilityInfoPanel
// Purpose: Show selected facility details in the right-side info card
// Inputs: facility object
function updateFacilityInfoPanel(facility) {
  const infoEl = document.getElementById('facility-info');
  if (!infoEl) return;
  if (!facility) {
    infoEl.innerHTML = 'Select a facility to view details.';
    return;
  }
  infoEl.innerHTML = `
    <div class="mb-2"><span class="text-uppercase text-muted">Facility</span><br><strong>${facility.name}</strong></div>
    <div class="mb-2"><span class="text-uppercase text-muted">Assigned BHW</span><br><strong>${facility.assigned_bhw || 'N/A'}</strong></div>
    <div class="mb-2"><span class="text-uppercase text-muted">User ID</span><br><code>${facility.user_id ?? ''}</code></div>
    <div class="text-muted">Lat: ${facility.latitude.toFixed(6)} | Lng: ${facility.longitude.toFixed(6)}</div>
  `;
}

// Function: selectFacilityById
// Purpose: Focus map and open popup for a facility, and update info panel
// Inputs: facilityId (number)
function selectFacilityById(facilityId) {
  console.log('Selecting facility with ID:', facilityId);
  console.log('Available facilities:', facilityCache);
  console.log('Available markers:', Array.from(facilityIdToMarker.keys()));
  
  const facility = facilityCache.find(f => String(f.facility_id) === String(facilityId));
  const marker = facilityIdToMarker.get(String(facilityId));
  
  console.log('Found facility:', facility);
  console.log('Found marker:', marker);
  
  if (!facility) {
    console.error('Facility not found in cache for ID:', facilityId);
    return;
  }
  
  if (!marker) {
    console.error('Marker not found for facility ID:', facilityId);
    return;
  }
  
  selectedFacilityId = String(facilityId);
  // Smoothly fly to the facility and open the popup after the movement to keep it centered
  const targetLatLng = [facility.latitude, facility.longitude];
  const targetZoom = Math.max(map.getZoom(), 15);
  
  console.log('Flying to:', targetLatLng, 'with zoom:', targetZoom);
  
  let opened = false;
  const openIfNeeded = () => {
    if (opened) return;
    opened = true;
    marker.openPopup();
    console.log('Popup opened for facility:', facility.name);
  };
  map.once('moveend', openIfNeeded);
  map.flyTo(targetLatLng, targetZoom, { animate: true, duration: 0.8 });
  updateFacilityInfoPanel(facility);
  // Highlight selected badge in list
  document.querySelectorAll('#facility-list .badge').forEach(b => b.classList.remove('active'));
  const active = document.querySelector(`#facility-list .badge[data-id="${String(facilityId)}"]`);
  if (active) active.classList.add('active');
}

// Function: populateFacilityDropdown
// Purpose: Fill the facility <select> with options and wire change event to focus map
function populateFacilityDropdown() {
  const select = document.getElementById('facility-select');
  if (!select) return;
  
  console.log('Populating dropdown with facilities:', facilityCache);
  
  // Reset options keeping the first placeholder
  select.innerHTML = '<option value="">-- Choose a facility --</option>';
  facilityCache.forEach(f => {
    console.log('Adding facility to dropdown:', f);
    const opt = document.createElement('option');
    opt.value = String(f.facility_id);
    opt.textContent = f.name;
    select.appendChild(opt);
  });
  
  select.addEventListener('change', (e) => {
    const id = e.target.value;
    console.log('Facility selected from dropdown:', id);
    if (id) selectFacilityById(id);
  });
}

// Function: plotFacilityMarkers
// Purpose: Fetch facilities then place markers on the map and wire events
async function plotFacilityMarkers() {
  facilityCache = await fetchFacilities();
  // Populate dropdown
  populateFacilityDropdown();
  
  facilityCache.forEach((facility) => {
    let popupContent = `<strong>${facility.name}</strong><br>`;
    if (facility.assigned_bhw) {
      popupContent += `<strong>BHW:</strong> ${facility.assigned_bhw}<br>`;
    } else {
      popupContent += 'No BHWS available<br>';
    }

    // Determine icon color based on facility type
    let icon = redIcon;
    if (facility.name.includes('MHO')) {
      icon = greenIcon;
    } else if (facility.name.includes('BHC')) {
      icon = blueIcon;
    }

    const marker = L.marker([facility.latitude, facility.longitude], { icon })
      .addTo(map)
      .bindPopup(popupContent);

    // Store marker by facility id for later focusing
    facilityIdToMarker.set(String(facility.facility_id), marker);

    // When a marker is clicked, update the info panel and remember selection
    marker.on('click', () => {
      selectedFacilityId = String(facility.facility_id);
      // Center the map on the marker for consistent positioning
      const latLng = marker.getLatLng();
      const zoom = Math.max(map.getZoom(), 15);
      map.flyTo(latLng, zoom, { animate: true, duration: 0.6 });
      // Open popup after fly to keep it centered
      map.once('moveend', () => marker.openPopup());
      updateFacilityInfoPanel(facility);
    });
  });
}

// Initialize the map
const DEFAULT_CENTER = [7.587429855100546, 125.82881651697123];
const DEFAULT_ZOOM = 12;
const map = L.map('map').setView(DEFAULT_CENTER, DEFAULT_ZOOM);

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
  
  // Initialize month badges (kept for future use of heatmap)
  getCurrentMonth();
  // Initialize heat map with current selections (no longer tied to UI)
  updateHeatMap();
  
  // Initialize facility markers, list, and info panel
  plotFacilityMarkers().then(() => {
    // Optionally auto-select first facility for a better UX
    if (facilityCache.length > 0) {
      updateFacilityInfoPanel(null); // keep empty until user clicks
    }
  });

  // Wire reset button to return to default view and clear selection
  const resetBtn = document.getElementById('facility-reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      const select = document.getElementById('facility-select');
      if (select) select.value = '';
      selectedFacilityId = null;
      // Close any open popup
      map.closePopup();
      // Reset info panel
      updateFacilityInfoPanel(null);
      // Fly back to default
      map.flyTo(DEFAULT_CENTER, DEFAULT_ZOOM, { animate: true, duration: 0.8 });
    });
  }
  
  // Disease filter badges removed in favor of facility dropdown
}); 