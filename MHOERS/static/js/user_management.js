let map;
let marker;

document.addEventListener("DOMContentLoaded", function() {
  // Handle provider type selection
  document.getElementById('selectDoctor').addEventListener('click', function() {
    // Close type selection modal
    const typeModal = bootstrap.Modal.getInstance(document.getElementById('providerTypeModal'));
    typeModal.hide();
    
    // Show the doctor registration modal
    const doctorModal = new bootstrap.Modal(document.getElementById('doctorModal'));
    doctorModal.show();
  });

  document.getElementById('selectNurse').addEventListener('click', function() {
    // Close type selection modal
    const typeModal = bootstrap.Modal.getInstance(document.getElementById('providerTypeModal'));
    typeModal.hide();
    
    // Show the nurse registration modal
    const nurseModal = new bootstrap.Modal(document.getElementById('nurseModal'));
    nurseModal.show();
  });

  document.getElementById('selectBHW').addEventListener('click', function() {
    // Close type selection modal
    const typeModal = bootstrap.Modal.getInstance(document.getElementById('providerTypeModal'));
    typeModal.hide();
    
    // TODO: Show BHW registration modal (to be implemented)
    alert('BHW registration form will be implemented');
  });

  const selectMidwifeBtn = document.getElementById('selectMidwife');
  if (selectMidwifeBtn) {
    selectMidwifeBtn.addEventListener('click', function() {
      // Close type selection modal
      const typeModal = bootstrap.Modal.getInstance(document.getElementById('providerTypeModal'));
      if (typeModal) {
        typeModal.hide();
      }
      
      // Show the midwife registration modal
      const midwifeModalElement = document.getElementById('midwifeModal');
      if (midwifeModalElement) {
        const midwifeModal = new bootstrap.Modal(midwifeModalElement);
        midwifeModal.show();
      } else {
        console.error('Midwife modal element not found');
      }
    });
  } else {
    console.error('Select Midwife button not found');
  }

  document.getElementById('selectHealthcareProvider').addEventListener('click', function() {
    // Close type selection modal
    const typeModal = bootstrap.Modal.getInstance(document.getElementById('providerTypeModal'));
    typeModal.hide();
    
    // Show the existing healthcare provider registration modal
    const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
    registerModal.show();
  });

  const rows = document.querySelectorAll(".clickable-row");

  rows.forEach(row => {
    row.addEventListener("click", function() {
      rows.forEach(r => r.classList.remove("active"));
      this.classList.add("active");

      document.getElementById("cardFacilityId").innerText = this.dataset.id;
      document.getElementById("cardFacility").innerText = this.dataset.facility;
      document.getElementById("cardBHW").innerText = this.dataset.bhw;
      document.getElementById("cardLocation").innerText = `${this.dataset.latitude}, ${this.dataset.longitude}`;
      document.getElementById("infoCard").scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Function to initialize the map
  function initializeMap() {
    if (map) {
      map.remove();
    }

    map = L.map('map').setView([7.587429855100546, 125.82881651697123], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    map.on('click', function(e) {
      const lat = e.latlng.lat;
      const lng = e.latlng.lng;
      document.getElementById('latitude').value = lat;
      document.getElementById('longitude').value = lng;
      if (marker) {
        marker.setLatLng([lat, lng]);
      } else {
        marker = L.marker([lat, lng]).addTo(map);
      }
    });

    setTimeout(() => {
      map.invalidateSize();
    }, 100);
  }


  // Initialize map when modal is shown
  document.getElementById('registerModal').addEventListener('shown.bs.modal', function() {
    initializeMap();
  });
 
  // Clean up map when modal is hidden
  document.getElementById('registerModal').addEventListener('hidden.bs.modal', function() {
    if (map) {
      map.remove();
      map = null;
    }
    if (marker) {
      marker = null;
    }
    document.getElementById('latitude').value = '';
    document.getElementById('longitude').value = '';
  });


  // Delete functionality
  const deleteButtons = document.querySelectorAll('.delete-button');
  deleteButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.stopPropagation(); // Prevent row click event
      const row = this.closest('tr');
      const facilityId = row.dataset.id;
      const facilityName = row.dataset.facility;

      // Populate delete modal
      document.getElementById('deleteFacilityId').textContent = facilityId;
      document.getElementById('deleteFacilityName').textContent = facilityName;
      document.getElementById('deleteFacilityIdInput').value = facilityId;

      // Show delete confirmation modal
      const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'));
      deleteModal.show();
    });
  });

  // Pending User Row Click Functionality
  const pendingUserRows = document.querySelectorAll('.pending-user-row');
  let currentUserType = '';
  let currentUserId = '';

  pendingUserRows.forEach(row => {
    row.addEventListener('click', function(e) {
      // Don't trigger if clicking on buttons
      if (e.target.closest('.btn-group')) {
        return;
      }

      // Remove active class from all rows
      pendingUserRows.forEach(r => r.classList.remove('active'));
      this.classList.add('active');

      // Get user data from data attributes
      currentUserType = this.dataset.userType;
      currentUserId = this.dataset.userId;

      // Populate modal with user data
      populateUserDetailsModal(this);

      // Show the modal
      const modal = new bootstrap.Modal(document.getElementById('pendingUserDetailsModal'));
      modal.show();
    });
  });

  // Function to populate user details modal
  function populateUserDetailsModal(row) {
    const userType = row.dataset.userType;
    
    // Basic information
    document.getElementById('detailFirstName').textContent = row.dataset.firstName || '-';
    document.getElementById('detailLastName').textContent = row.dataset.lastName || '-';
    document.getElementById('detailMiddleName').textContent = row.dataset.middleName || '-';
    document.getElementById('detailEmail').textContent = row.dataset.email || '-';
    document.getElementById('detailPhone').textContent = row.dataset.phone || '-';
    document.getElementById('detailStreetAddress').textContent = row.dataset.streetAddress || '-';
    document.getElementById('detailCity').textContent = row.dataset.city || '-';
    document.getElementById('detailBarangay').textContent = row.dataset.barangay || '-';
    document.getElementById('detailProvince').textContent = row.dataset.province || '-';
    document.getElementById('detailPostalCode').textContent = row.dataset.postalCode || '-';
    document.getElementById('detailRegistrationDate').textContent = row.dataset.registrationDate || '-';

    // Hide all sections first
    document.getElementById('professionalSection').style.display = 'none';
    document.getElementById('bhwSection').style.display = 'none';
    document.getElementById('assignmentSection').style.display = 'none';

    // Show relevant sections based on user type
    if (userType === 'doctor') {
      document.getElementById('professionalSection').style.display = 'block';
      document.getElementById('assignmentSection').style.display = 'block';
      document.getElementById('detailSpecialization').textContent = row.dataset.specialization || '-';
      document.getElementById('detailLicenseNumber').textContent = row.dataset.licenseNumber || '-';
      document.getElementById('detailAssignedBarangay').textContent = row.dataset.assignedBarangay || '-';
    } else if (userType === 'bhw') {
      document.getElementById('bhwSection').style.display = 'block';
      document.getElementById('assignmentSection').style.display = 'block';
      document.getElementById('detailAssignedBarangay').textContent = row.dataset.assignedBarangay || '-';
    } else if (userType === 'nurse') {
      document.getElementById('assignmentSection').style.display = 'block';
      document.getElementById('detailAssignedBarangay').textContent = row.dataset.assignedBarangay || '-';
    }

    // Update modal title based on user type
    const modalTitle = document.getElementById('pendingUserDetailsModalLabel');
    const modalSubtitle = document.querySelector('#pendingUserDetailsModal .modal-subtitle');
    
    if (userType === 'doctor') {
      modalTitle.textContent = `Dr. ${row.dataset.firstName} ${row.dataset.lastName} - Pending Doctor`;
      modalSubtitle.textContent = 'Review doctor registration information';
    } else if (userType === 'bhw') {
      modalTitle.textContent = `${row.dataset.firstName} ${row.dataset.lastName} - Pending BHW`;
      modalSubtitle.textContent = 'Review BHW registration information';
    } else if (userType === 'nurse') {
      modalTitle.textContent = `${row.dataset.firstName} ${row.dataset.lastName} - Pending Nurse`;
      modalSubtitle.textContent = 'Review nurse registration information';
    }
  }

  // Modal action button handlers
  document.getElementById('approveUserBtn').addEventListener('click', function() {
    if (currentUserType && currentUserId) {
      approveUser(currentUserType, currentUserId);
    }
  });

  document.getElementById('rejectUserBtn').addEventListener('click', function() {
    if (currentUserType && currentUserId) {
      rejectUser(currentUserType, currentUserId);
    }
  });
});

// Approval and Rejection Functions
function approveUser(userType, userId) {
    if (confirm(`Are you sure you want to approve this ${userType}?`)) {
        const formData = new FormData();
        formData.append('user_type', userType);
        formData.append('user_id', userId);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        
        fetch('/accounts/approve_user/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessageModal(data.type, data.title, data.message, '', function() {
                    location.reload();
                });
            } else {
                showMessageModal(data.type, data.title, data.message);
            }
        })
        .catch(error => {
            showMessageModal('error', 'Error', 'An error occurred while approving the user.');
            console.error('Error:', error);
        });
    }
}

function rejectUser(userType, userId) {
    // Show input modal for rejection reason
    const reason = prompt(`Please provide a reason for rejecting this ${userType}:`);
    if (reason !== null && reason.trim() !== '') {
        const formData = new FormData();
        formData.append('user_type', userType);
        formData.append('user_id', userId);
        formData.append('reason', reason);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        
        fetch('/accounts/reject_user/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessageModal(data.type, data.title, data.message, '', function() {
                    location.reload();
                });
            } else {
                showMessageModal(data.type, data.title, data.message);
            }
        })
        .catch(error => {
            showMessageModal('error', 'Error', 'An error occurred while rejecting the user.');
            console.error('Error:', error);
        });
    }
}

// Helper function to get CSRF token
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

// Handle AJAX form submissions for create_doctor, create_midwife, create_bhw
document.addEventListener('DOMContentLoaded', function() {
    // Doctor form
    const doctorForm = document.querySelector('.doctor-form');
    if (doctorForm) {
        doctorForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close the form modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('doctorModal'));
                    if (modal) modal.hide();
                    
                    // Show success modal
                    showMessageModal(data.type, data.title, data.message, '', function() {
                        location.reload();
                    });
                } else {
                    showMessageModal(data.type, data.title, data.message);
                }
            })
            .catch(error => {
                showMessageModal('error', 'Error', 'An error occurred while creating the doctor.');
                console.error('Error:', error);
            });
        });
    }
    
    // Midwife form
    const midwifeForm = document.querySelector('#midwifeModal form');
    if (midwifeForm) {
        midwifeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('midwifeModal'));
                    if (modal) modal.hide();
                    
                    showMessageModal(data.type, data.title, data.message, '', function() {
                        location.reload();
                    });
                } else {
                    showMessageModal(data.type, data.title, data.message);
                }
            })
            .catch(error => {
                showMessageModal('error', 'Error', 'An error occurred while creating the midwife.');
                console.error('Error:', error);
            });
        });
    }
    
    // BHW form
    const bhwForm = document.querySelector('#bhwModal form');
    if (bhwForm) {
        bhwForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('bhwModal'));
                    if (modal) modal.hide();
                    
                    showMessageModal(data.type, data.title, data.message, '', function() {
                        location.reload();
                    });
                } else {
                    showMessageModal(data.type, data.title, data.message);
                }
            })
            .catch(error => {
                showMessageModal('error', 'Error', 'An error occurred while creating the BHW.');
                console.error('Error:', error);
            });
        });
    }
});