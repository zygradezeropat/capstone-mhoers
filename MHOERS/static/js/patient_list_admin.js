$(document).ready(function() {
  // Show the active tab on page load
  const activeTab = $('.tab-pane.active').attr('id');
  if (activeTab) {
    $(`a[href="#${activeTab}"]`).tab('show');
  }

  // Initialize DataTables with modern styling
  const tableConfig = {
    responsive: true,
    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
         '<"row"<"col-sm-12"tr>>' +
         '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
    language: {
      search: "_INPUT_",
      searchPlaceholder: "Search patient records..."
    },
    pageLength: 10,
    order: [[0, 'asc']],
    columnDefs: [
      { 
        targets: -1, 
        orderable: false 
      },
      {
        targets: 0,
        type: 'string',
        render: function(data, type, row) {
          if (type === 'sort') {
            // Extract the ID number from the badge text for sorting
            const idMatch = data.match(/ID: #(\d+)/);
            return idMatch ? idMatch[1] : '';
          }
          return data;
        }
      }
    ]
  };

  $("#activeTable").DataTable(tableConfig);
  $("#pendingTable").DataTable(tableConfig);
  $("#referredTable").DataTable(tableConfig);
  $("#allTable").DataTable(tableConfig);

  // Button click events for View, Edit, Delete using event delegation
  $(document).on('click', '.edit-button', function() {
    const button = $(this);
    $('#editPatientName').val(button.data('patient'));
    $('#editReferralDate').val(button.data('date'));
    $('#editReferFrom').val(button.data('from'));
    $('#editReferTo').val(button.data('to'));
    $('#editStatus').val(button.data('status'));
    $('#editSex').val(button.data('sex'));
    $('#editHeight').val(button.data('height'));
    $('#editWeight').val(button.data('weight'));
    $('#editTemperature').val(button.data('temperature'));
    $('#editBpSystolic').val(button.data('systolic'));
    $('#editBpDiastolic').val(button.data('diastolic'));
    $('#editRespiratory').val(button.data('respiratory'));
    $('#editNotes').val(button.data('notes'));
    $('#editSymptoms').val(button.data('symptoms'));
    $('#editworkUp').val(button.data('workup'));
    $('#editDisease').val(button.data('disease'));
    $('#referral-id-edit-input').val(button.data('id'));
  }); 

  $(document).on('click', '.delete-button', function() {
    const button = $(this);
    const referralId = button.data('id');
    const patientName = button.data('patient');
    $('#referral-id-del').val(referralId);
    $('#delete-confirm-text').text(`Are you sure you want to delete the referral of ${patientName}?`);
  });

  $(document).on('click', '.view-button', function() {
    const button = $(this);
    const modalBody = $('#viewReferralModal .modal-body');
    
    
    // Check if this is from All Patients tab (has birth data)
    if (button.data('birth')) {
      // Clear existing content
      modalBody.empty();
      
      // Get name components directly from data attributes
      const firstName = button.data('first-name');
      const middleName = button.data('middle-name');
      const lastName = button.data('last-name');
      
      // Create patient information display
      const content = `
        <div class="container-fluid py-4">
            <div class="row">

      <!-- Chief Complaint & History -->

      <div class="col-md-3 mb-3">
        <div class="card shadow-sm h-100">
          <div class="card-header bg-primary text-white"><strong>CHIEF COMPLAINT & HISTORY</strong></div>
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">Chief Complaint</h6>
            <p>${button.data("address")}</p>
  
            <h6 class="card-subtitle mt-3 mb-2 text-muted">History of Present Illness</h6>
            <p>
              ↑BP LAST SUNDAY 150/80<br>
              (+) DIZZINESS<br>
              (+) WATERY STOOL<br>
              Herbal treatment: Bayabas & Mansanitas
            </p>
          </div>
        </div>
      </div>
  
      <!-- OBJECTIVE CARD -->
      <div class="col-md-3 mb-3">
        <div class="card shadow-sm h-100">
          <div class="card-header bg-info text-white">OBJECTIVE</div>
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">Vital Signs</h6>
            <ul class="list-unstyled">
              <li>BP: 142/76</li>
              <li>HR: 86</li>
              <li>TEMP: 36.4</li>
              <li>O2 SAT: 97%</li>
            </ul>
            <h6 class="card-subtitle mt-3 mb-2 text-muted">Physical Exam</h6>
            <p>Notes here...</p>
          </div>
        </div>
      </div>
  
      <!-- ASSESSMENT CARD -->
      <div class="col-md-3 mb-3">
        <div class="card shadow-sm h-100">
          <div class="card-header bg-warning text-dark">ASSESSMENT</div>
          <div class="card-body">
            <h6 class="card-subtitle mb-2">Diagnosis</h6>
            <p><strong>Benign Paroxysmal Vertigo (H81.1)</strong></p>
            <p class="text-muted">Improving dizziness<br>No more diarrhea</p>
          </div>
        </div>
      </div>
  
      <!-- PLAN CARD -->
      <div class="col-md-3 mb-3">
        <div class="card shadow-sm h-100">
          <div class="card-header bg-success text-white">PLAN</div>
          <div class="card-body">
            <h6 class="card-subtitle mb-2">Medication</h6>
            <p>Cinnarizine 25 mg<br>1 tab BID × 5 days</p>
            <span class="badge badge-danger">GIVEN</span>
  
            <h6 class="card-subtitle mt-3 mb-2">Advice</h6>
            <p>Non-pharmacological advice given.</p>
          </div>
        </div>
      </div>
  
    </div>
  </div>
      `;
      
      modalBody.html(content);
      
      // Update modal title and hide footer
      $('#viewReferralModal .modal-title').html('<i class="bi bi-person-lines-fill mr-2"></i>Patient Information');
      $('#viewReferralModal .modal-footer').hide();
    } else {
      // Original referral view logic
      $("#viewPatientName").val(button.data("patient"));
      $("#viewReferralDate").val(button.data("date"));
      $("#viewReferFrom").val(button.data("from"));
      $("#viewReferTo").val(button.data("to"));
      $("#viewStatus").val(button.data("status"));
      $("#viewNotes").val(button.data("notes"));
      $("#viewSymptoms").val(button.data("symptoms"));
      $("#viewWorkUp").val(button.data("workup"));
      $("#referral-id-input").val(button.data("id"));
      $("#viewheight").val(button.data("height"));
      $("#viewWeight").val(button.data("weight"));
      $("#viewbpsystolic").val(button.data("systolic"));
      $("#viewbpdiastolic").val(button.data("diastolic"));
      $("#viewpulserate").val(button.data("pulserate"));
      $("#viewrespiratory").val(button.data("respiratory"));
      $("#viewtemperature").val(button.data("temperature"));
      $("#viewoxygen").val(button.data("oxygen"));
      $("#viewcomplaint").val(button.data("complaint"));
      $("#viewdisease").val(button.data("disease"));
      $("#viewSex").val(button.data("sex"));

      // Hide Referred button if status is completed
      const status = button.data("status");
      const referredButton = $("#viewReferralModal .modal-footer form");
      if (status === "completed") {
        referredButton.hide();
      } else {
        referredButton.show();
      }
    }
  });
}); 