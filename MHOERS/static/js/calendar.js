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
      
      const followups = medicalFollowups[dateKey];
      const maxDisplay = 5;
      const displayFollowups = followups.slice(0, maxDisplay);
      
      displayFollowups.forEach((followup, index) => {
        const indicator = document.createElement("div");
        indicator.className = "followup-indicator";
        indicator.title = `Follow-up: ${followup.patient_name} - ${followup.illness_name}`;
        // Display advice text instead of icon, truncate if too long
        const adviceText = followup.advice ? followup.advice.substring(0, 30) + (followup.advice.length > 30 ? '...' : '') : 'Follow-up';
        indicator.innerHTML = `<span class="followup-text">${adviceText}</span>`;
        indicator.onclick = (e) => {
          e.stopPropagation(); // Prevent calendar day click
          showFollowupDetails(followup, current);
        };
        followupContainer.appendChild(indicator);
      });
      
      // Add "more..." option if there are more than 5 events
      if (followups.length > maxDisplay) {
        const moreIndicator = document.createElement("div");
        moreIndicator.className = "followup-indicator more-events";
        moreIndicator.innerHTML = `<span class="followup-text text-primary">+${followups.length - maxDisplay} more...</span>`;
        moreIndicator.onclick = (e) => {
          e.stopPropagation(); // Prevent calendar day click
          showAllEventsModal(followups, current);
        };
        followupContainer.appendChild(moreIndicator);
      }
      
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

// Function to show all events modal
function showAllEventsModal(followups, date) {
  const modal = document.createElement('div');
  modal.className = 'modal fade';
  modal.id = 'allEventsModal';
  modal.innerHTML = `
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="bi bi-calendar-event text-primary"></i>
            All Events for ${date.toLocaleDateString()}
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="list-group">
            ${followups.map((followup, index) => `
              <div class="list-group-item list-group-item-action" onclick="showFollowupDetailsFromModal(${JSON.stringify(followup).replace(/"/g, '&quot;')}, '${date.toISOString()}')">
                <div class="d-flex w-100 justify-content-between align-items-center">
                  <h6 class="mb-0 text-primary">${followup.advice || 'Follow-up'}</h6>
                  <small class="text-muted">${new Date(followup.followup_date).toLocaleDateString()}</small>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
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

// Function to show follow-up details from the all events modal
function showFollowupDetailsFromModal(followup, dateString) {
  const date = new Date(dateString);
  showFollowupDetails(followup, date);
}

// Function to show follow-up details
function showFollowupDetails(followup, date) {
  console.log('showFollowupDetails called with patient_id:', followup.patient_id);
  
  // Remove existing modal if any to prevent duplicates
  const existingModal = document.getElementById('followupModal');
  if (existingModal) {
    // Try to get Bootstrap modal instance and hide it first
    const bootstrapModalInstance = bootstrap.Modal.getInstance(existingModal);
    if (bootstrapModalInstance) {
      bootstrapModalInstance.hide();
      // Wait for modal to be hidden before removing and creating new one
      existingModal.addEventListener('hidden.bs.modal', function cleanup() {
        if (existingModal && existingModal.parentNode) {
          existingModal.parentNode.removeChild(existingModal);
        }
        existingModal.removeEventListener('hidden.bs.modal', cleanup);
        // Now create the new modal
        createFollowupDetailsModal(followup, date);
      }, { once: true });
      return; // Exit early, new modal will be created after cleanup
    } else {
      // No Bootstrap instance, just remove it
      if (existingModal.parentNode) {
        existingModal.parentNode.removeChild(existingModal);
      }
    }
  }
  
  // Create the modal
  createFollowupDetailsModal(followup, date);
}

// Helper function to create the follow-up details modal
function createFollowupDetailsModal(followup, date) {
  // Use status from followup object if provided, otherwise calculate it
  let status = followup.status;
  
  // Normalize status: trim whitespace and convert to lowercase for comparison
  if (status) {
    status = String(status).trim().toLowerCase();
  }
  
  if (!status) {
    // Calculate follow-up status if not provided
    // Parse followup_date string (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss)
    const followupDateStr = followup.followup_date;
    
    // Extract date part only (YYYY-MM-DD) to avoid timezone issues
    let datePart = followupDateStr;
    if (datePart.includes('T')) {
      datePart = datePart.split('T')[0];
    }
    
    // Parse date components directly to avoid timezone issues
    const [year, month, day] = datePart.split('-').map(Number);
    const followupDateOnly = new Date(year, month - 1, day);
    
    // Get today's date (local time, no time component)
    const today = new Date();
    const todayDateOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    
    // Compare dates
    const followupTime = followupDateOnly.getTime();
    const todayTime = todayDateOnly.getTime();
    
    if (followupTime < todayTime) {
      status = 'overdue';
    } else if (followupTime === todayTime) {
      status = 'today';
    } else {
      status = 'upcoming';
    }
  }
  
  // Hide buttons if status is completed (case-insensitive check)
  const isCompleted = status === 'completed';
  
  // Debug logging
  console.log('Follow-up status:', status, 'isCompleted:', isCompleted, 'followup_date:', followup.followup_date, 'showSmsButton:', !isCompleted);
  
  // Check if user is a doctor (doctors cannot see Record Follow-up Visit button)
  const isDoctor = typeof window.isDoctor !== 'undefined' && window.isDoctor === true;
  
  // Only show Record button if status is overdue or today (and not completed) AND user is not a doctor
  const showRecordButton = !isCompleted && (status === 'overdue' || status === 'today') && !isDoctor;
  // Show Send SMS button for ALL follow-ups (today, overdue, and future) - only hide if completed
  const showSmsButton = !isCompleted;
  
  const modal = document.createElement('div');
  modal.className = 'modal fade';
  modal.id = 'followupModal';
  modal.tabIndex = -1;              // ✅ required for proper focus
  modal.setAttribute("role", "dialog"); // ✅ accessibility + fixes clicks

  modal.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="bi bi-calendar-check text-success"></i>
            ${followup.advice}
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <style>
            #followupModal .modal-body .text-dark {
              color: #212529 !important;
            }
            #followupModal .modal-body .text-primary {
              color: #0d6efd !important;
            }
          </style>
          <div class="mb-2">
            <strong>Name of the patient:</strong><br>
            <span class="text-primary" style="color: #0d6efd !important;">${followup.patient_name}</span>
          </div>
          <div class="mb-2">
            <strong>Date as the follow up:</strong><br>
            <span style="color: #212529 !important;">${new Date(followup.followup_date).toLocaleDateString()}</span>
          </div>
          <div class="mb-2">
            <strong>Reason:</strong><br>
            <span style="color: #212529 !important;">${followup.notes}</span>
          </div>
          <div class="mb-2">
            <strong>Illness:</strong><br>
            <span style="color: #212529 !important;">${followup.illness_name}</span>
          </div>
          <hr>
          <div class="mb-2">
            <strong>Advice:</strong><br>
            <span style="color: #212529 !important;">${followup.advice}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          ${showSmsButton ? `
          <button 
            type="button" 
            class="btn btn-info send-sms-reminder" 
            data-patient-id="${followup.patient_id}"
            title="Send SMS reminder to patient">
            <i class="bi bi-send"></i> Send SMS
          </button>
          ` : ''}
          ${showRecordButton ? `
          <button 
            type="button" 
            class="btn btn-success add-consultation-form" 
            data-patient-id="${followup.patient_id}"
            title="New Consultation Form">
            <i class="bi bi-file-earmark-medical"></i> New Consultation Form
          </button>
          ` : ''}
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  const bootstrapModal = new bootstrap.Modal(modal, {
    backdrop: 'static',
    keyboard: false
  });
  bootstrapModal.show();
  
  // Debug: Verify SMS button exists (only if status is today)
  if (showSmsButton) {
    setTimeout(() => {
      const smsButton = modal.querySelector('.send-sms-reminder');
      if (smsButton) {
        console.log('✓ SMS button found in modal');
      } else {
        console.error('✗ SMS button NOT found in modal!');
      }
    }, 100);
  }

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

// Function to show follow-up visit form modal
function showFollowupVisitForm(patientId, medicalHistoryId, followupDate, illnessName) {
  // Remove existing modal if any
  const existingModal = document.getElementById('followupVisitFormModal');
  if (existingModal) {
    existingModal.remove();
  }
  
  const modal = document.createElement('div');
  modal.className = 'modal fade';
  modal.id = 'followupVisitFormModal';
  modal.tabIndex = -1;
  modal.setAttribute("role", "dialog");
  
  const formattedDate = new Date(followupDate).toLocaleDateString();
  
  modal.innerHTML = `
    <div class="modal-dialog modal-lg" style="max-height: 90vh; margin: 1.75rem auto;">
      <div class="modal-content" style="max-height: 90vh; display: flex; flex-direction: column;">
        <div class="modal-header bg-success text-white" style="flex-shrink: 0;">
          <h5 class="modal-title">
            <i class="bi bi-clipboard-check"></i> Record Follow-up Visit
          </h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form id="followupVisitForm" style="display: flex; flex-direction: column; flex: 1; min-height: 0;">
          <div class="modal-body" style="overflow-y: auto; flex: 1; min-height: 0;">
            <input type="hidden" name="patient_id" value="${patientId}">
            <input type="hidden" name="medical_history_id" value="${medicalHistoryId}">
            
            <div class="alert alert-info">
              <strong>Follow-up Date:</strong> ${formattedDate}<br>
              <strong>Illness:</strong> ${illnessName || 'N/A'}
            </div>
            
            <h6 class="mb-3">Vital Signs</h6>
            <div class="row">
              <div class="col-md-4 mb-3">
                <label class="form-label">Weight (kg) <span class="text-danger">*</span></label>
                <input type="number" class="form-control" name="weight" step="0.01" required>
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">Height (cm) <span class="text-danger">*</span></label>
                <input type="number" class="form-control" name="height" step="0.01" required>
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">Temperature (°C) <span class="text-danger">*</span></label>
                <input type="number" class="form-control" name="temperature" step="0.1" required>
              </div>
              <div class="col-md-3 mb-3">
                <label class="form-label">BP Systolic <span class="text-danger">*</span></label>
                <input type="number" class="form-control" name="bp_systolic" required>
              </div>
              <div class="col-md-3 mb-3">
                <label class="form-label">BP Diastolic <span class="text-danger">*</span></label>
                <input type="number" class="form-control" name="bp_diastolic" required>
              </div>
              <div class="col-md-3 mb-3">
                <label class="form-label">Pulse Rate <span class="text-danger">*</span></label>
                <input type="number" class="form-control" name="pulse_rate" required>
              </div>
              <div class="col-md-3 mb-3">
                <label class="form-label">Respiratory Rate <span class="text-danger">*</span></label>
                <input type="number" class="form-control" name="respiratory_rate" required>
              </div>
              <div class="col-md-3 mb-3">
                <label class="form-label">Oxygen Saturation (%) <span class="text-danger">*</span></label>
                <input type="number" class="form-control" name="oxygen_saturation" required>
              </div>
            </div>
            
            <hr>
            <h6 class="mb-3">Visit Information</h6>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Visit Date <span class="text-danger">*</span></label>
                <input type="date" class="form-control" name="visit_date" value="${followupDate.split('T')[0]}" required>
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Status <span class="text-danger">*</span></label>
                <select class="form-control" name="status" required>
                  <option value="completed">Completed</option>
                  <option value="no_show">No Show</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Current Symptoms</label>
              <textarea class="form-control" name="current_symptoms" rows="3" placeholder="Describe current symptoms..."></textarea>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Treatment Response</label>
              <textarea class="form-control" name="treatment_response" rows="3" placeholder="How did the patient respond to treatment?"></textarea>
            </div>
            
            <div class="mb-3">
              <label class="form-label">New Medications</label>
              <textarea class="form-control" name="new_medications" rows="2" placeholder="Any new medications prescribed..."></textarea>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Visit Notes</label>
              <textarea class="form-control" name="visit_notes" rows="3" placeholder="Additional notes about the visit..."></textarea>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Next Follow-up Date (if needed)</label>
              <input type="date" class="form-control" name="next_followup_date">
            </div>
          </div>
          <div class="modal-footer bg-light" style="border-top: 1px solid #dee2e6; padding: 1rem; flex-shrink: 0;">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="bi bi-x-circle"></i> Cancel
            </button>
            <button type="submit" class="btn btn-success" id="saveFollowupVisitBtn">
              <i class="bi bi-save"></i> Save Follow-up Visit
            </button>
          </div>
        </form>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  const bootstrapModal = new bootstrap.Modal(modal, {
    backdrop: 'static',
    keyboard: false
  });
  bootstrapModal.show();
  
  // Handle form submission
  const form = modal.querySelector('#followupVisitForm');
  if (!form) {
    console.error('Follow-up visit form not found!');
    return;
  }
  
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Find submit button by ID first, then by type
    let submitButton = document.getElementById('saveFollowupVisitBtn');
    if (!submitButton) {
      submitButton = form.querySelector('button[type="submit"]');
    }
    
    if (!submitButton) {
      alert('Error: Submit button not found. Please refresh and try again.');
      return;
    }
    
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';
    
    const formData = new FormData(form);
    
    fetch('/patients/api/record-followup-visit/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        submitButton.innerHTML = '<i class="bi bi-check-circle"></i> Saved!';
        submitButton.classList.remove('btn-success');
        submitButton.classList.add('btn-primary');
        
        setTimeout(() => {
          bootstrapModal.hide();
          modal.remove();
          // Refresh calendar to update follow-ups
          fetchMedicalFollowups();
          // Show success modal instead of alert
          showSuccessModal('Follow-up visit recorded successfully!', 'The follow-up visit has been saved to the patient\'s medical history.');
        }, 1000);
      } else {
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
        showErrorModal('Error', data.error || 'Failed to save follow-up visit');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      submitButton.disabled = false;
      submitButton.innerHTML = originalText;
      showErrorModal('Error', 'Error saving follow-up visit. Please try again.');
    });
  });
  
  modal.addEventListener('hidden.bs.modal', function() {
    document.body.removeChild(modal);
  });
}

// Redirect handler for modal button
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("go-to-assessment")) {
    e.preventDefault();
    e.stopPropagation();
    
    const patientId = e.target.getAttribute("data-patient-id");
    const medicalHistoryId = e.target.getAttribute("data-medical-history-id");
    const isFollowup = e.target.getAttribute("data-is-followup") === "true";
    console.log('New Assessment clicked for patient ID:', patientId, 'isFollowup:', isFollowup);

    // Check if the form exists
    const form = document.getElementById("goToAssessmentForm");
    const hiddenInput = document.getElementById("hiddenPatientId");
    const hiddenMedicalHistoryInput = document.getElementById("hiddenMedicalHistoryId");
    const hiddenIsFollowupInput = document.getElementById("hiddenIsFollowup");
    
    if (form && hiddenInput) {
      // Fill hidden input with patient_id
      hiddenInput.value = patientId;
      
      // If it's a follow-up referral, add medical history ID
      if (isFollowup && medicalHistoryId && hiddenMedicalHistoryInput) {
        hiddenMedicalHistoryInput.value = medicalHistoryId;
      }
      if (isFollowup && hiddenIsFollowupInput) {
        hiddenIsFollowupInput.value = "true";
      }
      
      // Submit the hidden form
      form.submit();
    } else {
      console.error('Assessment form or hidden input not found');
      alert('Error: Assessment form not found. Please refresh the page and try again.');
    }
  }
  
  // Handler for "Add New Consultation Form" button (for today's follow-ups)
  if (e.target.closest(".add-consultation-form")) {
    e.preventDefault();
    e.stopPropagation();
    
    const button = e.target.closest(".add-consultation-form");
    const patientId = button.getAttribute("data-patient-id");
    
    console.log('Add New Consultation Form clicked for patient ID:', patientId);
    
    // Redirect to assessment page with patient_id
    window.location.href = `/referral/assessment/?patient_id=${patientId}`;
  }
  
  // Handler for "Record Follow-up Visit" button (for overdue follow-ups)
  if (e.target.closest(".record-followup-visit")) {
    e.preventDefault();
    e.stopPropagation();
    
    const button = e.target.closest(".record-followup-visit");
    const patientId = button.getAttribute("data-patient-id");
    const medicalHistoryId = button.getAttribute("data-medical-history-id");
    const followupDate = button.getAttribute("data-followup-date");
    const illnessName = button.getAttribute("data-illness-name");
    
    console.log('Record Follow-up Visit clicked', { patientId, medicalHistoryId, followupDate, illnessName });
    
    // Open the follow-up visit form modal
    showFollowupVisitForm(patientId, medicalHistoryId, followupDate, illnessName);
  }
});

// SMS reminder button handler
document.addEventListener("click", function (e) {
  if (e.target.closest(".send-sms-reminder")) {
    e.preventDefault();
    e.stopPropagation();
    
    const button = e.target.closest(".send-sms-reminder");
    const patientId = button.getAttribute("data-patient-id");
    const originalText = button.innerHTML;
    
    // Disable button and show loading
    button.disabled = true;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> Sending...';
    
    // Send SMS request with manual=true to allow sending for any follow-up date
    fetch(`/patients/api/send-today-checkup-sms/${patientId}/?manual=true`, {
      method: 'GET',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
      if (data.ok) {
        button.innerHTML = '<i class="bi bi-check-circle"></i> Sent!';
        button.classList.remove('btn-info');
        button.classList.add('btn-success');
        
        // Show success message
        showSMSNotification('SMS reminder sent successfully!', 'success');
        
        // Reset button after 3 seconds
        setTimeout(() => {
          button.disabled = false;
          button.innerHTML = originalText;
          button.classList.remove('btn-success');
          button.classList.add('btn-info');
        }, 3000);
      } else {
        button.innerHTML = '<i class="bi bi-x-circle"></i> Failed';
        button.classList.remove('btn-info');
        button.classList.add('btn-danger');
        showSMSNotification(data.error || 'Failed to send SMS', 'error');
        
        // Reset button after 3 seconds
        setTimeout(() => {
          button.disabled = false;
          button.innerHTML = originalText;
          button.classList.remove('btn-danger');
          button.classList.add('btn-info');
        }, 3000);
      }
    })
    .catch(error => {
      console.error('Error sending SMS:', error);
      button.innerHTML = originalText;
      button.disabled = false;
      showSMSNotification('Error sending SMS. Please try again.', 'error');
    });
  }
});

// Helper function to show SMS notifications
function showSMSNotification(message, type) {
  // Try to use Bootstrap toast if available, otherwise use alert
  const toastContainer = document.getElementById('toast-container');
  if (toastContainer) {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    toast.addEventListener('hidden.bs.toast', () => {
      toastContainer.removeChild(toast);
    });
  } else {
    // Fallback to alert
    if (type === 'success') {
      alert('✓ ' + message);
    } else {
      alert('✗ ' + message);
    }
  }
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

// Function to show success modal
function showSuccessModal(title, message) {
  // Remove existing success modal if any
  const existingModal = document.getElementById('successModal');
  if (existingModal) {
    existingModal.remove();
  }
  
  const modal = document.createElement('div');
  modal.className = 'modal fade';
  modal.id = 'successModal';
  modal.tabIndex = -1;
  modal.setAttribute("role", "dialog");
  
  modal.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header bg-success text-white">
          <h5 class="modal-title">
            <i class="bi bi-check-circle-fill"></i> ${title}
          </h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body text-center py-4">
          <i class="bi bi-check-circle text-success" style="font-size: 4rem;"></i>
          <p class="mt-3 mb-0">${message}</p>
        </div>
        <div class="modal-footer justify-content-center">
          <button type="button" class="btn btn-success" data-bs-dismiss="modal">
            <i class="bi bi-check"></i> OK
          </button>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  const bootstrapModal = new bootstrap.Modal(modal);
  bootstrapModal.show();
  
  modal.addEventListener('hidden.bs.modal', function() {
    document.body.removeChild(modal);
  });
}

// Function to show error modal
function showErrorModal(title, message) {
  // Remove existing error modal if any
  const existingModal = document.getElementById('errorModal');
  if (existingModal) {
    existingModal.remove();
  }
  
  const modal = document.createElement('div');
  modal.className = 'modal fade';
  modal.id = 'errorModal';
  modal.tabIndex = -1;
  modal.setAttribute("role", "dialog");
  
  modal.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header bg-danger text-white">
          <h5 class="modal-title">
            <i class="bi bi-exclamation-triangle-fill"></i> ${title}
          </h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body text-center py-4">
          <i class="bi bi-x-circle text-danger" style="font-size: 4rem;"></i>
          <p class="mt-3 mb-0">${message}</p>
        </div>
        <div class="modal-footer justify-content-center">
          <button type="button" class="btn btn-danger" data-bs-dismiss="modal">
            <i class="bi bi-x"></i> Close
          </button>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  const bootstrapModal = new bootstrap.Modal(modal);
  bootstrapModal.show();
  
  modal.addEventListener('hidden.bs.modal', function() {
    document.body.removeChild(modal);
  });
}

function renderSchedule() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  let dateKey = getLocalDateKey(today);
  const scheduleContent = document.getElementById('scheduleContent');
  const overdueContent = document.getElementById('overdueContent');
  
  // Clear both sections
  if (scheduleContent) scheduleContent.innerHTML = '';
  if (overdueContent) overdueContent.innerHTML = '';
  
  // Fallback for backends that return unpadded keys like YYYY-M-D
  if (!medicalFollowups[dateKey]) {
    const altKey = `${today.getFullYear()}-${today.getMonth() + 1}-${today.getDate()}`;
    if (medicalFollowups[altKey]) {
      dateKey = altKey;
    }
  }

  // Separate today's and overdue follow-ups
  const todayFollowups = [];
  const overdueFollowups = [];
  
  // Get today's follow-ups
  if (medicalFollowups[dateKey] && medicalFollowups[dateKey].length > 0) {
    medicalFollowups[dateKey].forEach(followup => {
      todayFollowups.push({
        ...followup,
        status: 'today',
        date: new Date(followup.followup_date)
      });
    });
  }
  
  // Get overdue follow-ups (past dates)
  Object.keys(medicalFollowups).forEach(key => {
    const followupDate = new Date(key);
    followupDate.setHours(0, 0, 0, 0);
    
    if (followupDate < today) {
      medicalFollowups[key].forEach(followup => {
        overdueFollowups.push({
          ...followup,
          status: 'overdue',
          date: new Date(followup.followup_date)
        });
      });
    }
  });
  
  // Sort overdue by date (oldest first)
  overdueFollowups.sort((a, b) => a.date - b.date);
  
  // Render overdue section (compact version)
  const overdueSection = document.getElementById('overdueSection');
  if (overdueContent && overdueSection) {
    if (overdueFollowups.length > 0) {
      // Show the section
      overdueSection.style.display = '';
      
      const overdueCountEl = document.getElementById('overdueCount');
      if (overdueCountEl) {
        overdueCountEl.textContent = `${overdueFollowups.length} item${overdueFollowups.length !== 1 ? 's' : ''}`;
      }
      
      console.log('Found overdue followups:', overdueFollowups.length);
      const overdueContainer = document.createElement("div");
      overdueContainer.className = "list-group list-group-flush";
      
      // Show all overdue items (scrollable container handles overflow)
      overdueFollowups.forEach((followup, index) => {
        const schedule = document.createElement("div");
        schedule.className = "list-group-item d-flex align-items-center py-2 px-2 border-0 border-bottom";
        schedule.style.cursor = 'pointer';
        schedule.innerHTML = `
          <div class="me-2 text-danger" style="font-size: 0.9rem;"><i class="bi bi-exclamation-triangle"></i></div>
          <div class="flex-grow-1" style="min-width: 0;">
            <div class="d-flex align-items-center justify-content-between">
              <span class="fw-semibold text-truncate" style="font-size: 0.9rem;">${followup.patient_name}</span>
              <small class="text-danger ms-2" style="font-size: 0.75rem; white-space: nowrap;">${followup.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</small>
            </div>
            ${followup.notes ? `<small class="text-muted text-truncate d-block" style="font-size: 0.75rem;">${followup.notes.substring(0, 40)}${followup.notes.length > 40 ? '...' : ''}</small>` : ''}
          </div>
        `;
        schedule.onclick = () => showFollowupDetails(followup, followup.date);
        schedule.onmouseenter = function() {
          this.style.backgroundColor = '#f8f9fa';
        };
        schedule.onmouseleave = function() {
          this.style.backgroundColor = '';
        };
        overdueContainer.appendChild(schedule);
      });
      
      overdueContent.appendChild(overdueContainer);
    } else {
      // Hide the entire section if no overdue items
      overdueSection.style.display = 'none';
    }
  }

  // Render today's section
  if (scheduleContent) {
    if (todayFollowups.length > 0) {
      console.log('Found today followups:', todayFollowups.length);
      const scheduleContainer = document.createElement("div");
      scheduleContainer.className = "list-group";
      
      const maxDisplay = 5;
      const displayToday = todayFollowups.slice(0, maxDisplay);
      
      displayToday.forEach((followup, index) => {
        const schedule = document.createElement("div");
        schedule.className = "list-group-item d-flex align-items-start";
        schedule.innerHTML = `
          <div class="me-3 text-success"><i class="bi bi-calendar-check"></i></div>
          <div class="flex-grow-1">
            <div class="fw-bold">${followup.patient_name} <span class="badge bg-info ms-2">Today</span></div>
            <div class="text-muted">${followup.notes || ''}</div>
          </div>
        `;
        schedule.onclick = () => showFollowupDetails(followup, followup.date);
        scheduleContainer.appendChild(schedule);
      });
      
      // Add "more..." option if there are more than 5 today's events
      if (todayFollowups.length > maxDisplay) {
        const moreSchedule = document.createElement("div");
        moreSchedule.className = "list-group-item d-flex align-items-start text-primary";
        moreSchedule.innerHTML = `
          <div class="me-3 text-primary"><i class="bi bi-three-dots"></i></div>
          <div>
            <div class="fw-bold">+${todayFollowups.length - maxDisplay} more events...</div>
            <div class="text-muted">Click to view all events for today</div>
          </div>
        `;
        moreSchedule.onclick = () => showAllEventsModal(todayFollowups, today);
        scheduleContainer.appendChild(moreSchedule);
      }
      
      scheduleContent.appendChild(scheduleContainer);
    } else {
      scheduleContent.innerHTML = '<div class="text-muted">No schedules for today.</div>';
    }
  }
}                


