// Global variables for current selections
let currentDisease = 'open_wounds';
let currentMonth = '';
let currentYear = 2025; // Default to 2025 (prediction year based on 2023-2024 data)
// Cache of facilities and markers for quick lookup and filtering
let facilityCache = [];
let facilityIdToMarker = new Map();
let selectedFacilityId = null;
// Facility layer group for toggling visibility (will be initialized when map is ready)
let facilityLayerGroup = null;

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

// Modern pin marker icons - teardrop shape with white circle
const mhoIcon = L.divIcon({
  className: 'facility-marker mho-marker',
  html: `
    <svg width="32" height="40" viewBox="0 0 32 40" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">
      <path d="M16 0 C10 0, 4 4, 4 10 C4 16, 16 32, 16 32 C16 32, 28 16, 28 10 C28 4, 22 0, 16 0 Z" 
            fill="#2563eb" stroke="none"/>
      <circle cx="16" cy="14" r="6" fill="white"/>
    </svg>
  `,
  iconSize: [32, 40],
  iconAnchor: [16, 40],
  popupAnchor: [0, -40]
});

const bhcIcon = L.divIcon({
  className: 'facility-marker bhc-marker',
  html: `
    <svg width="28" height="36" viewBox="0 0 32 40" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">
      <path d="M16 0 C10 0, 4 4, 4 10 C4 16, 16 32, 16 32 C16 32, 28 16, 28 10 C28 4, 22 0, 16 0 Z" 
            fill="#2563eb" stroke="none"/>
      <circle cx="16" cy="14" r="6" fill="white"/>
    </svg>
  `,
  iconSize: [28, 36],
  iconAnchor: [14, 36],
  popupAnchor: [0, -36]
});

const otherFacilityIcon = L.divIcon({
  className: 'facility-marker other-marker',
  html: `
    <svg width="24" height="32" viewBox="0 0 32 40" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">
      <path d="M16 0 C10 0, 4 4, 4 10 C4 16, 16 32, 16 32 C16 32, 28 16, 28 10 C28 4, 22 0, 16 0 Z" 
            fill="#2563eb" stroke="none"/>
      <circle cx="16" cy="14" r="6" fill="white"/>
    </svg>
  `,
  iconSize: [24, 32],
  iconAnchor: [12, 32],
  popupAnchor: [0, -32]
});

// Function to create custom numbered marker icon with percentage-based color
function createNumberedMarkerIcon(number, percentage = 0) {
  const size = 40;
  const className = 'numbered-marker';
  
  // Determine color based on percentage of total cases - use pure colors to match heatmap
  // Pure Green: 0-20% of total
  // Pure Yellow: 21-60% of total
  // Pure Red: 61-100% of total
  let bgColor, textColor;
  if (percentage === 0 || number === '0') {
    bgColor = '#f8f9fa';  // Gray for zero
    textColor = '#6c757d';
  } else if (percentage <= 20) {
    bgColor = '#00ff00';  // Pure green for low percentage (0-20%)
    textColor = '#000000';  // Black text for contrast
  } else if (percentage <= 60) {
    bgColor = '#ffff00';  // Pure yellow for medium percentage (21-60%)
    textColor = '#000000';  // Black text for contrast
  } else {
    bgColor = '#ff0000';  // Pure red for high percentage (61-100%)
    textColor = '#ffffff';  // White text for contrast
  }
  
  // Use border color that matches the background for pure color effect
  const borderColor = (percentage === 0 || number === '0') ? 'white' : bgColor;
  
  return L.divIcon({
    className: className,
    html: `
      <div style="
        background-color: ${bgColor};
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        border: 3px solid ${borderColor};
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
        color: ${textColor};
        text-align: center;
        line-height: 1;
      ">
        ${number}
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
    popupAnchor: [0, -size/2]
  });
}

// Function to get predicted cases for a facility/barangay
function getPredictedCasesForBarangay(barangayName, diseaseCode, monthNum, barangayPredictions) {
  if (!barangayPredictions || barangayPredictions.error) return 0;
  
  // Filter out poblacion
  const filteredPredictions = {};
  Object.keys(barangayPredictions).forEach(b => {
    if (!b.toLowerCase().includes('poblacion')) {
      filteredPredictions[b] = barangayPredictions[b];
    }
  });
  
  // Try to find matching barangay (case-insensitive, handle variations)
  const matchingBarangay = Object.keys(filteredPredictions).find(b => {
    const bLower = b.toLowerCase().trim();
    const nameLower = barangayName.toLowerCase().trim();
    return bLower === nameLower || 
           bLower.includes(nameLower) || 
           nameLower.includes(bLower);
  });
  
  if (!matchingBarangay) return 0;
  
  const months = filteredPredictions[matchingBarangay];
  if (!months || !months[monthNum] || !months[monthNum].all_diseases) return 0;
  
  const monthData = months[monthNum].all_diseases;
  // Try to get the disease count (handle normalized codes)
  const normalizedCode = normalizeDiseaseCode(diseaseCode);
  return monthData[diseaseCode] || monthData[normalizedCode] || 0;
}

// Function to update marker icons - show regular map markers (no numbers)
async function updateMarkerIntensities() {
  // Check if year is 2025 - if not, clear data
  if (currentYear !== 2025) {
    // Clear all marker popups and show no data message
    facilityCache.forEach((facility) => {
      const marker = facilityIdToMarker.get(String(facility.facility_id));
      if (!marker) return;
      
      marker.setOpacity(1);
      marker.options.interactive = true;
      
      let icon = otherFacilityIcon;
      if (facility.name.includes('MHO')) {
        icon = mhoIcon;
      } else if (facility.name.includes('BHC')) {
        icon = bhcIcon;
      }
      
      marker.setIcon(icon);
      
      // Update popup with no data message
      const popupContent = `
        <div style="min-width: 200px;">
          <strong>Facility:</strong> ${facility.name}<br>
          <strong>Disease:</strong> -<br>
          <strong>Predicted:</strong> No data available<br>
          <small class="text-muted">Predictions only available for 2025</small>
        </div>
      `;
      marker.setPopupContent(popupContent);
    });
    return;
  }
  
  if (!currentDisease || !currentMonth) {
    // If no selection, show default markers without disease info
    facilityCache.forEach((facility) => {
      const marker = facilityIdToMarker.get(String(facility.facility_id));
      if (!marker) return;
      
      marker.setOpacity(1);
      marker.options.interactive = true;
      
      let icon = otherFacilityIcon;
      if (facility.name.includes('MHO')) {
        icon = mhoIcon;
      } else if (facility.name.includes('BHC')) {
        icon = bhcIcon;
      }
      
      marker.setIcon(icon);
      
      // Update popup with basic info
      const popupContent = `
        <div style="min-width: 200px;">
          <strong>Facility:</strong> ${facility.name}<br>
          <strong>Disease:</strong> -<br>
          <strong>Predicted:</strong> -
        </div>
      `;
      marker.setPopupContent(popupContent);
    });
    return;
  }
  
  // Get disease code from current disease filter
  let targetDiseaseCode = null;
  for (const [code, filterKey] of Object.entries(diseaseCodeToFilter)) {
    if (filterKey === currentDisease) {
      targetDiseaseCode = code;
      break;
    }
  }
  
  if (!targetDiseaseCode) return;
  
  // Get disease display name
  const diseaseDisplayNames = {
    'T14.1': 'Open Wounds (T14.1)',
    'W54.99': 'Dog Bites (W54.99)',
    'J06.9': 'Acute Respiratory Infections (J06.9)',
    'J15': 'Bacterial pneumonia (J15)',
    'I10.1': 'Hypertension Level 2 (I10.1)',
    'I10-1': 'Hypertension Level 2 (I10-1)'
  };
  const diseaseName = diseaseDisplayNames[targetDiseaseCode] || targetDiseaseCode;
  
  // Check if month range is selected
  const monthFrom = document.getElementById('month-from');
  const monthTo = document.getElementById('month-to');
  let isMonthRange = false;
  let monthsInRange = [];
  
  if (monthFrom && monthTo && monthFrom.value && monthTo.value) {
    const fromParts = monthFrom.value.split(' ');
    const toParts = monthTo.value.split(' ');
    const fromMonth = fromParts[0];
    const toMonth = toParts[0];
    
    const allMonths = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"];
    const fromIndex = allMonths.indexOf(fromMonth);
    const toIndex = allMonths.indexOf(toMonth);
    
    if (fromIndex !== -1 && toIndex !== -1 && fromIndex <= toIndex) {
      isMonthRange = true;
      monthsInRange = allMonths.slice(fromIndex, toIndex + 1);
    }
  }
  
  // Get month number mapping
  const monthNames = {
    'January': '1', 'February': '2', 'March': '3', 'April': '4',
    'May': '5', 'June': '6', 'July': '7', 'August': '8',
    'September': '9', 'October': '10', 'November': '11', 'December': '12'
  };
  
  // Get barangay predictions
  const barangayPredictions = await fetchBarangayDiseasePeakPredictions();
  
  // Show regular facility markers (map pins) without numbers
  facilityCache.forEach((facility) => {
    const marker = facilityIdToMarker.get(String(facility.facility_id));
    if (!marker) return;
    
    // Ensure marker is visible and interactive
    marker.setOpacity(1);
    marker.options.interactive = true;
    
    // Use default facility icons (MHO, BHC, or other) - no numbers
    let icon = otherFacilityIcon;
    if (facility.name.includes('MHO')) {
      icon = mhoIcon;
    } else if (facility.name.includes('BHC')) {
      icon = bhcIcon;
    }
    
    marker.setIcon(icon);
    
    // Calculate predicted cases for this facility
    let predictedCases = 0;
    if (isMonthRange && monthsInRange.length > 0) {
      // Month range selected - aggregate cases across all months
      monthsInRange.forEach(month => {
        const monthNum = monthNames[month] || month.replace(/\D/g, '');
        const monthCases = getPredictedCasesForBarangay(
          facility.name,
          targetDiseaseCode,
          monthNum,
          barangayPredictions
        );
        predictedCases += monthCases;
      });
    } else {
      // Single month selected
      const monthNum = monthNames[currentMonth] || currentMonth.replace(/\D/g, '');
      predictedCases = getPredictedCasesForBarangay(
        facility.name,
        targetDiseaseCode,
        monthNum,
        barangayPredictions
      );
    }
    
    // Format the number (show 1 decimal if needed, otherwise integer)
    const displayCount = predictedCases > 0 
      ? (predictedCases % 1 === 0 ? predictedCases.toFixed(0) : predictedCases.toFixed(1))
      : '0';
    
    // Update popup with requested format
    const popupContent = `
      <div style="min-width: 200px;">
        <strong>Facility:</strong> ${facility.name}<br>
        <strong>Disease:</strong> ${diseaseName}<br>
        <strong>Predicted:</strong> ${displayCount}
      </div>
    `;
    marker.setPopupContent(popupContent);
  });
}

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
  
  // Initialize facility layer group if not already done
  if (!facilityLayerGroup) {
    facilityLayerGroup = L.layerGroup();
  }
  
  // Clear existing markers
  facilityLayerGroup.clearLayers();
  facilityIdToMarker.clear();
  
  facilityCache = await fetchFacilities();
  // Populate dropdown
  populateFacilityDropdown();
  
  facilityCache.forEach((facility) => {
    // Initial popup content (will be updated by updateMarkerIntensities when filters are selected)
    let popupContent = `
      <div style="min-width: 200px;">
        <strong>Facility:</strong> ${facility.name}<br>
        <strong>Disease:</strong> -<br>
        <strong>Predicted:</strong> -
      </div>
    `;

    // Determine icon based on facility type - use enhanced icons
    let icon = otherFacilityIcon;
    if (facility.name.includes('MHO')) {
      icon = mhoIcon;
    } else if (facility.name.includes('BHC')) {
      icon = bhcIcon;
    }

    const marker = L.marker([facility.latitude, facility.longitude], { 
      icon,
      zIndexOffset: 1000  // Ensure markers appear above heat layer
    })
      .addTo(facilityLayerGroup)
      .bindPopup(popupContent, {
        maxWidth: 250,
        className: 'facility-popup'
      });

    // Store marker by facility id for later focusing
    facilityIdToMarker.set(String(facility.facility_id), marker);

    // Enhanced hover effects
    marker.on('mouseover', function() {
      // Highlight the marker by bringing it to front
      marker.setZIndexOffset(2000);
      // Optionally open popup on hover (uncomment if desired)
      // marker.openPopup();
    });

    marker.on('mouseout', function() {
      // Reset z-index
      marker.setZIndexOffset(1000);
      // Optionally close popup on mouseout (uncomment if desired)
      // marker.closePopup();
    });

    // When a marker is clicked, update the info panel and remember selection
    marker.on('click', () => {
      selectedFacilityId = String(facility.facility_id);
      // Open popup without zooming - stay at current position
      marker.openPopup();
      updateFacilityInfoPanel(facility);
    });
  });
  
  // Add facility layer to map
  facilityLayerGroup.addTo(map);
  
  // Add layer control if it doesn't exist
  if (!window.layerControl) {
    window.layerControl = L.control.layers(
      {}, // Base layers (none for now)
      {
        
      },
      {
        position: 'topright',
        collapsed: false
      }
    ).addTo(map);
  }
  
  // Make layers globally accessible
  window.facilityLayerGroup = facilityLayerGroup;
  window.heat = heat;
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

  // Initialize heat layer with pure color zones based on case percentages
  heat = L.heatLayer([], {
    radius: 40,
    blur: 25,
    maxZoom: 10,
    max: 1.0,
    gradient: {
      0.0: '#00ffff',  // Cyan - Low
      0.33: '#00ff00', // Green - Light
      0.66: '#ffff00', // Yellow - Moderate
      1.0: '#ff0000'   // Red - Severe
    }
  }).addTo(map);
  
  // Initialize facility layer group
  if (!facilityLayerGroup) {
    facilityLayerGroup = L.layerGroup();
  }
  
  // Make layers globally accessible
  window.heat = heat;
  window.facilityLayerGroup = facilityLayerGroup;
  window.map = map;
  
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
// Cache for barangay predictions (to avoid multiple API calls)
let barangayPredictionsCache = null;

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

// Function to fetch barangay disease peak predictions from API (with caching)
async function fetchBarangayDiseasePeakPredictions(forceRefresh = false) {
  // Return cached data if available and not forcing refresh
  if (!forceRefresh && barangayPredictionsCache !== null) {
    console.log('Using cached barangay predictions');
    return barangayPredictionsCache;
  }
  
  try {
    console.log('Fetching barangay predictions from API...');
    const url = `/analytics/api/barangay-disease-peak-predictions/`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    // Cache the result
    barangayPredictionsCache = data;
    console.log('Barangay predictions cached');
    return data;
  } catch (error) {
    console.error('Error fetching barangay disease peak predictions:', error);
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
  // Note: updatePredictionTable now uses barangay predictions, so we don't need to call it here
  // The table will be updated when barangay predictions are loaded
  
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

// Function to update prediction summary table using barangay-based predictions
async function updatePredictionTable(allPredictions) {
  const tableContainer = document.getElementById('prediction-table-container');
  const table = document.getElementById('prediction-summary-table');
  
  if (!tableContainer || !table) {
    console.error('Table elements not found');
    return;
  }
  
  // Always show all 12 months, even if some don't have data
  const allMonths = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];
  
  // Month number to name mapping
  const monthNumToName = {
    '1': 'January', '2': 'February', '3': 'March', '4': 'April',
    '5': 'May', '6': 'June', '7': 'July', '8': 'August',
    '9': 'September', '10': 'October', '11': 'November', '12': 'December'
  };
  
  const months = allMonths;
  
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
  
  // Fetch barangay predictions
  const barangayPredictions = await fetchBarangayDiseasePeakPredictions();
  
  // Initialize disease data structure (use normalized codes only to avoid duplicates)
  const diseaseData = {};
  // Use normalized codes only - normalize I10.1 to I10-1
  const allDiseaseCodes = ['T14.1', 'W54.99', 'J06.9', 'J15', 'I10-1'];
  allDiseaseCodes.forEach(code => {
    diseaseData[code] = {};
    months.forEach(month => {
      diseaseData[code][month] = 0; // Initialize to 0
    });
  });
  
  // If barangay predictions are available, use them to calculate totals
  if (barangayPredictions && !barangayPredictions.error) {
    // Sum up predictions from all barangays by disease and month
    Object.keys(barangayPredictions).forEach(barangay => {
      // Filter out poblacion
      if (barangay.toLowerCase().includes('poblacion')) {
        return;
      }
      
      const months = barangayPredictions[barangay];
      Object.keys(months).forEach(monthNum => {
        const monthName = monthNumToName[monthNum];
        if (!monthName) return;
        
        const monthData = months[monthNum];
        if (monthData && monthData.all_diseases) {
          // Sum up all diseases for this barangay and month
          Object.entries(monthData.all_diseases).forEach(([diseaseCode, count]) => {
            // Normalize disease code
            const normalizedCode = normalizeDiseaseCode(diseaseCode);
            if (diseaseData[normalizedCode] && diseaseData[normalizedCode][monthName] !== undefined) {
              diseaseData[normalizedCode][monthName] += count;
            }
          });
        }
      });
    });
  } else {
    // Fallback to old method if barangay predictions not available
    const monthsWithData = Object.keys(allPredictions).sort((a, b) => {
      return allMonths.indexOf(a) - allMonths.indexOf(b);
    });
    
    monthsWithData.forEach(month => {
      const monthPrediction = allPredictions[month];
      if (monthPrediction && typeof monthPrediction === 'object' && !Array.isArray(monthPrediction)) {
        if (monthPrediction.all_diseases) {
          Object.entries(monthPrediction.all_diseases).forEach(([diseaseCode, count]) => {
            if (diseaseCode === 'ZOO' || diseaseCode === 'zoo') {
              return;
            }
            const normalizedCode = normalizeDiseaseCode(diseaseCode);
            if (!diseaseData[normalizedCode]) {
              diseaseData[normalizedCode] = {};
              months.forEach(m => {
                diseaseData[normalizedCode][m] = 0;
              });
            }
            diseaseData[normalizedCode][month] = (diseaseData[normalizedCode][month] || 0) + count;
          });
        } else if (monthPrediction.disease && monthPrediction.count !== undefined) {
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
  }
  
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
  
  // Sort diseases by code, filter out ZOO, and ensure no duplicates after normalization
  const normalizedDiseaseData = {};
  Object.keys(diseaseData).forEach(code => {
    if (code === 'ZOO' || code === 'zoo') return;
    const normalized = normalizeDiseaseCode(code);
    if (!normalizedDiseaseData[normalized]) {
      normalizedDiseaseData[normalized] = diseaseData[code];
    } else {
      // Merge data if duplicate found (shouldn't happen with proper normalization, but just in case)
      months.forEach(month => {
        normalizedDiseaseData[normalized][month] = (normalizedDiseaseData[normalized][month] || 0) + (diseaseData[code][month] || 0);
      });
    }
  });
  
  const sortedDiseases = Object.keys(normalizedDiseaseData)
    .filter(diseaseCode => {
      const count = months.reduce((sum, month) => sum + (normalizedDiseaseData[diseaseCode][month] || 0), 0);
      return count > 0; // Only show diseases with data
    })
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
      const count = normalizedDiseaseData[diseaseCode][month] || 0;
      // Format count: show 2 decimal places if it's a decimal, otherwise show as integer
      const formattedCount = count % 1 === 0 ? count.toFixed(0) : count.toFixed(2);
      countCell.textContent = formattedCount;
      countCell.style.textAlign = 'center';
      
      // Add color coding based on count (adjusted for smaller decimal values)
      if (count === 0) {
        countCell.textContent = '-';
        countCell.style.backgroundColor = '#f8f9fa';
        countCell.style.color = '#6c757d';
        countCell.style.fontStyle = 'italic';
      } else if (count < 5) {
        countCell.style.backgroundColor = '#d1ecf1';
        countCell.style.color = '#0c5460';
        countCell.style.fontWeight = '500';
      } else if (count < 15) {
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

// Function to update barangay disease predictions table
async function updateBarangayPredictionTable() {
  const tableContainer = document.getElementById('barangay-prediction-table-container');
  const table = document.getElementById('barangay-prediction-table');
  
  if (!tableContainer || !table) {
    console.error('Barangay table elements not found');
    return;
  }
  
  // Fetch barangay predictions
  const barangayPredictions = await fetchBarangayDiseasePeakPredictions();
  
  if (!barangayPredictions || barangayPredictions.error) {
    console.error('Error loading barangay predictions:', barangayPredictions?.error || 'Unknown error');
    tableContainer.style.display = 'none';
    return;
  }
  
  // Disease display names
  const diseaseDisplayNames = {
    'T14.1': 'Open Wounds (T14.1)',
    'W54.99': 'Dog Bites (W54.99)',
    'J06.9': 'Acute Respiratory Infections (J06.9)',
    'J15': 'Bacterial pneumonia (J15)',
    'I10.0': 'Hypertension Level 1 (I10.0)',
    'I10.1': 'Hypertension Level 2 (I10.1)',
    'I10-1': 'Hypertension Level 2 (I10-1)'
  };
  
  // Month names
  const monthNames = {
    '1': 'January', '2': 'February', '3': 'March', '4': 'April',
    '5': 'May', '6': 'June', '7': 'July', '8': 'August',
    '9': 'September', '10': 'October', '11': 'November', '12': 'December'
  };
  
  // Build table body
  const tbody = table.querySelector('tbody');
  tbody.innerHTML = '';
  
  // Sort barangays alphabetically and filter out "poblacion" (case-insensitive)
  const sortedBarangays = Object.keys(barangayPredictions)
    .filter(barangay => !barangay.toLowerCase().includes('poblacion'))
    .sort();
  
  sortedBarangays.forEach(barangay => {
    const months = barangayPredictions[barangay];
    
    // Sort months numerically
    const sortedMonths = Object.keys(months).sort((a, b) => parseInt(a) - parseInt(b));
    
    sortedMonths.forEach(monthNum => {
      const monthData = months[monthNum];
      if (!monthData) return;
      
      const row = document.createElement('tr');
      
      // Barangay cell
      const barangayCell = document.createElement('td');
      barangayCell.textContent = barangay;
      barangayCell.style.fontWeight = '600';
      row.appendChild(barangayCell);
      
      // Month cell
      const monthCell = document.createElement('td');
      monthCell.textContent = monthNames[monthNum] || monthNum;
      row.appendChild(monthCell);
      
      // Peak disease cell
      const peakDiseaseCell = document.createElement('td');
      const peakDisease = monthData.peak_disease || 'N/A';
      peakDiseaseCell.textContent = diseaseDisplayNames[peakDisease] || peakDisease;
      peakDiseaseCell.style.fontWeight = '500';
      row.appendChild(peakDiseaseCell);
      
      // Peak cases cell
      const peakCasesCell = document.createElement('td');
      const peakCases = monthData.peak_cases || 0;
      peakCasesCell.textContent = peakCases.toFixed(2);
      peakCasesCell.style.textAlign = 'center';
      peakCasesCell.style.fontWeight = '600';
      
      // Color code based on case count
      if (peakCases === 0) {
        peakCasesCell.style.backgroundColor = '#f8f9fa';
        peakCasesCell.style.color = '#6c757d';
      } else if (peakCases < 3) {
        peakCasesCell.style.backgroundColor = '#d1ecf1';
        peakCasesCell.style.color = '#0c5460';
      } else if (peakCases < 5) {
        peakCasesCell.style.backgroundColor = '#fff3cd';
        peakCasesCell.style.color = '#856404';
      } else {
        peakCasesCell.style.backgroundColor = '#f8d7da';
        peakCasesCell.style.color = '#721c24';
      }
      
      row.appendChild(peakCasesCell);
      
      // All diseases cell (formatted list)
      const allDiseasesCell = document.createElement('td');
      const allDiseases = monthData.all_diseases || {};
      const diseaseList = Object.entries(allDiseases)
        .map(([disease, count]) => {
          const displayName = diseaseDisplayNames[disease] || disease;
          return `${displayName}: ${count.toFixed(2)}`;
        })
        .join(', ');
      allDiseasesCell.textContent = diseaseList || 'No data';
      allDiseasesCell.style.fontSize = '0.9em';
      allDiseasesCell.style.maxWidth = '400px';
      row.appendChild(allDiseasesCell);
      
      tbody.appendChild(row);
    });
  });
  
  // Show table container
  if (tbody.children.length > 0) {
    tableContainer.style.display = 'block';
  } else {
    tableContainer.style.display = 'none';
  }
}

// Function to update heat map based on selected disease and month with animation
async function updateHeatMap() {
  if (!map || !heat) {
    console.warn('Map or heat layer not initialized yet. Skipping heatmap update.');
    return;
  }
  
  // Check if current year has prediction data (only 2025 has data)
  if (currentYear !== 2025) {
    console.warn(`No prediction data available for year ${currentYear}. Only 2025 has predictions based on 2023-2024 data.`);
    
    // Clear heatmap
    if (heat) {
      heat.setLatLngs([]);
    }
    // Hide prediction summary when no data available
    const countDisplay = document.getElementById('prediction-count-display');
    if (countDisplay) {
      countDisplay.style.display = 'none';
    }
    return;
  }
  
  // Check if any months are selected - if not, clear heatmap and return
  const monthFrom = document.getElementById('month-from');
  const monthTo = document.getElementById('month-to');
  // Check if dropdowns have valid month selections (not empty, not "Select Month")
  const hasMonthFrom = monthFrom && monthFrom.value && 
                       monthFrom.value.trim() !== '' && 
                       !monthFrom.value.toLowerCase().includes('select month');
  const hasMonthTo = monthTo && monthTo.value && 
                     monthTo.value.trim() !== '' && 
                     !monthTo.value.toLowerCase().includes('select month');
  // Only check dropdowns, not currentMonth (which might have stale value)
  const hasAnyMonthSelected = hasMonthFrom || hasMonthTo;
  
  if (!hasAnyMonthSelected) {
    // No months selected - clear heatmap but keep markers visible
    console.log('No months selected - clearing heatmap');
    if (heat) {
      heat.setLatLngs([]);
    }
    // Hide prediction summary
    const countDisplay = document.getElementById('prediction-count-display');
    if (countDisplay) {
      countDisplay.style.display = 'none';
    }
    // Clear currentMonth to prevent stale data
    currentMonth = '';
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
  
  // Generate heat points using per-facility counts (same as markers) for accurate matching
  let heatData = [];
  let currentCount = null;
  
  // Get disease code from current disease filter
  let targetDiseaseCode = null;
  for (const [code, filterKey] of Object.entries(diseaseCodeToFilter)) {
    if (filterKey === currentDisease) {
      targetDiseaseCode = code;
      break;
    }
  }
  
  // Check if month range is selected (monthFrom and monthTo already declared above)
  let isMonthRange = false;
  let monthsInRange = [];
  
  if (monthFrom && monthTo && monthFrom.value && monthTo.value) {
    const fromParts = monthFrom.value.split(' ');
    const toParts = monthTo.value.split(' ');
    const fromMonth = fromParts[0];
    const toMonth = toParts[0];
    
    const allMonths = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"];
    const fromIndex = allMonths.indexOf(fromMonth);
    const toIndex = allMonths.indexOf(toMonth);
    
    if (fromIndex !== -1 && toIndex !== -1 && fromIndex <= toIndex) {
      isMonthRange = true;
      monthsInRange = allMonths.slice(fromIndex, toIndex + 1);
    }
  }
  
  if (!targetDiseaseCode || !facilityCache || facilityCache.length === 0) {
    // Fallback to cached data if available
    if (predictionsCache[currentMonth] && predictionsCache[currentMonth][key]) {
      const allPoints = predictionsCache[currentMonth][key];
      heatData = allPoints.map(point => [point.lat, point.lng, point.intensity || 0.5]);
      if (allPoints.length > 0 && allPoints[0].count !== undefined) {
        currentCount = allPoints[0].count;
      }
    }
  } else {
    // Use barangay predictions to get per-facility counts (same as markers)
    const monthNames = {
      'January': '1', 'February': '2', 'March': '3', 'April': '4',
      'May': '5', 'June': '6', 'July': '7', 'August': '8',
      'September': '9', 'October': '10', 'November': '11', 'December': '12'
    };
    
    const barangayPredictions = await fetchBarangayDiseasePeakPredictions();
    
    // Calculate per-facility cases and total (same logic as markers)
    const facilityCases = new Map();
    let totalCases = 0;
    
    if (isMonthRange && monthsInRange.length > 0) {
      // Month range selected - aggregate cases across all months (same as markers)
      facilityCache.forEach((facility) => {
        let aggregatedCases = 0;
        
        // Sum up cases for each month in the range
        monthsInRange.forEach(month => {
          const monthNum = monthNames[month] || month.replace(/\D/g, '');
          const monthCases = getPredictedCasesForBarangay(
            facility.name,
            targetDiseaseCode,
            monthNum,
            barangayPredictions
          );
          aggregatedCases += monthCases;
        });
        
        facilityCases.set(facility.facility_id, aggregatedCases);
        totalCases += aggregatedCases;
      });
    } else if (currentMonth) {
      // Single month selected - only process if currentMonth is set
      const monthNum = monthNames[currentMonth] || currentMonth.replace(/\D/g, '');
      
      facilityCache.forEach((facility) => {
        const predictedCases = getPredictedCasesForBarangay(
          facility.name,
          targetDiseaseCode,
          monthNum,
          barangayPredictions
        );
        facilityCases.set(facility.facility_id, predictedCases);
        totalCases += predictedCases;
      });
    } else {
      // No month selected - clear heatmap
      if (heat) {
        heat.setLatLngs([]);
      }
      return;
    }
    
    // Get total cases for display
    if (facilityCases.size > 0) {
      currentCount = Array.from(facilityCases.values()).reduce((sum, count) => sum + count, 0);
    }
    
    // Prepare normalization values for intensity scaling
    const facilityValues = Array.from(facilityCases.values()).filter(value => value > 0);
    const maxCases = facilityValues.length > 0 ? Math.max(...facilityValues) : 0;
    
    facilityCache.forEach((facility) => {
      if (!facility.latitude || !facility.longitude) return;
      
      const predictedCases = facilityCases.get(facility.facility_id) || 0;
      if (predictedCases <= 0) {
        return; // No predicted cases for this facility
      }
      
      // Normalize predicted cases into 0-1 range for heat intensity
      let intensity = 0.2;
      if (maxCases > 0) {
        intensity = predictedCases / maxCases;
      }
      intensity = Math.max(0.2, Math.min(1.0, intensity));
      
      // Create multiple points per facility for better heat visualization
      const pointsPerFacility = Math.max(1, Math.ceil(predictedCases / 5));
      for (let i = 0; i < pointsPerFacility; i++) {
        // Small random offset for visual spread
        const latOffset = (Math.random() - 0.5) * 0.002;
        const lngOffset = (Math.random() - 0.5) * 0.002;
        
        heatData.push([
          parseFloat(facility.latitude) + latOffset,
          parseFloat(facility.longitude) + lngOffset,
          intensity
        ]);
      }
    });
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
  
  // Update count display (now uses barangay predictions)
  await updateCountDisplay(currentCount);
  
  // Update marker intensities with predicted cases
  await updateMarkerIntensities();
  
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
async function updateCountDisplay(count) {
  // Create or update count display element
  let countDisplay = document.getElementById('prediction-count-display');
  const monthContainer = document.getElementById('month-container');
  const mapContainer = document.getElementById('map');
  
  if (!countDisplay) {
    countDisplay = document.createElement('div');
    countDisplay.id = 'prediction-count-display';
    countDisplay.className = 'mt-3 mb-3';
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
  
  // Try to get count from barangay predictions if available
  let totalCount = count;
  if (currentMonth) {
    try {
      const barangayPredictions = await fetchBarangayDiseasePeakPredictions();
      if (barangayPredictions && !barangayPredictions.error) {
        // Get disease code from current disease filter
        let targetDiseaseCode = null;
        for (const [code, filterKey] of Object.entries(diseaseCodeToFilter)) {
          if (filterKey === currentDisease) {
            targetDiseaseCode = code;
            break;
          }
        }
        
        // Extract month number from month name (e.g., "January" -> "1")
        const monthNames = {
          'January': '1', 'February': '2', 'March': '3', 'April': '4',
          'May': '5', 'June': '6', 'July': '7', 'August': '8',
          'September': '9', 'October': '10', 'November': '11', 'December': '12'
        };
        const monthNum = monthNames[currentMonth] || currentMonth.replace(/\D/g, '');
        
        // Sum up predictions from all barangays for this disease and month
        let sum = 0;
        Object.keys(barangayPredictions).forEach(barangay => {
          // Filter out poblacion
          if (barangay.toLowerCase().includes('poblacion')) {
            return;
          }
          
          const months = barangayPredictions[barangay];
          if (months[monthNum] && months[monthNum].all_diseases) {
            const monthData = months[monthNum].all_diseases;
            // Check for disease code (try both normalized and original)
            if (targetDiseaseCode && monthData[targetDiseaseCode] !== undefined) {
              sum += monthData[targetDiseaseCode];
            } else {
              // Try normalized version
              const normalizedCode = normalizeDiseaseCode(targetDiseaseCode);
              if (monthData[normalizedCode] !== undefined) {
                sum += monthData[normalizedCode];
              } else {
                // Try all disease codes to find match
                Object.entries(monthData).forEach(([diseaseCode, diseaseCount]) => {
                  const normalized = normalizeDiseaseCode(diseaseCode);
                  if (normalized === normalizeDiseaseCode(targetDiseaseCode)) {
                    sum += diseaseCount;
                  }
                });
              }
            }
          }
        });
        
        if (sum > 0) {
          totalCount = sum;
        }
      }
    } catch (error) {
      console.error('Error fetching barangay predictions for count display:', error);
    }
  }
  
  // Check if month range is active
  const monthFrom = document.getElementById('month-from');
  const monthTo = document.getElementById('month-to');
  let monthRangeText = '';
  let isMonthRange = false;
  
  if (monthFrom && monthTo && monthFrom.value && monthTo.value) {
    const fromParts = monthFrom.value.split(' ');
    const toParts = monthTo.value.split(' ');
    const fromMonth = fromParts[0];
    const toMonth = toParts[0];
    
    // Get months in range (inline logic since getMonthsInRange is scoped)
    const months = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"];
    const fromIndex = months.indexOf(fromMonth);
    const toIndex = months.indexOf(toMonth);
    
    // Show range summary if months are selected and valid (allow same month)
    if (fromIndex !== -1 && toIndex !== -1 && fromIndex <= toIndex) {
      isMonthRange = true;
      const monthsInRange = months.slice(fromIndex, toIndex + 1);
      try {
        // Try to use fetchMonthRangePredictions if available, otherwise calculate inline
        let aggregatedData = null;
        if (typeof fetchMonthRangePredictions !== 'undefined') {
          aggregatedData = await fetchMonthRangePredictions(monthsInRange);
        } else {
          // Inline calculation if function not accessible
          aggregatedData = { selectedDiseaseTotal: 0 };
          const barangayPredictions = await fetchBarangayDiseasePeakPredictions();
          if (barangayPredictions && !barangayPredictions.error) {
            let targetDiseaseCode = null;
            if (typeof diseaseCodeToFilter !== 'undefined') {
              for (const [code, filterKey] of Object.entries(diseaseCodeToFilter)) {
                if (filterKey === currentDisease) {
                  targetDiseaseCode = code;
                  break;
                }
              }
            }
            const monthNames = {
              'January': '1', 'February': '2', 'March': '3', 'April': '4',
              'May': '5', 'June': '6', 'July': '7', 'August': '8',
              'September': '9', 'October': '10', 'November': '11', 'December': '12'
            };
            for (const month of monthsInRange) {
              const monthNum = monthNames[month];
              Object.keys(barangayPredictions).forEach(barangay => {
                if (barangay.toLowerCase().includes('poblacion')) return;
                const months = barangayPredictions[barangay];
                if (months[monthNum] && months[monthNum].all_diseases) {
                  const monthData = months[monthNum].all_diseases;
                  if (targetDiseaseCode && monthData[targetDiseaseCode] !== undefined) {
                    aggregatedData.selectedDiseaseTotal += monthData[targetDiseaseCode];
                  } else if (targetDiseaseCode && typeof normalizeDiseaseCode !== 'undefined') {
                    const normalizedCode = normalizeDiseaseCode(targetDiseaseCode);
                    if (monthData[normalizedCode] !== undefined) {
                      aggregatedData.selectedDiseaseTotal += monthData[normalizedCode];
                    }
                  }
                }
              });
            }
          }
        }
        
        if (aggregatedData && aggregatedData.selectedDiseaseTotal > 0) {
          monthRangeText = `
            <strong>Total Predicted Cases:</strong> ${aggregatedData.selectedDiseaseTotal.toFixed(0)} cases of ${diseaseName} across the month of ${fromMonth} to ${toMonth} (${currentYear})<br>
          `;
        }
      } catch (error) {
        console.error('Error fetching month range data for display:', error);
      }
    }
  }
  
  // Check if a month range is actually selected by user via dropdowns
  // Only show when BOTH "From Month" AND "To Month" are selected
  const hasMonthFromSelected = monthFrom && monthFrom.value;
  const hasMonthToSelected = monthTo && monthTo.value;
  const hasMonthRangeSelected = hasMonthFromSelected && hasMonthToSelected;
  
  // Only show display if both months are selected (month range)
  if (!hasMonthRangeSelected) {
    countDisplay.style.display = 'none';
    return;
  }
  
  // Update className based on whether month range is active
  if (isMonthRange) {
    // Add alert classes when 2 months are chosen
    countDisplay.className = 'alert alert-info mt-3 mb-3';
  } else {
    // Remove alert classes for single month
    countDisplay.className = 'mt-3 mb-3';
  }
  
  // Format the message as requested
  if (isMonthRange) {
    // When month range is selected, only show the Total Predicted Cases text
    countDisplay.innerHTML = monthRangeText || '';
    countDisplay.style.display = monthRangeText ? 'block' : 'none';
  } else {
    // When single month is selected, show the Prediction Summary
    if (totalCount !== null && totalCount !== undefined && totalCount > 0) {
      // Format count: show 2 decimal places if it's a decimal, otherwise show as integer
      const formattedCount = totalCount % 1 === 0 ? totalCount.toFixed(0) : totalCount.toFixed(2);
      countDisplay.innerHTML = `
        <strong>Prediction Summary:</strong> Predicted "${formattedCount}" cases of ${diseaseName} for ${monthName}<br>
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
}

// Global variable for current year - Default to 2025 since predictions are based on 2023-2024 data
// (currentYear is already declared at the top of the file)

// Disease mapping for display
const diseaseDisplayMap = {
  'open_wounds': 'Open Wounds (T14.1)',
  'dog_bites': 'Dog Bites (W54.99)',
  'acute_respiratory': 'Acute respiratory infections (J06.9)',
  'pneumonia': 'Pneumonia (J15)',
  'hypertension_level_2': 'Hypertension Level 2 (I10-1)'
};

// Function to populate month dropdowns
function populateMonthDropdowns(selectedYear) {
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  
  const monthFrom = document.getElementById('month-from');
  const monthTo = document.getElementById('month-to');
  
  if (monthFrom && monthTo) {
    // Clear existing options except the first one
    monthFrom.innerHTML = '<option value="">Select Month</option>';
    monthTo.innerHTML = '<option value="">Select Month</option>';
    
    months.forEach((month, index) => {
      const monthValue = `${month} ${selectedYear}`;
      const optionFrom = document.createElement('option');
      optionFrom.value = monthValue;
      optionFrom.textContent = monthValue;
      
      const optionTo = document.createElement('option');
      optionTo.value = monthValue;
      optionTo.textContent = monthValue;
      
      monthFrom.appendChild(optionFrom);
      monthTo.appendChild(optionTo);
    });
  }
}

// Function to generate month badges grouped by year
function getCurrentMonth(selectedYear = null) {
  const monthContainer = document.getElementById('month-container-grouped');
  const legacyContainer = document.getElementById('month-container');
  
  // Use selected year or default to current year
  const targetYear = selectedYear || currentYear;
  
  // Removed the early return check - allow function to continue even without containers
  // This ensures populateMonthDropdowns() is always called
  
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  
  // Clear existing month badges (only if containers exist)
  if (monthContainer) monthContainer.innerHTML = '';
  if (legacyContainer) legacyContainer.innerHTML = '';
  
  // Create year group container
  if (monthContainer) {
    const yearGroup = document.createElement('div');
    yearGroup.className = 'year-group mb-3';
    
    const yearHeader = document.createElement('h6');
    yearHeader.className = 'text-muted mb-2';
    yearHeader.textContent = `${targetYear}`;
    yearGroup.appendChild(yearHeader);
    
    const monthBadgesContainer = document.createElement('div');
    monthBadgesContainer.className = 'd-flex flex-wrap gap-2';
    
    for (let i = 0; i < 12; i++) {
      let monthDate = months[i];
      // Store just the month name for API calls (e.g., "January")
      // But display with year (e.g., "January 2026")
      let monthKey = monthDate; // API expects just month name
      let monthDisplay = `${monthDate} ${targetYear}`; // Display format

      let monthBadge = document.createElement("span");
      monthBadge.className = "disease-badge month-badge";
      monthBadge.textContent = monthDisplay;
      monthBadge.dataset.month = monthKey; // Store just month name for API
      monthBadge.dataset.monthDisplay = monthDisplay; // Store display format
      monthBadge.style.cursor = 'pointer';
      
      // Set first month (January) as active by default
      if (i === 0) {
        monthBadge.classList.add('active');
        if (!currentMonth) currentMonth = monthKey; // Use just month name
      }
      
      // Add click event listener
      monthBadge.addEventListener('click', async function() {
        // Remove active class from all month badges
        document.querySelectorAll('.month-badge').forEach(badge => {
          badge.classList.remove('active');
          badge.style.transform = 'scale(1)';
        });
        
        // Add active class to clicked badge
        this.classList.add('active');
        this.style.transform = 'scale(1.05)';
        
        // Update current month (use just month name for API)
        currentMonth = this.dataset.month;
        console.log('Month selected:', currentMonth);
        
        // Update dropdowns with display format
        const monthFrom = document.getElementById('month-from');
        const monthTo = document.getElementById('month-to');
        if (monthFrom) monthFrom.value = this.dataset.monthDisplay;
        if (monthTo) monthTo.value = this.dataset.monthDisplay;
        
        // Update active filters
        updateActiveFilters();
        
        // Update marker intensities when month changes
        await updateMarkerIntensities();
        updateHeatMap();
      });
      
      monthBadgesContainer.appendChild(monthBadge);
    }
    
    yearGroup.appendChild(monthBadgesContainer);
    monthContainer.appendChild(yearGroup);
  }
  
  // Also populate legacy container for backward compatibility
  if (legacyContainer) {
    for (let i = 0; i < 12; i++) {
      let monthDate = months[i];
      let monthKey = monthDate; // API expects just month name

      let monthBadge = document.createElement("span");
      monthBadge.className = "disease-badge month-badge";
      monthBadge.textContent = `${monthDate} ${targetYear}`;
      monthBadge.dataset.month = monthKey;
      
      if (i === 0 && targetYear === 2025) {
        monthBadge.classList.add('active');
        if (!currentMonth) currentMonth = monthKey;
      }
      
      monthBadge.addEventListener('click', async function() {
        document.querySelectorAll('.month-badge').forEach(badge => {
          badge.classList.remove('active');
          badge.style.transform = 'scale(1)';
        });
        this.classList.add('active');
        this.style.transform = 'scale(1.05)';
        currentMonth = this.dataset.month;
        await updateMarkerIntensities();
        updateHeatMap();
      });
      
      legacyContainer.appendChild(monthBadge);
    }
  }
  
  // Populate month dropdowns
  populateMonthDropdowns(targetYear);
}



// Initialize with current month data (will be set by getCurrentMonth)
// updateHeatMap() will be called after getCurrentMonth() in DOMContentLoaded
// plotFacilityMarkers() will be called after map initialization in DOMContentLoaded

function updateActiveFilters() {
  const activeFiltersDiv = document.getElementById('active-filters');
  const activeFiltersText = document.getElementById('active-filters-text');
  
  if (!activeFiltersDiv || !activeFiltersText) return;
  
  const yearFilter = document.getElementById('year-filter');
  const diseaseFilter = document.getElementById('disease-filter');
  
  const filterParts = [];
  
  if (yearFilter && yearFilter.value) {
    filterParts.push(`Year: ${yearFilter.value}`);
  }
  
  if (diseaseFilter && diseaseFilter.value) {
    const diseaseName = diseaseDisplayMap[diseaseFilter.value] || diseaseFilter.value;
    filterParts.push(diseaseName);
  }
  
  // Check if month range is selected (both dropdowns have values)
  const monthFrom = document.getElementById('month-from');
  const monthTo = document.getElementById('month-to');
  const displayYear = yearFilter && yearFilter.value ? yearFilter.value : '2025';
  
  if (monthFrom && monthTo) {
    const fromValue = monthFrom.value;
    const toValue = monthTo.value;
    
    if (fromValue && toValue) {
      // Both months selected - show range format
      const fromParts = fromValue.split(' ');
      const toParts = toValue.split(' ');
      const fromMonth = fromParts[0];
      const toMonth = toParts[0];
      
      // Check if different months (range) or same month
      if (fromMonth !== toMonth) {
        // Different months - show range format: "January to April (2024)"
        filterParts.push(`${fromMonth} to ${toMonth} (${displayYear})`);
      } else {
        // Same month - show single month format: "January (2024)"
        filterParts.push(`${fromMonth} (${displayYear})`);
      }
    } else if (!fromValue && !toValue) {
      // Both dropdowns are empty - show "Select Month"
      filterParts.push('Select Month');
    } else if (fromValue || toValue) {
      // Only one dropdown has value - show that month
      const selectedValue = fromValue || toValue;
      const monthParts = selectedValue.split(' ');
      const selectedMonth = monthParts[0];
      filterParts.push(`${selectedMonth} ${displayYear}`);
    }
  } else if (currentMonth) {
    // Fallback: Only currentMonth is set (from badge or default) - show single month format
    filterParts.push(`${currentMonth} ${displayYear}`);
  }
  
  if (filterParts.length > 0) {
    activeFiltersText.textContent = `Active Filters: ${filterParts.join(' / ')}`;
    activeFiltersDiv.style.display = 'block';
  } else {
    activeFiltersDiv.style.display = 'none';
  }
}

// Function to clear all filters
async function clearAllFilters() {
  const yearFilter = document.getElementById('year-filter');
  const diseaseFilter = document.getElementById('disease-filter');
  const monthFrom = document.getElementById('month-from');
  const monthTo = document.getElementById('month-to');
  
  // Reset year to 2025 (default prediction year)
  if (yearFilter) {
    yearFilter.value = '2025';
  }
  
  // Reset disease to default
  if (diseaseFilter) {
    diseaseFilter.value = 'open_wounds';
  }
  
  // Clear both month dropdowns
  if (monthFrom) {
    monthFrom.value = '';
  }
  if (monthTo) {
    monthTo.value = '';
  }
  
  // Clear current month and disease variables
  currentMonth = '';
  currentDisease = 'open_wounds';
  
  // Clear month badges (remove active state)
  document.querySelectorAll('.month-badge').forEach(badge => {
    badge.classList.remove('active');
    badge.style.transform = 'scale(1)';
  });
  
  // Update legacy disease badges
  document.querySelectorAll('.disease-badge[data-disease]').forEach(badge => {
    badge.classList.remove('active');
    badge.style.transform = 'scale(1)';
    if (badge.dataset.disease === currentDisease) {
      badge.classList.add('active');
      badge.style.transform = 'scale(1.1)';
    }
  });
  
  // Hide month range results
  const resultsContainer = document.getElementById('month-range-results');
  if (resultsContainer) {
    resultsContainer.style.display = 'none';
  }
  
  // Clear heatmap
  if (heat) {
    heat.setLatLngs([]);
  }
  
  // Hide prediction summary
  const countDisplay = document.getElementById('prediction-count-display');
  if (countDisplay) {
    countDisplay.style.display = 'none';
  }
  
  // Update active filters
  updateActiveFilters();
  
  // Refresh markers and heatmap (will clear since no months selected)
  await updateMarkerIntensities();
  updateHeatMap();
  
  console.log('All filters cleared');
}

// Add click handlers for disease filters with enhanced feedback
document.addEventListener('DOMContentLoaded', async function() {
  console.log('DOM Content Loaded - Initializing heatmap...');
  
  // Initialize map first
  initializeMap();
  
  // Fetch barangay predictions ONCE and cache it (reduces API calls from 3 to 1)
  console.log('Fetching barangay predictions (one time)...');
  await fetchBarangayDiseasePeakPredictions();
  
  // Load barangay predictions table (uses cached data)
  await updateBarangayPredictionTable();
  
  // Update summary table using barangay predictions (uses cached data)
  await updatePredictionTable({});
  
  // Also fetch old predictions for raw data table (if needed)
  await fetchAllPredictions().then(() => {
    console.log('All predictions fetched, updating raw data table...');
    updateRawDataTable(rawPredictionsCache);
  });
  
  // Initialize month badges with 2025 (prediction year based on 2023-2024 data)
  getCurrentMonth(2025);
  
  // Ensure currentMonth is set if not already set
  if (!currentMonth) {
    currentMonth = 'January';
  }
  
  // Initialize heat map with current selections (no longer tied to UI)
  updateHeatMap();
  
  // Initialize facility markers, list, and info panel
  plotFacilityMarkers().then(async () => {
    // Optionally auto-select first facility for a better UX
    if (facilityCache.length > 0) {
      updateFacilityInfoPanel(null); // keep empty until user clicks
    }
    // Update marker intensities after markers are plotted
    await updateMarkerIntensities();
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
  
  // New filter handlers
  const yearFilter = document.getElementById('year-filter');
  
  // Initialize currentYear from year filter (defaults to 2025)
  if (yearFilter && yearFilter.value) {
    currentYear = parseInt(yearFilter.value) || 2025;
  }
  
  // Function to handle year input changes
  async function handleYearChange() {
    if (!yearFilter) return;
    
    let inputValue = yearFilter.value.trim();
    
    // Validate year input
    if (!inputValue || isNaN(inputValue)) {
      // If empty or invalid, default to 2025
      yearFilter.value = '2025';
      inputValue = '2025';
    }
    
    const selectedYear = parseInt(inputValue);
    
    // Validate year range
    if (selectedYear < 2020 || selectedYear > 2030) {
      yearFilter.value = '2025';
      currentYear = 2025;
      getCurrentMonth(2025);
      updateActiveFilters();
      updateHeatMap();
      return;
    }
    
    currentYear = selectedYear;
    
    getCurrentMonth(selectedYear);
    updateActiveFilters();
    
    // If year is not 2025, clear the heatmap or show empty state
    if (selectedYear !== 2025) {
      // Clear heatmap data for years without predictions
      if (heat) {
        heat.setLatLngs([]);
      }
      // Hide prediction summary when no data available
      const countDisplay = document.getElementById('prediction-count-display');
      if (countDisplay) {
        countDisplay.style.display = 'none';
      }
      // Hide month range results
      const resultsContainer = document.getElementById('month-range-results');
      if (resultsContainer) {
        resultsContainer.style.display = 'none';
      }
      // Update markers to show no data message
      await updateMarkerIntensities();
      // Also call updateHeatMap to ensure everything is cleared
      await updateHeatMap();
    } else {
      // Normal update for 2025
      await updateMarkerIntensities();
      await updateHeatMap();
    }
  }
  
  if (yearFilter) {
    // Handle input change (when user types and leaves field)
    yearFilter.addEventListener('change', handleYearChange);
    
    // Handle input event for real-time validation (optional)
    yearFilter.addEventListener('input', function() {
      // Optional: You can add real-time validation here if needed
      // For now, we'll just validate on change/blur
    });
    
    // Handle Enter key press
    yearFilter.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleYearChange();
        yearFilter.blur(); // Remove focus after Enter
      }
    });
  }
  
  const diseaseFilter = document.getElementById('disease-filter');
  if (diseaseFilter) {
    diseaseFilter.addEventListener('change', async function() {
      currentDisease = this.value;
      
      // Update legacy badges if they exist
      document.querySelectorAll('.disease-badge[data-disease]').forEach(badge => {
        if (badge.dataset.disease === currentDisease) {
          badge.classList.add('active');
        } else {
          badge.classList.remove('active');
        }
      });
      
      updateActiveFilters();
      await updateMarkerIntensities();
      updateHeatMap();
      
      // If month range is active, refresh the range results with new disease filter
      const monthFrom = document.getElementById('month-from');
      const monthTo = document.getElementById('month-to');
      if (monthFrom && monthTo && monthFrom.value && monthTo.value) {
        await handleMonthRange();
      }
    });
  }
  
  // Function to get month index (0-11)
  function getMonthIndex(monthName) {
    const months = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"];
    return months.indexOf(monthName);
  }
  
  // Function to get all months between from and to
  function getMonthsInRange(fromMonth, toMonth) {
    const months = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"];
    const fromIndex = getMonthIndex(fromMonth);
    const toIndex = getMonthIndex(toMonth);
    
    if (fromIndex === -1 || toIndex === -1) return [];
    if (fromIndex > toIndex) return []; // Invalid range
    
    return months.slice(fromIndex, toIndex + 1);
  }
  
  // Function to fetch and aggregate predictions for a month range
  // Uses the same data source as updateCountDisplay (barangay predictions API)
  async function fetchMonthRangePredictions(months) {
    const aggregatedData = {
      selectedDiseaseTotal: 0,  // Total for currently selected disease only
      allDiseasesTotal: 0,      // Total for all diseases combined
      byMonth: {},
      byBarangay: {}  // Aggregated counts by barangay for heatmap
    };
    
    // Get disease code from current disease filter key (reverse lookup - same as updateCountDisplay)
    let targetDiseaseCode = null;
    if (typeof diseaseCodeToFilter !== 'undefined') {
      for (const [code, filterKey] of Object.entries(diseaseCodeToFilter)) {
        if (filterKey === currentDisease) {
          targetDiseaseCode = code;
          break;
        }
      }
    }
    
    // Use the same API as updateCountDisplay - barangay predictions
    try {
      const barangayPredictions = await fetchBarangayDiseasePeakPredictions();
      
      if (!barangayPredictions || barangayPredictions.error) {
        console.error('Error fetching barangay predictions for month range');
        return aggregatedData;
      }
      
      // Extract month number mapping (same as updateCountDisplay)
      const monthNames = {
        'January': '1', 'February': '2', 'March': '3', 'April': '4',
        'May': '5', 'June': '6', 'July': '7', 'August': '8',
        'September': '9', 'October': '10', 'November': '11', 'December': '12'
      };
      
      // Process each month in the range
      for (const month of months) {
        const monthNum = monthNames[month] || month.replace(/\D/g, '');
        let selectedDiseaseCount = 0;
        let allDiseasesCount = 0;
        
        // Sum up predictions from all barangays for this month (same logic as updateCountDisplay)
        Object.keys(barangayPredictions).forEach(barangay => {
          // Filter out poblacion (same as updateCountDisplay)
          if (barangay.toLowerCase().includes('poblacion')) {
            return;
          }
          
          const months = barangayPredictions[barangay];
          if (months[monthNum] && months[monthNum].all_diseases) {
            const monthData = months[monthNum].all_diseases;
            
            // Calculate total for all diseases in this barangay
            const barangayAllDiseasesTotal = Object.values(monthData).reduce((sum, count) => sum + count, 0);
            allDiseasesCount += barangayAllDiseasesTotal;
            
            // Find count for the currently selected disease (same matching logic as updateCountDisplay)
            let barangaySelectedDiseaseCount = 0;
            if (targetDiseaseCode && monthData[targetDiseaseCode] !== undefined) {
              barangaySelectedDiseaseCount = monthData[targetDiseaseCode];
              selectedDiseaseCount += barangaySelectedDiseaseCount;
            } else {
              // Try normalized version
              const normalizedCode = normalizeDiseaseCode(targetDiseaseCode);
              if (monthData[normalizedCode] !== undefined) {
                barangaySelectedDiseaseCount = monthData[normalizedCode];
                selectedDiseaseCount += barangaySelectedDiseaseCount;
              } else {
                // Try all disease codes to find match (same as updateCountDisplay)
                Object.entries(monthData).forEach(([diseaseCode, diseaseCount]) => {
                  const normalized = normalizeDiseaseCode(diseaseCode);
                  if (normalized === normalizeDiseaseCode(targetDiseaseCode)) {
                    barangaySelectedDiseaseCount += diseaseCount;
                    selectedDiseaseCount += diseaseCount;
                  }
                });
              }
            }
            
            // Store aggregated data by barangay for heatmap
            if (!aggregatedData.byBarangay[barangay]) {
              aggregatedData.byBarangay[barangay] = {
                selectedDisease: 0,
                allDiseases: 0,
                facilityCount: 0
              };
            }
            aggregatedData.byBarangay[barangay].selectedDisease += barangaySelectedDiseaseCount;
            aggregatedData.byBarangay[barangay].allDiseases += barangayAllDiseasesTotal;
          }
        });
        
        // Store month data
        aggregatedData.byMonth[month] = {
          selectedDisease: selectedDiseaseCount,
          allDiseases: allDiseasesCount
        };
        
        aggregatedData.selectedDiseaseTotal += selectedDiseaseCount;
        aggregatedData.allDiseasesTotal += allDiseasesCount;
        
        console.log(`Month ${month}: Selected disease (${currentDisease}): ${selectedDiseaseCount}, All diseases: ${allDiseasesCount}`);
      }
    } catch (error) {
      console.error('Error fetching barangay predictions for month range:', error);
    }
    
    return aggregatedData;
  }
  
  // Function to convert aggregated barangay data to heatmap points
  function convertAggregatedDataToHeatPoints(aggregatedData) {
    if (!aggregatedData || !aggregatedData.byBarangay || !facilityCache || facilityCache.length === 0) {
      return [];
    }
    
    const heatPoints = [];
    const allCounts = Object.values(aggregatedData.byBarangay).map(b => b.selectedDisease);
    
    // Calculate total cases for percentage-based intensity zones
    const totalCases = allCounts.reduce((sum, count) => sum + count, 0);
    
    // Group facilities by barangay
    const facilitiesByBarangay = {};
    facilityCache.forEach(facility => {
      if (facility.barangay) {
        const barangayName = facility.barangay.trim();
        if (!facilitiesByBarangay[barangayName]) {
          facilitiesByBarangay[barangayName] = [];
        }
        facilitiesByBarangay[barangayName].push(facility);
      }
    });
    
    // Create heat points for each barangay
    Object.entries(aggregatedData.byBarangay).forEach(([barangayName, data]) => {
      if (data.selectedDisease <= 0) return;
      
      // Find facilities in this barangay (case-insensitive match)
      const matchingFacilities = [];
      Object.entries(facilitiesByBarangay).forEach(([facilityBarangay, facilities]) => {
        if (facilityBarangay.toLowerCase().includes(barangayName.toLowerCase()) ||
            barangayName.toLowerCase().includes(facilityBarangay.toLowerCase())) {
          matchingFacilities.push(...facilities);
        }
      });
      
      // If no exact match, try to find facilities with similar barangay names
      if (matchingFacilities.length === 0) {
        Object.entries(facilitiesByBarangay).forEach(([facilityBarangay, facilities]) => {
          // Try partial match
          const barangayWords = barangayName.toLowerCase().split(/\s+/);
          const facilityWords = facilityBarangay.toLowerCase().split(/\s+/);
          const hasCommonWord = barangayWords.some(word => 
            word.length > 3 && facilityWords.some(fw => fw.includes(word) || word.includes(fw))
          );
          if (hasCommonWord) {
            matchingFacilities.push(...facilities);
          }
        });
      }
      
      // Update facility count
      data.facilityCount = matchingFacilities.length;
      
      // Calculate average cases per facility for comparison
      const facilityCount = Object.values(facilitiesByBarangay).reduce((sum, facilities) => sum + facilities.length, 0);
      const averageCases = facilityCount > 0 ? totalCases / facilityCount : 0;
      
      // Calculate ratio compared to average
      let ratio = 0;
      if (averageCases > 0) {
        ratio = data.selectedDisease / averageCases;
      } else if (totalCases > 0) {
        // Fallback to percentage if no average
        const percentage = (data.selectedDisease / totalCases) * 100;
        ratio = percentage / 100;
      }
      
      // Only show facilities with ratio > 0.8 in RED, don't display others
      if (ratio <= 0.8 || data.selectedDisease === 0) {
        return; // Skip this barangay - don't add to heatmap
      }
      
      // If ratio > 0.8, show in RED only
      const baseIntensity = 1.0; // Pure red zone
      
      // Create heat points for each facility in this barangay
      if (matchingFacilities.length > 0) {
        matchingFacilities.forEach(facility => {
          if (facility.latitude && facility.longitude) {
            // Create multiple points per facility based on count (1 point per 10 cases)
            const pointsPerFacility = Math.max(1, Math.ceil(data.selectedDisease / 10));
            for (let i = 0; i < pointsPerFacility; i++) {
              // Small random offset for visual spread
              const latOffset = (Math.random() - 0.5) * 0.002;
              const lngOffset = (Math.random() - 0.5) * 0.002;
              
              heatPoints.push({
                lat: parseFloat(facility.latitude) + latOffset,
                lng: parseFloat(facility.longitude) + lngOffset,
                intensity: baseIntensity,
                count: data.selectedDisease,
                facilityCount: matchingFacilities.length,
                barangay: barangayName
              });
            }
          }
        });
      } else {
        // If no facilities found, create a point at a default location or skip
        // For now, we'll skip barangays without facilities
        console.warn(`No facilities found for barangay: ${barangayName}`);
      }
    });
    
    return heatPoints;
  }
  
  // Function to display month range results
  function displayMonthRangeResults(aggregatedData, months) {
    const resultsContainer = document.getElementById('month-range-results');
    if (!resultsContainer) return;
    
    if (months.length === 0 || aggregatedData.totalCases === 0) {
      resultsContainer.style.display = 'none';
      return;
    }
    
    resultsContainer.style.display = 'block';
    
   
    let html = `
      
    `;
    
    // Display each month's data
    for (const month of months) {
      const monthData = aggregatedData.byMonth[month] || {};
      // Get count for the currently selected disease and all diseases
      const diseaseCount = monthData.selectedDisease || 0;
      const monthTotal = monthData.allDiseases || 0;
      
      html += `
        <tr>
          <td><strong>${month}</strong></td>
          <td>${diseaseCount.toFixed(0)}</td>
          <td>${monthTotal.toFixed(0)}</td>
        </tr>
      `;
    }
    
    // Add total row - use aggregated totals
    html += `
              </tbody>
              <tfoot class="table-secondary">
                <tr>
                  <td><strong>Total</strong></td>
                  <td><strong>${aggregatedData.selectedDiseaseTotal.toFixed(0)}</strong></td>
                  <td><strong>${aggregatedData.allDiseasesTotal.toFixed(0)}</strong></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>
    `;
    
    resultsContainer.innerHTML = html;
  }
  
  // Function to handle month range selection
  async function handleMonthRange() {
    // Check if year is 2025 - if not, clear everything and return
    if (currentYear !== 2025) {
      // Clear heatmap
      if (heat) {
        heat.setLatLngs([]);
      }
      // Hide prediction summary
      const countDisplay = document.getElementById('prediction-count-display');
      if (countDisplay) {
        countDisplay.style.display = 'none';
      }
      // Hide month range results
      const resultsContainer = document.getElementById('month-range-results');
      if (resultsContainer) {
        resultsContainer.style.display = 'none';
      }
      // Update markers to show no data
      await updateMarkerIntensities();
      return;
    }
    
    const monthFrom = document.getElementById('month-from');
    const monthTo = document.getElementById('month-to');
    
    if (!monthFrom || !monthTo) return;
    
    const fromValue = monthFrom.value;
    const toValue = monthTo.value;
    
    // If both are selected, process range
    if (fromValue && toValue) {
      const fromParts = fromValue.split(' ');
      const toParts = toValue.split(' ');
      const fromMonth = fromParts[0];
      const toMonth = toParts[0];
      
      const monthsInRange = getMonthsInRange(fromMonth, toMonth);
      
      if (monthsInRange.length === 0) {
        alert('Invalid month range. Please ensure "From Month" comes before "To Month".');
        return;
      }
      
      // Treat both single month and multiple months as month range when both dropdowns are selected
      // Multiple months (or same month) - fetch and aggregate
      console.log(`Fetching predictions for month range: ${monthsInRange.join(', ')}`);
      
      // Show loading indicator
      const resultsContainer = document.getElementById('month-range-results');
      if (resultsContainer) {
        resultsContainer.style.display = 'block';
        resultsContainer.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Loading predictions...</p></div>';
      }
      
      const aggregatedData = await fetchMonthRangePredictions(monthsInRange);
      displayMonthRangeResults(aggregatedData, monthsInRange);
      
      // Update month badges to show range
      document.querySelectorAll('.month-badge').forEach(badge => {
        badge.classList.remove('active');
        badge.style.transform = 'scale(1)';
        if (monthsInRange.includes(badge.dataset.month)) {
          badge.classList.add('active');
          badge.style.transform = 'scale(1.05)';
        }
      });
      
      // Convert aggregated data to heatmap points and display on map
      if (heat && aggregatedData && aggregatedData.byBarangay) {
        const heatPoints = convertAggregatedDataToHeatPoints(aggregatedData);
        const heatData = heatPoints.map(point => [point.lat, point.lng, point.intensity]);
        
        // Fade out current heat
        heat.setOptions({ opacity: 0 });
        
        // Update data and fade in
        setTimeout(() => {
          heat.setLatLngs(heatData);
          heat.setOptions({ opacity: 1 });
          console.log(`Heatmap updated with ${heatPoints.length} points from ${Object.keys(aggregatedData.byBarangay).length} barangays`);
        }, 300);
      }
      
      // Update count display to show month range summary
      await updateCountDisplay(null);
      
      // Update marker intensities with aggregated values across month range
      await updateMarkerIntensities();
      
      updateActiveFilters();
    } else if (fromValue || toValue) {
      // Only one selected, use single month logic
      // Check year first - if not 2025, clear and return
      if (currentYear !== 2025) {
        // Clear heatmap
        if (heat) {
          heat.setLatLngs([]);
        }
        // Hide prediction summary
        const countDisplay = document.getElementById('prediction-count-display');
        if (countDisplay) {
          countDisplay.style.display = 'none';
        }
        // Hide range results
        const resultsContainer = document.getElementById('month-range-results');
        if (resultsContainer) resultsContainer.style.display = 'none';
        // Update markers to show no data
        await updateMarkerIntensities();
        return;
      }
      
      const selectedValue = fromValue || toValue;
      const monthParts = selectedValue.split(' ');
      const monthName = monthParts[0];
      currentMonth = monthName;
      
      // Update month badges
      document.querySelectorAll('.month-badge').forEach(badge => {
        badge.classList.remove('active');
        badge.style.transform = 'scale(1)';
        if (badge.dataset.month === currentMonth) {
          badge.classList.add('active');
          badge.style.transform = 'scale(1.05)';
        }
      });
      
      // Hide range results
      const resultsContainer = document.getElementById('month-range-results');
      if (resultsContainer) resultsContainer.style.display = 'none';
      
      updateActiveFilters();
      await updateMarkerIntensities();
      updateHeatMap();
    } else {
      // Both empty - clear currentMonth and clear heatmap
      currentMonth = '';
      // Hide range results
      const resultsContainer = document.getElementById('month-range-results');
      if (resultsContainer) resultsContainer.style.display = 'none';
      // Clear heatmap since no months are selected
      updateActiveFilters();
      await updateMarkerIntensities();
      updateHeatMap();
    }
  }
  
  const monthFrom = document.getElementById('month-from');
  const monthTo = document.getElementById('month-to');
  
  if (monthFrom) {
    monthFrom.addEventListener('change', handleMonthRange);
  }
  
  if (monthTo) {
    monthTo.addEventListener('change', handleMonthRange);
  }
  
  // Quick filter buttons
  const filterCurrentYear = document.getElementById('filter-current-year');
  if (filterCurrentYear) {
    filterCurrentYear.addEventListener('click', function() {
      if (yearFilter) {
        yearFilter.value = '2025'; // Set to 2025 (prediction year)
        // Trigger change event to update everything
        yearFilter.dispatchEvent(new Event('change'));
      }
    });
  }
  
  const filterClear = document.getElementById('filter-clear');
  if (filterClear) {
    filterClear.addEventListener('click', clearAllFilters);
  }
  
  // Add click handlers for disease filter badges (legacy support)
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
      
      // Update dropdown if it exists
      if (diseaseFilter) {
        diseaseFilter.value = currentDisease;
      }
      
      // Update marker intensities when disease changes
      updateMarkerIntensities();
      updateActiveFilters();
      console.log('Disease selected:', currentDisease);
      updateHeatMap();
    });
  });
  
  // Initialize active filters display
  updateActiveFilters();
}); 