// Global variables for current selections
let currentDisease = 'open_wounds';
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
  // OPEN WOUNDS (T14.1) - All 12 months
  'open_wounds-January': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'open_wounds-February': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'open_wounds-March': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'open_wounds-April': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2),
  ],
  'open_wounds-May': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'open_wounds-June': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'open_wounds-July': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'open_wounds-August': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.2),
  ],
  'open_wounds-September': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5.1),
  ],
  'open_wounds-October': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 4.2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.6),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5.5),
  ],
  'open_wounds-November': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.8),
  ],
  'open_wounds-December': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.9),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.0),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.1),
  ],

  // DOG BITES (W54.99) - All 12 months
  'dog_bites-January': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2),
  ],
  'dog_bites-February': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 0.9),
  ],
  'dog_bites-March': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.6),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'dog_bites-April': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2),
  ],
  'dog_bites-May': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2),
  ],
  'dog_bites-June': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 0.9),
  ],
  'dog_bites-July': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.6),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'dog_bites-August': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.7),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2.8),
  ],
  'dog_bites-September': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.6),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.9),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.2),
  ],
  'dog_bites-October': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3.1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.8),
  ],
  'dog_bites-November': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.7),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.5),
  ],
  'dog_bites-December': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.9),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 2.9),
  ],

  // ACUTE RESPIRATORY INFECTIONS (J06.9) - All 12 months
  'acute_respiratory-January': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 0.4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'acute_respiratory-February': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.7),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'acute_respiratory-March': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'acute_respiratory-April': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 0.4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'acute_respiratory-May': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 0.4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 5),
  ],
  'acute_respiratory-June': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.7),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4),
  ],
  'acute_respiratory-July': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3),
  ],
  'acute_respiratory-August': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 0.9),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.6),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.8),
  ],
  'acute_respiratory-September': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.3),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.2),
  ],
  'acute_respiratory-October': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.6),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.9),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.5),
  ],
  'acute_respiratory-November': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.9),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.4),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.7),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.1),
  ],
  'acute_respiratory-December': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.0),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.6),
  ],

  // PNEUMONIA (J15) - All 12 months
  'pneumonia-January': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.2),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.2),
  ],
  'pneumonia-February': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3.2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.1),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.5),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.8),
  ],
  'pneumonia-March': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.9),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.3),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.5),
  ],
  'pneumonia-April': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.4),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.9),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.8),
  ],
  'pneumonia-May': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 1.5),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 0.8),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.5),
  ],
  'pneumonia-June': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.2),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.6),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.0),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.0),
  ],
  'pneumonia-July': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.8),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.0),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.4),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.6),
  ],
  'pneumonia-August': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 3.0),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 2.2),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.6),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.8),
  ],
  'pneumonia-September': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.6),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.8),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.2),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.4),
  ],
  'pneumonia-October': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.4),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.7),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.2),
  ],
  'pneumonia-November': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.0),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.5),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.0),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 3.9),
  ],
  'pneumonia-December': [
    ...generateRandomPoints(7.552622064739173, 125.84503485413579, 2.3),
    ...generateRandomPoints(7.588579595450028, 125.84428777875284, 1.7),
    ...generateRandomPoints(7.591473025041597, 125.80166888687106, 1.1),
    ...generateRandomPoints(7.521442817020294, 125.79194746388369, 4.1),
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
  const facility = facilityCache.find(f => String(f.facility_id) === String(facilityId));
  const marker = facilityIdToMarker.get(String(facilityId));
  if (!facility || !marker) return;
  selectedFacilityId = String(facilityId);
  // Smoothly fly to the facility and open the popup after the movement to keep it centered
  const targetLatLng = [facility.latitude, facility.longitude];
  const targetZoom = Math.max(map.getZoom(), 15);
  let opened = false;
  const openIfNeeded = () => {
    if (opened) return;
    opened = true;
    marker.openPopup();
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
  // Reset options keeping the first placeholder
  select.innerHTML = '<option value="">-- Choose a facility --</option>';
  facilityCache.forEach(f => {
    const opt = document.createElement('option');
    opt.value = String(f.facility_id);
    opt.textContent = f.name;
    select.appendChild(opt);
  });
  select.addEventListener('change', (e) => {
    const id = e.target.value;
    if (id) selectFacilityById(id);
  });
}

// Function: plotFacilityMarkers
// Purpose: Fetch facilities then place markers on the map and wire events
async function plotFacilityMarkers() {
  if (!map) {
    console.error('Map not initialized yet. Call initializeMap() first.');
    return;
  }
  
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

// Initialize the map - will be set up when DOM is ready
const DEFAULT_CENTER = [7.587429855100546, 125.82881651697123];
const DEFAULT_ZOOM = 12;
let map = null;
let heat = null;

// Initialize map when DOM is ready
function initializeMap() {
  if (map) return; // Already initialized
  
  const mapElement = document.getElementById('map');
  if (!mapElement) {
    console.error('Map element not found!');
    return;
  }
  
  map = L.map('map').setView(DEFAULT_CENTER, DEFAULT_ZOOM);

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  // Initialize heat layer with enhanced visibility
  heat = L.heatLayer([], {
    radius: 40,
    blur: 25,
    maxZoom: 10,
    max: 1.0,
    gradient: {
      0.0: 'transparent',
      0.2: 'blue',
      0.4: 'cyan',
      0.6: 'lime',
      0.8: 'yellow',
      1.0: 'red'
    }
  }).addTo(map);
  
  console.log('Map initialized successfully');
}



// Disease code to filter key mapping (matches data-disease attributes in HTML)
const diseaseCodeToFilter = {
  'T14.1': 'open_wounds',  // Open Wounds (T14.1)
  'W54.99': 'dog_bites',  // Dog Bites (W54.99)
  'J06.9': 'acute_respiratory',  // Acute respiratory infections (J06.9)
  'J15': 'pneumonia',  // Pneumonia (J15)
  'I10-1': 'hypertension_level_2',  // Hypertension Level 2 (I10-1)
  'I10.1': 'hypertension_level_2'  // Hypertension Level 2 (I10.1) - normalized
};

// Function to normalize disease codes (convert dots to hyphens for consistency)
function normalizeDiseaseCode(diseaseCode) {
  if (!diseaseCode) return diseaseCode;
  // Normalize I10.0 -> I10-0, I10.1 -> I10-1, etc.
  return diseaseCode.replace(/I10\.0/g, 'I10-0').replace(/I10\.1/g, 'I10-1');
}

// Cache for predictions
let predictionsCache = {};
// Cache for storing count information for display
let countInfoCache = {};
// Cache for raw predictions data (for table display)
let rawPredictionsCache = {};

// Function to fetch disease peak predictions from API
async function fetchDiseasePeakPredictions(month = null) {
  try {
    const url = `/analytics/api/disease-peak-predictions/?samples_per_month=100${month ? `&month=${month}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching disease peak predictions:', error);
    return null;
  }
}

// Function to convert disease predictions to heatmap data
function convertPredictionsToHeatData(predictions, facilities) {
  const heatData = {};
  
  if (!predictions || predictions.error) {
    return heatData;
  }
  
  // Collect all counts from all diseases across all months for normalization
  const allCounts = [];
  for (const [month, prediction] of Object.entries(predictions)) {
    if (prediction && typeof prediction === 'object') {
      // Check if we have all_diseases (new format) or just disease/count (old format)
      if (prediction.all_diseases && Object.keys(prediction.all_diseases).length > 0) {
        // New format: collect counts from all diseases
        Object.values(prediction.all_diseases).forEach(count => {
          allCounts.push(count);
        });
      } else if (prediction.count !== undefined) {
        // Old format: just the peak disease count
        allCounts.push(prediction.count);
      }
    }
  }
  
  const minCount = allCounts.length > 0 ? Math.min(...allCounts) : 0;
  const maxCount = allCounts.length > 0 ? Math.max(...allCounts) : 1;
  const countRange = maxCount - minCount || 1; // Avoid division by zero
  
  // Store count info for display
  const countInfo = {};
  
  // For each month-disease combination, generate heat points based on facilities
  for (const [month, prediction] of Object.entries(predictions)) {
    if (!prediction || typeof prediction !== 'object') {
      continue;
    }
    
    // Process all diseases if available, otherwise just the peak disease
    const diseasesToProcess = [];
    
    if (prediction.all_diseases && Object.keys(prediction.all_diseases).length > 0) {
      // New format: process all diseases
      Object.entries(prediction.all_diseases).forEach(([diseaseCode, count]) => {
        diseasesToProcess.push({ diseaseCode, count });
      });
    } else if (prediction.disease && prediction.count !== undefined) {
      // Old format: only peak disease (for backward compatibility)
      diseasesToProcess.push({ 
        diseaseCode: prediction.disease, 
        count: prediction.count 
      });
    }
    
    // Process each disease for this month
    diseasesToProcess.forEach(({ diseaseCode, count }) => {
      // Normalize disease code first (I10.1 -> I10-1, I10.0 -> I10-0)
      const normalizedCode = normalizeDiseaseCode(diseaseCode);
      // Map disease code to filter key
      const filterKey = diseaseCodeToFilter[normalizedCode] || diseaseCodeToFilter[diseaseCode] || normalizedCode.toLowerCase().replace(/[^a-z0-9]/g, '');
      
      // Debug logging
      console.log(`Processing disease: ${diseaseCode} (normalized: ${normalizedCode}) -> filterKey: ${filterKey}`);
      
      // Generate heat points for facilities
      const key = `${filterKey}-${month}`;
      heatData[key] = [];
      
      // Store count info for this key
      countInfo[key] = {
        count: count,
        disease: diseaseCode,
        month: month
      };
      
      if (facilities && facilities.length > 0) {
        // Normalize count to 0-1 range for intensity
        const normalizedIntensity = countRange > 0 
          ? (count - minCount) / countRange 
          : 0.5; // Default to medium if all counts are same
        
        // Ensure minimum visibility (0.2) and maximum (1.0)
        const baseIntensity = Math.max(0.2, Math.min(1.0, normalizedIntensity));
        
        // Create multiple heat points per facility based on count
        // More points = stronger heat visualization
        const pointsPerFacility = Math.max(1, Math.ceil(count / 10)); // 1 point per 10 predicted cases
        
        facilities.forEach(facility => {
          if (facility.latitude && facility.longitude) {
            // Create multiple points with slight variation in position for better heat distribution
            for (let i = 0; i < pointsPerFacility; i++) {
              // Small random offset (0.001 degrees ≈ 100m) for visual spread
              const latOffset = (Math.random() - 0.5) * 0.002;
              const lngOffset = (Math.random() - 0.5) * 0.002;
              
              heatData[key].push({
                lat: parseFloat(facility.latitude) + latOffset,
                lng: parseFloat(facility.longitude) + lngOffset,
                intensity: baseIntensity,
                count: count // Store count for tooltip/display
              });
            }
          }
        });
      }
    });
  }
  
  // Store count info in cache
  if (!countInfoCache[currentMonth]) {
    countInfoCache[currentMonth] = {};
  }
  Object.assign(countInfoCache[currentMonth], countInfo);
  
  return heatData;
}

// Function to fetch all predictions for all available months
async function fetchAllPredictions() {
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  
  const allPredictions = {};
  
  // First, try to fetch all months at once (more efficient)
  try {
    console.log('Fetching all months at once...');
    const allPredictionsResponse = await fetchDiseasePeakPredictions(null);
    console.log('Bulk fetch response:', allPredictionsResponse);
    
    if (allPredictionsResponse && !allPredictionsResponse.error) {
      // If we got all months at once, use that
      let monthsFound = 0;
      months.forEach(month => {
        if (allPredictionsResponse[month]) {
          allPredictions[month] = allPredictionsResponse[month];
          rawPredictionsCache[month] = allPredictionsResponse[month];
          monthsFound++;
          console.log(`Found ${month} in bulk response`);
        }
      });
      console.log(`Found ${monthsFound} months in bulk response out of ${months.length} expected`);
      
      // If we got all months, we're done
      if (monthsFound === months.length) {
        console.log('All months fetched successfully in bulk');
      } else {
        console.log(`Missing ${months.length - monthsFound} months, will fetch individually`);
      }
    } else if (allPredictionsResponse && allPredictionsResponse.error) {
      console.error('Bulk fetch returned error:', allPredictionsResponse.error);
    }
  } catch (error) {
    console.log('Could not fetch all months at once, fetching individually...', error);
  }
  
  // If we didn't get all months, fetch them individually
  for (const month of months) {
    if (allPredictions[month]) {
      console.log(`Skipping ${month} - already have data`);
      continue; // Skip if we already have this month
    }
    
    try {
      console.log(`Fetching individual prediction for ${month}...`);
      const predictions = await fetchDiseasePeakPredictions(month);
      console.log(`Response for ${month}:`, predictions);
      
      if (predictions && !predictions.error) {
        // The API returns { "January": { "disease": "...", "count": ... } } when month is specified
        // or { "January": {...}, "February": {...} } when month is null
        // Extract the actual prediction data
        let monthData = null;
        
        if (predictions[month]) {
          // If month key exists, use that
          monthData = predictions[month];
          console.log(`Extracted ${month} data from month key`);
        } else if (predictions.disease || predictions.all_diseases) {
          // If it's already the data object, use it directly
          monthData = predictions;
          console.log(`Using ${month} data directly from response`);
        } else {
          // Try to get the first value if it's an object
          const keys = Object.keys(predictions);
          if (keys.length > 0 && predictions[keys[0]]) {
            monthData = predictions[keys[0]];
            console.log(`Extracted ${month} data from first key: ${keys[0]}`);
          }
        }
        
        if (monthData) {
          allPredictions[month] = monthData;
          rawPredictionsCache[month] = monthData;
          console.log(`✓ Successfully fetched prediction for ${month}:`, monthData);
        } else {
          console.warn(`⚠ No data extracted for ${month}. Response structure:`, predictions);
        }
      } else if (predictions && predictions.error) {
        console.error(`✗ API error for ${month}:`, predictions.error);
      } else {
        console.warn(`⚠ No valid response for ${month}`);
      }
    } catch (error) {
      console.error(`✗ Error fetching predictions for ${month}:`, error);
    }
  }
  
  // Log summary of predictions
  console.log('=== All predictions summary ===');
  console.log('Months with data:', Object.keys(allPredictions));
  console.log('Full predictions object:', allPredictions);
  
  const diseaseCounts = {};
  Object.values(allPredictions).forEach(pred => {
    if (pred && pred.disease) {
      diseaseCounts[pred.disease] = (diseaseCounts[pred.disease] || 0) + 1;
    }
  });
  console.log('Disease distribution across months:', diseaseCounts);
  
  // Update table with all predictions
  updatePredictionTable(allPredictions);
  
  // Update raw data table (if it still exists)
  if (typeof updateRawDataTable === 'function') {
    updateRawDataTable(allPredictions);
  }
  
  return allPredictions;
}

// Function to update raw API data table
function updateRawDataTable(allPredictions) {
  const tableContainer = document.getElementById('raw-data-table-container');
  const table = document.getElementById('raw-data-table');
  
  if (!tableContainer || !table) {
    console.error('Raw data table elements not found');
    return;
  }
  
  // Get all months sorted
  const months = Object.keys(allPredictions).sort((a, b) => {
    const monthOrder = ["January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"];
    return monthOrder.indexOf(a) - monthOrder.indexOf(b);
  });
  
  if (months.length === 0) {
    tableContainer.style.display = 'none';
    return;
  }
  
  // Build disease display name mapping
  const diseaseDisplayNames = {
    'T14.1': 'Open Wounds (T14.1)',
    'W54.99': 'Dog Bites (W54.99)',
    'J06.9': 'Acute Respiratory Infections (J06.9)',
    'J15': 'Bacterial pneumonia (J15)',
    'I10-1': 'Hypertension Level 2 (I10-1)',
    'I10.1': 'Hypertension Level 2 (I10-1)'  // Normalized
  };
  
  // Build table body
  const tbody = table.querySelector('tbody');
  tbody.innerHTML = '';
  
  months.forEach(month => {
    const monthData = allPredictions[month];
    
    if (monthData && typeof monthData === 'object' && !Array.isArray(monthData)) {
      // If we have all_diseases, create a row for each disease
      if (monthData.all_diseases && Object.keys(monthData.all_diseases).length > 0) {
        // Sort diseases by count (descending)
        const sortedDiseases = Object.entries(monthData.all_diseases)
          .sort((a, b) => b[1] - a[1]);
        
        // Filter out ZOO disease and normalize disease codes before processing
        const filteredDiseases = sortedDiseases
          .filter(([diseaseCode]) => {
            return diseaseCode !== 'ZOO' && diseaseCode !== 'zoo';
          })
          .map(([diseaseCode, count]) => {
            // Normalize disease code (I10.1 -> I10-1, I10.0 -> I10-0)
            return [normalizeDiseaseCode(diseaseCode), count];
          })
          // Group by normalized code and sum counts if duplicates exist
          .reduce((acc, [code, count]) => {
            const existing = acc.find(([c]) => c === code);
            if (existing) {
              existing[1] += count;
            } else {
              acc.push([code, count]);
            }
            return acc;
          }, [])
          .sort((a, b) => b[1] - a[1]); // Re-sort by count after normalization
        
        filteredDiseases.forEach(([diseaseCode, count], index) => {
          const row = document.createElement('tr');
          
          // Month cell (only show for first disease of the month)
          if (index === 0) {
            const monthCell = document.createElement('td');
            monthCell.textContent = month;
            monthCell.style.fontWeight = '600';
            monthCell.rowSpan = filteredDiseases.length;
            monthCell.style.verticalAlign = 'middle';
            row.appendChild(monthCell);
          }
          
          // Disease Code cell
          const diseaseCell = document.createElement('td');
          diseaseCell.innerHTML = `${diseaseCode}<br><small class="text-muted">${diseaseDisplayNames[diseaseCode] || ''}</small>`;
          row.appendChild(diseaseCell);
          
          // Predicted Count cell
          const countCell = document.createElement('td');
          countCell.textContent = count;
          countCell.style.textAlign = 'center';
          countCell.style.fontWeight = '600';
          
          // Color code based on count
          if (count < 20) {
            countCell.style.color = '#0c5460';
            countCell.style.backgroundColor = '#d1ecf1';
          } else if (count < 40) {
            countCell.style.color = '#856404';
            countCell.style.backgroundColor = '#fff3cd';
          } else {
            countCell.style.color = '#721c24';
            countCell.style.backgroundColor = '#f8d7da';
          }
          row.appendChild(countCell);
          
          // Total Samples cell (only show for first disease)
          if (index === 0) {
            const samplesCell = document.createElement('td');
            const totalSamples = monthData.total_samples !== undefined ? monthData.total_samples : 'N/A';
            samplesCell.textContent = totalSamples;
            samplesCell.style.textAlign = 'center';
            samplesCell.rowSpan = filteredDiseases.length;
            samplesCell.style.verticalAlign = 'middle';
            row.appendChild(samplesCell);
          }
          
          tbody.appendChild(row);
        });
      } else {
        // Fallback to old format (only peak disease)
        const row = document.createElement('tr');
        
        // Month cell
        const monthCell = document.createElement('td');
        monthCell.textContent = month;
        monthCell.style.fontWeight = '600';
        row.appendChild(monthCell);
        
        // Disease Code cell
        const diseaseCell = document.createElement('td');
        const diseaseCode = monthData.disease || 'N/A';
        diseaseCell.innerHTML = `${diseaseCode}<br><small class="text-muted">${diseaseDisplayNames[diseaseCode] || ''}</small>`;
        row.appendChild(diseaseCell);
        
        // Predicted Count cell
        const countCell = document.createElement('td');
        const count = monthData.count !== undefined ? monthData.count : 'N/A';
        countCell.textContent = count;
        countCell.style.textAlign = 'center';
        countCell.style.fontWeight = '600';
        
        // Color code based on count
        if (count !== 'N/A') {
          if (count < 20) {
            countCell.style.color = '#0c5460';
            countCell.style.backgroundColor = '#d1ecf1';
          } else if (count < 40) {
            countCell.style.color = '#856404';
            countCell.style.backgroundColor = '#fff3cd';
          } else {
            countCell.style.color = '#721c24';
            countCell.style.backgroundColor = '#f8d7da';
          }
        }
        row.appendChild(countCell);
        
        // Total Samples cell
        const samplesCell = document.createElement('td');
        const totalSamples = monthData.total_samples !== undefined ? monthData.total_samples : 'N/A';
        samplesCell.textContent = totalSamples;
        samplesCell.style.textAlign = 'center';
        row.appendChild(samplesCell);
        
        tbody.appendChild(row);
      }
    }
  });
  
  // Show table container
  tableContainer.style.display = 'block';
}

// Function to update prediction summary table
function updatePredictionTable(allPredictions) {
  const tableContainer = document.getElementById('prediction-table-container');
  const table = document.getElementById('prediction-summary-table');
  
  if (!tableContainer || !table) {
    console.error('Table elements not found');
    return;
  }
  
  // Always show all 12 months, even if some don't have data
  const allMonths = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];
  
  // Get months that have predictions (for data processing)
  const monthsWithData = Object.keys(allPredictions).sort((a, b) => {
    return allMonths.indexOf(a) - allMonths.indexOf(b);
  });
  
  // Use all 12 months for table display
  const months = allMonths;
  
  if (monthsWithData.length === 0 && Object.keys(allPredictions).length === 0) {
    tableContainer.style.display = 'none';
    return;
  }
  
  // Build disease to display name mapping
  const diseaseDisplayNames = {
    'T14.1': 'Open Wounds (T14.1)',
    'W54.99': 'Dog Bites (W54.99)',
    'J06.9': 'Acute Respiratory Infections (J06.9)',
    'J15': 'Bacterial pneumonia (J15)',
    'I10-0': 'Hypertension Level 1 (I10-0)',
    'I10.0': 'Hypertension Level 1 (I10-0)',  // Normalized
    'I10-1': 'Hypertension Level 2 (I10-1)',
    'I10.1': 'Hypertension Level 2 (I10-1)'  // Normalized
  };
  
  // Collect all diseases and their counts per month
  // API now returns all_diseases with all predictions, not just peak
  const diseaseData = {};
  
  // Initialize all known diseases
  const allDiseaseCodes = ['T14.1', 'W54.99', 'J06.9', 'J15', 'I10-1'];
  allDiseaseCodes.forEach(code => {
    diseaseData[code] = {};
    months.forEach(month => {
      diseaseData[code][month] = 0; // Initialize to 0
    });
  });
  
  // Fill in actual predictions (all diseases per month)
  // Only process months that have data in allPredictions
  monthsWithData.forEach(month => {
    const monthPrediction = allPredictions[month];
    if (monthPrediction && typeof monthPrediction === 'object' && !Array.isArray(monthPrediction)) {
      // Check if we have all_diseases (new format) or just disease/count (old format)
      if (monthPrediction.all_diseases) {
        // New format: all diseases with their counts
        Object.entries(monthPrediction.all_diseases).forEach(([diseaseCode, count]) => {
          // Filter out ZOO disease code
          if (diseaseCode === 'ZOO' || diseaseCode === 'zoo') {
            return;
          }
          // Normalize disease code (I10.1 -> I10-1, I10.0 -> I10-0)
          const normalizedCode = normalizeDiseaseCode(diseaseCode);
          if (!diseaseData[normalizedCode]) {
            diseaseData[normalizedCode] = {};
            months.forEach(m => {
              diseaseData[normalizedCode][m] = 0;
            });
          }
          // Accumulate counts if the same disease appears with different formats
          diseaseData[normalizedCode][month] = (diseaseData[normalizedCode][month] || 0) + count;
        });
      } else if (monthPrediction.disease && monthPrediction.count !== undefined) {
        // Old format: only peak disease (for backward compatibility)
        const diseaseCode = normalizeDiseaseCode(monthPrediction.disease);
        if (!diseaseData[diseaseCode]) {
          diseaseData[diseaseCode] = {};
          months.forEach(m => {
            diseaseData[diseaseCode][m] = 0;
          });
        }
        diseaseData[diseaseCode][month] = monthPrediction.count;
      }
    }
  });
  
  // Build table header
  const thead = table.querySelector('thead tr');
  thead.innerHTML = '<th>Disease</th>';
  months.forEach(month => {
    const th = document.createElement('th');
    th.textContent = month;
    th.style.textAlign = 'center';
    thead.appendChild(th);
  });
  
  // Build table body
  const tbody = table.querySelector('tbody');
  tbody.innerHTML = '';
  
  // Sort diseases by code and filter out ZOO
  const sortedDiseases = Object.keys(diseaseData)
    .filter(diseaseCode => diseaseCode !== 'ZOO' && diseaseCode !== 'zoo')
    .sort();
  
  sortedDiseases.forEach(diseaseCode => {
    const row = document.createElement('tr');
    
    // Disease name cell
    const diseaseCell = document.createElement('td');
    diseaseCell.textContent = diseaseDisplayNames[diseaseCode] || diseaseCode;
    diseaseCell.style.fontWeight = '500';
    row.appendChild(diseaseCell);
    
    // Month count cells
    months.forEach(month => {
      const countCell = document.createElement('td');
      const count = diseaseData[diseaseCode][month] || 0;
      countCell.textContent = count;
      countCell.style.textAlign = 'center';
      
      // Add color coding based on count
      if (count === 0) {
        countCell.textContent = '-';
        countCell.style.backgroundColor = '#f8f9fa';
        countCell.style.color = '#6c757d';
        countCell.style.fontStyle = 'italic';
      } else if (count < 20) {
        countCell.style.backgroundColor = '#d1ecf1';
        countCell.style.color = '#0c5460';
        countCell.style.fontWeight = '500';
      } else if (count < 40) {
        countCell.style.backgroundColor = '#fff3cd';
        countCell.style.color = '#856404';
        countCell.style.fontWeight = '600';
      } else {
        countCell.style.backgroundColor = '#f8d7da';
        countCell.style.color = '#721c24';
        countCell.style.fontWeight = '700';
      }
      
      row.appendChild(countCell);
    });
    
    tbody.appendChild(row);
  });
  
  // Show table container
  tableContainer.style.display = 'block';
}

// Function to update heat map based on selected disease and month with animation
async function updateHeatMap() {
  if (!map || !heat) {
    console.warn('Map or heat layer not initialized yet. Skipping heatmap update.');
    return;
  }
  
  const key = `${currentDisease}-${currentMonth}`;
  console.log(`Updating heatmap - Disease: ${currentDisease}, Month: ${currentMonth}, Key: ${key}`);
  
  // Try to fetch predictions from API
  if (!predictionsCache[currentMonth]) {
    try {
      const predictions = await fetchDiseasePeakPredictions(currentMonth || null);
      console.log('Fetched predictions from API:', predictions);
      if (predictions && !predictions.error) {
        // Extract the month data properly
        let monthData = null;
        if (predictions[currentMonth]) {
          monthData = predictions[currentMonth];
        } else if (predictions.disease || predictions.all_diseases) {
          monthData = predictions;
        } else {
          // Try to get the first value if it's an object
          const keys = Object.keys(predictions);
          if (keys.length > 0 && predictions[keys[0]]) {
            monthData = predictions[keys[0]];
          }
        }
        
        if (monthData) {
          // Store raw predictions for this month (don't overwrite other months)
          rawPredictionsCache[currentMonth] = monthData;
          // Convert predictions to heat data and cache
          const heatDataMap = convertPredictionsToHeatData(monthData, facilityCache);
          console.log('Converted heat data map keys:', Object.keys(heatDataMap));
          predictionsCache[currentMonth] = heatDataMap;
        }
      }
    } catch (error) {
      console.error('Error fetching predictions:', error);
    }
  }
  
  // Use cached predictions or fallback to sample data
  let heatData = [];
  let currentCount = null;
  
  if (predictionsCache[currentMonth] && predictionsCache[currentMonth][key]) {
    const points = predictionsCache[currentMonth][key];
    console.log(`Found ${points.length} points in cache for key: ${key}`);
    heatData = points.map(point => [point.lat, point.lng, point.intensity]);
    // Get count from first point (all points have same count)
    if (points.length > 0 && points[0].count !== undefined) {
      currentCount = points[0].count;
    }
  } else if (sampleData[key]) {
    // Fallback to sample data if API data not available
    console.log(`Using sample data for key: ${key}`);
    heatData = sampleData[key].map(point => [point.lat, point.lng, point.intensity]);
  } else {
    console.warn(`No data found for key: ${key} (neither in cache nor sample data)`);
    console.log('Available cache keys:', predictionsCache[currentMonth] ? Object.keys(predictionsCache[currentMonth]) : 'none');
    console.log('Available sample data keys:', Object.keys(sampleData).filter(k => k.startsWith(currentDisease)));
  }
  
  // Try to get count from countInfoCache if not found in points
  if (currentCount === null || currentCount === undefined) {
    if (countInfoCache[currentMonth] && countInfoCache[currentMonth][key]) {
      currentCount = countInfoCache[currentMonth][key].count;
      console.log(`Found count from countInfoCache: ${currentCount}`);
    }
  }
  
  // Try to get count from rawPredictionsCache if still not found
  if ((currentCount === null || currentCount === undefined) && rawPredictionsCache[currentMonth]) {
    const monthPrediction = rawPredictionsCache[currentMonth];
    
    // Get disease code from current disease filter key (reverse lookup)
    let targetDiseaseCode = null;
    for (const [code, filterKey] of Object.entries(diseaseCodeToFilter)) {
      if (filterKey === currentDisease) {
        targetDiseaseCode = code;
        break;
      }
    }
    
    if (monthPrediction.all_diseases) {
      // New format: all diseases with their counts
      // Try to find the count for this disease by matching disease codes
      for (const [code, count] of Object.entries(monthPrediction.all_diseases)) {
        const normalized = normalizeDiseaseCode(code);
        const normalizedTarget = targetDiseaseCode ? normalizeDiseaseCode(targetDiseaseCode) : null;
        
        // Match by exact code, normalized code, or filter key
        if (code === targetDiseaseCode || 
            normalized === normalizedTarget ||
            diseaseCodeToFilter[code] === currentDisease || 
            diseaseCodeToFilter[normalized] === currentDisease) {
          currentCount = count;
          console.log(`Found count from rawPredictionsCache.all_diseases: ${currentCount} for ${code} (currentDisease: ${currentDisease})`);
          break;
        }
      }
    } else if (monthPrediction.disease && monthPrediction.count !== undefined) {
      // Old format: check if it matches current disease
      const predictionDiseaseCode = normalizeDiseaseCode(monthPrediction.disease);
      const normalizedTarget = targetDiseaseCode ? normalizeDiseaseCode(targetDiseaseCode) : null;
      
      if (monthPrediction.disease === targetDiseaseCode ||
          predictionDiseaseCode === normalizedTarget || 
          diseaseCodeToFilter[monthPrediction.disease] === currentDisease ||
          diseaseCodeToFilter[predictionDiseaseCode] === currentDisease) {
        currentCount = monthPrediction.count;
        console.log(`Found count from rawPredictionsCache.count: ${currentCount} (currentDisease: ${currentDisease})`);
      }
    }
  }
  
  // Update count display
  updateCountDisplay(currentCount);
  
  // Update summary table if we have predictions
  // Always use the full cache to show all months, not just the current one
  if (Object.keys(rawPredictionsCache).length > 0) {
    // Create a copy of the cache to ensure we're showing all months
    const allPredictionsForTable = { ...rawPredictionsCache };
    updatePredictionTable(allPredictionsForTable);
    updateRawDataTable(allPredictionsForTable);
  }
  
  // Fade out current heat
  heat.setOptions({ opacity: 0 });
  
  // Update data and fade in
  setTimeout(() => {
    heat.setLatLngs(heatData);
    heat.setOptions({ opacity: 1 });
  }, 300);
}

// Function to update count display
function updateCountDisplay(count) {
  // Create or update count display element
  let countDisplay = document.getElementById('prediction-count-display');
  const monthContainer = document.getElementById('month-container');
  const mapContainer = document.getElementById('map');
  
  if (!countDisplay) {
    countDisplay = document.createElement('div');
    countDisplay.id = 'prediction-count-display';
    countDisplay.className = 'alert alert-info mt-3 mb-3';
    countDisplay.style.fontSize = '14px';
    
    // Insert after the month container's parent (disease-filter div), before the map
    if (monthContainer && monthContainer.parentElement && mapContainer) {
      // Find the parent disease-filter div that contains the month container
      let parentDiv = monthContainer.parentElement;
      // Insert after the parent div, before the map
      if (parentDiv && parentDiv.parentElement) {
        parentDiv.parentElement.insertBefore(countDisplay, mapContainer);
      } else {
        // Fallback: insert before map
        mapContainer.parentElement.insertBefore(countDisplay, mapContainer);
      }
    } else if (mapContainer && mapContainer.parentElement) {
      // Fallback: insert before map if month container not found
      mapContainer.parentElement.insertBefore(countDisplay, mapContainer);
    }
  }
  
  // Get disease name (should include the code like "Open Wounds (T14.1)")
  const diseaseBadge = document.querySelector('.disease-badge.active') || 
                        document.querySelector('.disease-badge[data-disease="' + currentDisease + '"]');
  let diseaseName = currentDisease;
  if (diseaseBadge) {
    diseaseName = diseaseBadge.textContent.trim();
  }
  
  // Get month name (should include year like "January 2026")
  const monthBadge = document.querySelector('.month-badge.active');
  let monthName = currentMonth || 'Current Month';
  if (monthBadge) {
    monthName = monthBadge.textContent.trim();
  }
  
  // Format the message as requested
  if (count !== null && count !== undefined && count > 0) {
    countDisplay.innerHTML = `
      <strong>Prediction Summary:</strong> Predicted "${count}" cases of ${diseaseName} for ${monthName}<br>
      <small class="text-muted d-block mt-1">Check the summary table below for detailed predictions by month</small>
    `;
    countDisplay.style.display = 'block';
  } else {
    // Show message even without count
    countDisplay.innerHTML = `
      <strong>Prediction Summary:</strong> Viewing ${diseaseName} for ${monthName}<br>
      <small class="text-muted d-block mt-1">Check the summary table below for detailed predictions by month</small>
    `;
    countDisplay.style.display = 'block';
  }
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
  
  // Clear existing month badges
  monthContainer.innerHTML = '';
  
  // Generate all 12 months for 2026
  const targetYear = 2026;
  for (let i = 0; i < 12; i++){
    let monthDate = months[i];
    let monthKey = monthDate;

    let monthBadge = document.createElement("span");
    monthBadge.className = "disease-badge month-badge";
    monthBadge.textContent = `${monthDate} ${targetYear}`;
    monthBadge.dataset.month = monthKey;
    
    // Set first month (January) as active by default
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



// Initialize with current month data (will be set by getCurrentMonth)
// updateHeatMap() will be called after getCurrentMonth() in DOMContentLoaded
// plotFacilityMarkers() will be called after map initialization in DOMContentLoaded

// Add click handlers for disease filters with enhanced feedback
document.addEventListener('DOMContentLoaded', async function() {
  console.log('DOM Content Loaded - Initializing heatmap...');
  
  // Initialize map first
  initializeMap();
  
  // Fetch all predictions FIRST to populate the summary table with all months
  await fetchAllPredictions().then(() => {
    console.log('All predictions fetched, updating table...');
    // Update table with all predictions after fetching
    // Always try to update the table, even if cache is empty (will show empty table)
    updatePredictionTable(rawPredictionsCache);
    updateRawDataTable(rawPredictionsCache);
  });
  
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
  
  // Add click handlers for disease filter badges
  document.querySelectorAll('.disease-badge[data-disease]').forEach(badge => {
    badge.addEventListener('click', function() {
      // Remove active class and reset styles from all disease badges
      document.querySelectorAll('.disease-badge[data-disease]').forEach(b => {
        b.classList.remove('active');
        b.style.transform = 'scale(1)';
      });
      
      // Add active class to clicked badge
      this.classList.add('active');
      this.style.transform = 'scale(1.1)';
      
      // Update current disease and refresh map
      currentDisease = this.dataset.disease;
      console.log('Disease selected:', currentDisease);
      updateHeatMap();
    });
  });
}); 