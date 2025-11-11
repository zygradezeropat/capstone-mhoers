$(document).ready(function() {
  // Show the active tab on page load
  const activeTab = $('.tab-pane.active').attr('id');
  if (activeTab) {
    $(`a[href="#${activeTab}"]`).tab('show');
  }

  // Initialize DataTables with modern styling
  const tableConfig = {
    responsive: true,
    dom: '<"row mb-3"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
         '<"row"<"col-sm-12"tr>>' +
         '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
    language: {
      search: "_INPUT_",
      searchPlaceholder: "Search records..."
    },
    pageLength: 10,
    order: [[0, 'asc']],
    columnDefs: [
      { 
        targets: -1, 
        orderable: false 
      }
    ]
  };

  // Initialize Active Table
  if ($("#activeTable").length && !$.fn.DataTable.isDataTable('#activeTable')) {
    $("#activeTable").DataTable(tableConfig);
  }

  // Initialize Referred Table
  if ($("#referredTable").length && !$.fn.DataTable.isDataTable('#referredTable')) {
    $("#referredTable").DataTable(tableConfig);
  }

  // Initialize All Patients Table
  if ($("#allTable").length && !$.fn.DataTable.isDataTable('#allTable')) {
    $("#allTable").DataTable(tableConfig);
  }

  // Button click events for View, Edit, Delete using event delegation
  $(document).on('click', '.edit-button', function() {
    const button = $(this);
    
    // Debug: Log data attributes to verify they're being read
    console.log('Lifestyle data from database:', {
      isSmoker: button.attr('data-is-smoker'),
      smokingSticks: button.attr('data-smoking-sticks'),
      isAlcoholic: button.attr('data-is-alcoholic'),
      alcoholBottles: button.attr('data-alcohol-bottles'),
      familyPlanning: button.attr('data-family-planning'),
      familyPlanningType: button.attr('data-family-planning-type')
    });
    $('#editPatientName').val(button.data('patient'));
    $('#editReferralDate').val(button.data('date'));
    $('#editReferFrom').val(button.data('from'));
    $('#editReferTo').val(button.data('to'));
    $('#editStatus').val(button.data('status'));
    const sex = button.data('sex');
    $('#editSex').val(sex);
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
    $('#editIcdCode').val(button.data('icd-code') || '');
    
    // Lifestyle/Social History fields - pulled from database
    // Read raw attribute value (Django yesno filter outputs "True" or "False" as strings)
    const isSmokerAttr = button.attr('data-is-smoker');
    const isSmoker = isSmokerAttr === 'True';
    $('#editIsSmoker').prop('checked', isSmoker);
    const smokingSticks = button.attr('data-smoking-sticks') || '';
    $('#editSmokingSticks').val(smokingSticks);
    $('#editSmokingSticks').prop('disabled', !isSmoker);
    
    const isAlcoholicAttr = button.attr('data-is-alcoholic');
    const isAlcoholic = isAlcoholicAttr === 'True';
    $('#editIsAlcoholic').prop('checked', isAlcoholic);
    const alcoholBottles = button.attr('data-alcohol-bottles') || '';
    $('#editAlcoholBottles').val(alcoholBottles);
    $('#editAlcoholBottles').prop('disabled', !isAlcoholic);
    
    const isFamilyPlanningAttr = button.attr('data-family-planning');
    const isFamilyPlanning = isFamilyPlanningAttr === 'True';
    $('#editFamilyPlanning').prop('checked', isFamilyPlanning);
    const familyPlanningType = button.attr('data-family-planning-type') || '';
    $('#editFamilyPlanningType').val(familyPlanningType);
    $('#editFamilyPlanningType').prop('disabled', !isFamilyPlanning);
    
    // Menstrual History fields
    $('#editMenarche').val(button.data('menarche') || '');
    $('#editSexuallyActive').prop('checked', button.data('sexually-active') === true || button.data('sexually-active') === 'True');
    $('#editNumberOfPartners').val(button.data('number-of-partners') || '');
    $('#editIsMenopause').prop('checked', button.data('is-menopause') === true || button.data('is-menopause') === 'True');
    $('#editMenopauseAge').val(button.data('menopause-age') || '');
    const lmp = button.data('last-menstrual-period');
    if (lmp) {
      $('#editLastMenstrualPeriod').val(lmp);
    }
    $('#editPeriodDuration').val(button.data('period-duration') || '');
    $('#editPeriodInterval').val(button.data('period-interval') || '');
    $('#editPadsPerDay').val(button.data('pads-per-day') || '');
    
    // Pregnancy History fields
    $('#editIsPregnant').prop('checked', button.data('is-pregnant') === true || button.data('is-pregnant') === 'True');
    $('#editGravidity').val(button.data('gravidity') || '');
    $('#editParity').val(button.data('parity') || '');
    $('#editDeliveryType').val(button.data('delivery-type') || '');
    $('#editFullTermBirths').val(button.data('full-term-births') || '');
    $('#editPrematureBirths').val(button.data('premature-births') || '');
    $('#editAbortions').val(button.data('abortions') || '');
    $('#editLivingChildren').val(button.data('living-children') || '');
    
    $('#referral-id-edit-input').val(button.data('id'));
    
    // Show/hide menstrual and pregnancy sections based on sex
    if (sex && sex.toLowerCase() === 'female') {
      $('#menstrualHistorySection').show();
      $('#pregnancyHistorySection').show();
    } else {
      $('#menstrualHistorySection').hide();
      $('#pregnancyHistorySection').hide();
    }
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