// Global variables
let currentDate = new Date();
let medicalFollowups = {};
let appointments = [];
let referrals = [];
let reminders = [];
let currentUserId = null;
let isAdmin = false;
let timelineFollowups = [];
// Helper to build a YYYY-MM-DD key using local time (avoids UTC shift issues)
function getLocalDateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
let scheduleToday = {};



// Initialize calendar
document.addEventListener("DOMContentLoaded", function () {
  // Set user context if available

  if (typeof window.currentUserId !== "undefined") {
    currentUserId = window.currentUserId;
  }
  if (typeof window.isAdmin !== "undefined") {
    isAdmin = window.isAdmin;
  }

  renderCalendar(); // Draw the calendar
  fetchMedicalFollowups(); // Get medical follow-ups for current month
  // Also render schedule after a short delay to ensure data is loaded
  setTimeout(() => {
    if (Object.keys(medicalFollowups).length > 0) {
      renderSchedule();
    }
  }, 1000);
});


// Function to fetch medical history follow-up dates
async function fetchMedicalFollowups() {
  try {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1; // JavaScript months are 0-indexed
    
    // Fetch medical follow-ups (filtering is handled on the backend)
    const response = await fetch(`/patients/api/medical-history-followups/?year=${year}&month=${month}`, {
      method: 'GET',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCookie('csrftoken')
      },
      credentials: 'same-origin'
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch medical follow-ups');
    }
    
    const data = await response.json();
    if (data.success) {
      medicalFollowups = data.followups;

      console.log("Medical Follow-ups:", medicalFollowups);
      renderCalendar(); // Re-render calendar to show follow-ups
      renderSchedule(); // Render today's schedule
    }
  } catch (error) {
    console.error('Error fetching medical follow-ups:', error);
  }
  }
  
// Function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Function to filter appointappointments by current user
function filterAppointmentsByUser(appointments) {
  if (!currentUserId || isAdmin) return appointments;

  return appointments.filter(appointment => {
    // Check if appointment has user_id field or if it's associated with current user's patients
    return appointment.user_id === currentUserId || 
           appointment.patient_user_id === currentUserId ||
           !appointment.user_id; // Include appointments without user_id for backward compatibility
  });
}

// Function to filter referrals by current user
function filterReferralsByUser(referrals) {
  if (!currentUserId) return referrals;
  
  // Filter referrals that belong to current user
  return referrals.filter(referral => {
    return referral.user_id === currentUserId || 
           referral.patient_user_id === currentUserId ||
           !referral.user_id; // Include referrals without user_id for backward compatibility
  });
}

// Calendar functions
function renderCalendar() {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startDate = new Date(firstDay);
  startDate.setDate(startDate.getDate() - firstDay.getDay());

  const endDate = new Date(lastDay);
  endDate.setDate(endDate.getDate() + (6 - lastDay.getDay()));

  document.getElementById(
    "currentMonth"
  ).textContent = `${firstDay.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  })}`;

  const calendarGrid = document.getElementById("calendarGrid");
  calendarGrid.innerHTML = "";

  // Add weekdays header
  const weekdaysContainer = document.createElement("div");
  weekdaysContainer.className = "calendar-weekdays";
  
  const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  daysOfWeek.forEach((day) => {
    const dayHeader = document.createElement("div");
    dayHeader.className = "calendar-weekday";
    dayHeader.textContent = day;
    weekdaysContainer.appendChild(dayHeader);
  });
  calendarGrid.appendChild(weekdaysContainer);

  // Add calendar days container
  const daysContainer = document.createElement("div");
  daysContainer.className = "calendar-days";

  // Add calendar days
  const current = new Date(startDate);
  while (current <= endDate) {
    const dayElement = document.createElement("div");
    dayElement.className = "calendar-day";

    if (current.getMonth() !== month) {
      dayElement.classList.add("other-month");
    }

    if (isToday(current)) {
      dayElement.classList.add("today");
    }

    // Add day number
    const dayNumber = document.createElement("span");
    dayNumber.textContent = current.getDate();
    dayElement.appendChild(dayNumber);
    
    // Add medical follow-up indicators (already filtered by user in fetchMedicalFollowups)
    const dateKey = getLocalDateKey(current);
    if (medicalFollowups[dateKey]) {
      const followupContainer = document.createElement("div");
      followupContainer.className = "followup-indicators";
      
      medicalFollowups[dateKey].forEach((followup, index) => {
        const indicator = document.createElement("div");
        indicator.className = "followup-indicator";
        indicator.title = `Follow-up: ${followup.patient_name} - ${followup.illness_name}`;
        indicator.innerHTML = `<i class="bi bi-calendar-check"></i>`;
        indicator.onclick = (e) => {
          e.stopPropagation(); // Prevent calendar day click
          showFollowupDetails(followup, current);
        };
        followupContainer.appendChild(indicator);
      });
      
      dayElement.appendChild(followupContainer);
    }
    
    dayElement.onclick = () => openAppointmentModal(current);
    daysContainer.appendChild(dayElement);
    current.setDate(current.getDate() + 1);
  }
  
  calendarGrid.appendChild(daysContainer);
}

function isToday(date) {
  const today = new Date();
  return date.toDateString() === today.toDateString();
}

// Function to show follow-up details
function showFollowupDetails(followup, date) {
  const modal = document.createElement('div');
  modal.className = 'modal fade';
  modal.id = 'followupModal';
  modal.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="bi bi-calendar-check text-success"></i>
            Medical Follow-up
          </h5>
          <button type="button" class="btn-close" data-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-md-6">
              <strong>Patient:</strong><br>
              <span class="text-primary">${followup.patient_name}</span>
            </div>
            <div class="col-md-6">
              <strong>Reason:</strong><br>
              <span class="text-success">${followup.notes}</span>
            </div>
          </div>
          <hr>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" onclick="viewPatientDetails(${followup.patient_id})">
            <i class="bi bi-person"></i> View Patient Details
          </button>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Initialize Bootstrap modal
  const bootstrapModal = new bootstrap.Modal(modal);
  bootstrapModal.show();
  
  // Remove modal from DOM after it's hidden
  modal.addEventListener('hidden.bs.modal', function() {
    document.body.removeChild(modal);
  });
}

// Function to view patient details (placeholder - you can implement this based on your needs)
function viewPatientDetails(patientId) {
  // You can implement this to redirect to patient details page
  // or open a modal with patient information
  console.log('Viewing patient details for ID:', patientId);
  // Example: window.location.href = `/patients/patient/${patientId}/`;
}



function previousMonth() {
  currentDate.setMonth(currentDate.getMonth() - 1);
  renderCalendar();
  fetchMedicalFollowups(); // Fetch follow-ups for new month
}

function nextMonth() {
  currentDate.setMonth(currentDate.getMonth() + 1);
  renderCalendar();
  fetchMedicalFollowups(); // Fetch follow-ups for new month
}

function goToToday() {
  currentDate = new Date();
  renderCalendar();
  fetchMedicalFollowups(); // Fetch follow-ups for current month
  }

function renderSchedule() {
  const today = new Date();
  let dateKey = getLocalDateKey(today);
  const scheduleContent = document.getElementById('scheduleContent');
  
  scheduleContent.innerHTML = '';
  
  // Fallback for backends that return unpadded keys like YYYY-M-D
  if (!medicalFollowups[dateKey]) {
    const altKey = `${today.getFullYear()}-${today.getMonth() + 1}-${today.getDate()}`;
    if (medicalFollowups[altKey]) {
      dateKey = altKey;
    }
  }

  if (medicalFollowups[dateKey] && medicalFollowups[dateKey].length > 0) {
    console.log('Found followups for today:', medicalFollowups[dateKey].length);
    const scheduleContainer = document.createElement("div");
    scheduleContainer.className = "list-group";
    
    medicalFollowups[dateKey].forEach((followup, index) => {
      const schedule = document.createElement("div");
      schedule.className = "list-group-item d-flex align-items-start";
      schedule.innerHTML = `
        <div class="me-3 text-success"><i class="bi bi-calendar-check"></i></div>
        <div>
          <div class="fw-bold">${followup.patient_name}</div>
          <div class="text-muted">${followup.notes || ''}</div>
        </div>
      `;
      schedule.onclick = () => showFollowupDetails(followup, today);
      scheduleContainer.appendChild(schedule);
    });
    
    scheduleContent.appendChild(scheduleContainer);
  } else {
    console.log('No followups found for today');
    scheduleContent.innerHTML = '<div class="text-muted">No schedules for today.</div>';
  }
}                


