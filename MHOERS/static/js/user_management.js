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
      document.getElementById('detailRegistrationNumber').textContent = row.dataset.registrationNumber || '-';
      document.getElementById('detailAccreditationNumber').textContent = row.dataset.accreditationNumber || '-';
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
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '{% url "approve_user" %}';
        
        const csrfToken = document.createElement('input');
        csrfToken.type = 'hidden';
        csrfToken.name = 'csrfmiddlewaretoken';
        csrfToken.value = '{{ csrf_token }}';
        
        const userTypeInput = document.createElement('input');
        userTypeInput.type = 'hidden';
        userTypeInput.name = 'user_type';
        userTypeInput.value = userType;
        
        const userIdInput = document.createElement('input');
        userIdInput.type = 'hidden';
        userIdInput.name = 'user_id';
        userIdInput.value = userId;
        
        form.appendChild(csrfToken);
        form.appendChild(userTypeInput);
        form.appendChild(userIdInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

function rejectUser(userType, userId) {
    const reason = prompt(`Please provide a reason for rejecting this ${userType}:`);
    if (reason !== null && reason.trim() !== '') {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '{% url "reject_user" %}';
        
        const csrfToken = document.createElement('input');
        csrfToken.type = 'hidden';
        csrfToken.name = 'csrfmiddlewaretoken';
        csrfToken.value = '{{ csrf_token }}';
        
        const userTypeInput = document.createElement('input');
        userTypeInput.type = 'hidden';
        userTypeInput.name = 'user_type';
        userTypeInput.value = userType;
        
        const userIdInput = document.createElement('input');
        userIdInput.type = 'hidden';
        userIdInput.name = 'user_id';
        userIdInput.value = userId;
        
        const reasonInput = document.createElement('input');
        reasonInput.type = 'hidden';
        reasonInput.name = 'reason';
        reasonInput.value = reason;
        
        form.appendChild(csrfToken);
        form.appendChild(userTypeInput);
        form.appendChild(userIdInput);
        form.appendChild(reasonInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}