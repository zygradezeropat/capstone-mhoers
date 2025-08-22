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

// Call plotFacilityMarkers after map initialization
plotFacilityMarkers();

