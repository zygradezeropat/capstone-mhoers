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
      searchPlaceholder: "Search records...",
      emptyTable: "No records available."
    },
    pageLength: 10,
    order: [[6, 'asc']], // Sort by Severity column (index 6) ascending (High=0, Medium=1, Low=2, Unspecified=3)
    columnDefs: [
      { 
        targets: -1, 
        orderable: false 
      },
      {
        targets: 6, // Severity column
        type: 'num', // Treat as numeric for proper sorting
        orderData: [6] // Use data-order attribute
      }
    ]
  };

  // Initialize Pending Table
  const $pendingTable = $("#pendingTable");
  if ($pendingTable.length) {
    if ($.fn.DataTable.isDataTable($pendingTable)) {
      $pendingTable.DataTable().destroy();
    }
    $pendingTable.DataTable(tableConfig);
  }

  // Initialize Active Table
  const $activeTable = $("#activeTable");
  if ($activeTable.length) {
    if ($.fn.DataTable.isDataTable($activeTable)) {
      $activeTable.DataTable().destroy();
    }
    $activeTable.DataTable(tableConfig);
  }

  // Initialize Referred Table (different config - no Severity column)
  const $referredTable = $("#referredTable");
  if ($referredTable.length) {
    if ($.fn.DataTable.isDataTable($referredTable)) {
      $referredTable.DataTable().destroy();
    }
    // Referred table has different columns: Date/Time, Patient Name, Facility, Location, Status, Actions
    // So it doesn't have a Severity column - use default sort by Date (column 0)
    const referredTableConfig = {
      responsive: true,
      dom: '<"row mb-3"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
           '<"row"<"col-sm-12"tr>>' +
           '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
      language: {
        search: "_INPUT_",
        searchPlaceholder: "Search records...",
        emptyTable: "No records available."
      },
      pageLength: 10,
      order: [[0, 'desc']], // Sort by Date/Time column (index 0) descending (newest first)
      columnDefs: [
        { 
          targets: -1, 
          orderable: false 
        },
        {
          targets: 0, // Date/Time column
          type: 'num', // Treat as numeric (timestamp) for proper sorting
          orderData: [0] // Use data-order attribute
        }
      ],
      // Set table ID for filtering
      sTableId: 'referredTable'
    };
    $referredTable.DataTable(referredTableConfig);
  }

  // Initialize All Patients Table - only when tab is visible
  function initAllPatientsTable() {
    const $allTable = $("#allTable");
    if (!$allTable.length) {
      return; // Table doesn't exist
    }
    
    // Check if table is in a visible tab
    const $tabPane = $allTable.closest('.tab-pane');
    const isTabActive = $tabPane.length && ($tabPane.hasClass('active') || $tabPane.hasClass('show'));
    
    // Don't initialize if tab is not active (DataTables needs visible table to count columns correctly)
    if (!isTabActive) {
      return;
    }
    
    // Destroy existing DataTable if it exists
    if ($.fn.DataTable.isDataTable('#allTable')) {
      try {
        $allTable.DataTable().destroy();
      } catch (e) {
        console.warn('Error destroying existing DataTable:', e);
      }
    }
    
    // Check if table structure is valid
    const $thead = $allTable.find('thead');
    const $tbody = $allTable.find('tbody');
    
    if (!$thead.length || !$tbody.length) {
      console.warn('allTable missing thead or tbody');
      return;
    }
    
    const headerCols = $thead.find('th').length;
    
    if (headerCols === 0) {
      console.warn('allTable has no header columns');
      return;
    }
    
    // Remove any rows with colspan (empty state rows) - DataTables will handle empty state
    $tbody.find('tr').each(function() {
      const $row = $(this);
      const $firstCell = $row.find('td').first();
      if ($firstCell.length && $firstCell.attr('colspan')) {
        $row.remove();
      }
    });
    
    // Verify all remaining rows have correct number of cells
    let validRowCount = 0;
    let hasInvalidRows = false;
    
    $tbody.find('tr').each(function() {
      const $row = $(this);
      const cellCount = $row.find('td').length;
      
      // Skip rows with no cells (shouldn't happen, but just in case)
      if (cellCount === 0) {
        $row.remove();
        return;
      }
      
      if (cellCount !== headerCols) {
        console.warn('Row has', cellCount, 'cells but header has', headerCols, '- removing invalid row');
        $row.remove(); // Remove invalid rows instead of just flagging
        hasInvalidRows = true;
      } else {
        validRowCount++;
      }
    });
    
    // Only initialize if we have valid structure (even if empty, that's fine)
    // DataTables can handle empty tables as long as structure is correct
    if (hasInvalidRows && validRowCount === 0) {
      console.error('allTable has no valid rows after cleanup');
      return;
    }
    
    // Ensure table is visible before initializing
    const isTableVisible = $allTable.is(':visible') && $allTable.width() > 0;
    if (!isTableVisible) {
      // Wait a bit and try again if tab is active
      setTimeout(function() {
        if ($allTable.is(':visible') && $allTable.width() > 0) {
          try {
            $allTable.DataTable(tableConfig);
          } catch (e) {
            console.error('Error initializing allTable DataTable:', e);
          }
        }
      }, 100);
      return;
    }
    
    // Initialize DataTable
    try {
      $allTable.DataTable(tableConfig);
    } catch (e) {
      console.error('Error initializing allTable DataTable:', e);
    }
  }
  
  // Initialize when tab is shown (Bootstrap 4 and 5 compatible)
  $('a[href="#tab3"], button[data-bs-target="#tab3"], button[data-target="#tab3"]').on('shown.bs.tab shown', function() {
    // Wait a bit longer to ensure table is fully rendered
    setTimeout(function() {
      // Force a layout recalculation
      const $allTable = $('#allTable');
      if ($allTable.length) {
        $allTable[0].offsetHeight; // Force reflow
      }
      initAllPatientsTable();
    }, 300);
  });
  
  // Also listen for tab pane show event
  $('#tab3').on('shown.bs.tab', function() {
    setTimeout(function() {
      const $allTable = $('#allTable');
      if ($allTable.length) {
        $allTable[0].offsetHeight; // Force reflow
      }
      initAllPatientsTable();
    }, 300);
  });
  
  // Initialize if tab is already active (with delay to ensure DOM is ready)
  if ($('#tab3').hasClass('active') || $('#tab3').hasClass('show')) {
    setTimeout(function() {
      const $tab3 = $('#tab3');
      const $allTable = $('#allTable');
      if ($tab3.length && $allTable.length && 
          ($tab3.hasClass('active') || $tab3.hasClass('show'))) {
        // Force a layout recalculation
        $allTable[0].offsetHeight; // Force reflow
        initAllPatientsTable();
      }
    }, 400);
  }
  
  // Initialize allTable when view_mode == 'patients' (no tabs, table is directly visible)
  // Check if allTable exists and is not inside a tab-pane
  const $allTableDirect = $('#allTable');
  if ($allTableDirect.length) {
    const $tabPane = $allTableDirect.closest('.tab-pane');
    // If table is NOT inside a tab-pane, it means we're in patients mode
    if (!$tabPane.length) {
      // Table is directly visible (patients mode), initialize it
      setTimeout(function() {
        if ($allTableDirect.length && $allTableDirect.is(':visible')) {
          // Use a simpler config for patients table (no severity column)
          const patientsTableConfig = {
            responsive: true,
            dom: '<"row mb-3"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                 '<"row"<"col-sm-12"tr>>' +
                 '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
            language: {
              search: "_INPUT_",
              searchPlaceholder: "Search patients...",
              emptyTable: "No patients available."
            },
            pageLength: 10,
            order: [[0, 'asc']], // Sort by Patient Information (name) ascending
            columnDefs: [
              { 
                targets: -1, // Actions column
                orderable: false 
              }
            ]
          };
          
          // Destroy existing DataTable if it exists
          if ($.fn.DataTable.isDataTable($allTableDirect)) {
            $allTableDirect.DataTable().destroy();
          }
          
          // Initialize DataTable
          try {
            $allTableDirect.DataTable(patientsTableConfig);
          } catch (e) {
            console.error('Error initializing allTable DataTable (patients mode):', e);
          }
        }
      }, 300);
    }
  }

  // Function to convert and set date value
  function setEditReferralDate(dateValue) {
    const $dateField = $('#editReferralDate');
    
    if (!$dateField.length) {
      console.error('editReferralDate field not found in DOM');
      return;
    }
    
    if (!dateValue) {
      console.warn('No date value provided');
      $dateField.val('');
      return;
    }
    
    console.log('Raw date value:', dateValue);
    
    // Parse date string like "2025-11-17 02:30 PM" or "2025-11-17 2:30 PM"
    const dateMatch = dateValue.match(/(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})\s+(AM|PM)/i);
    if (dateMatch) {
      const [, datePart, hour, minute, ampm] = dateMatch;
      let hour24 = parseInt(hour, 10);
      if (ampm.toUpperCase() === 'PM' && hour24 !== 12) {
        hour24 += 12;
      } else if (ampm.toUpperCase() === 'AM' && hour24 === 12) {
        hour24 = 0;
      }
      const formattedDate = `${datePart}T${hour24.toString().padStart(2, '0')}:${minute}`;
      console.log('Converted date for datetime-local:', formattedDate);
      $dateField.val(formattedDate);
      
      // Verify the value was set
      const setValue = $dateField.val();
      if (setValue !== formattedDate) {
        console.warn('Value mismatch! Expected:', formattedDate, 'Got:', setValue);
        // Try setting it again
        setTimeout(function() {
          $dateField.val(formattedDate);
          console.log('Retry setting date value:', $dateField.val());
        }, 50);
      }
    } else {
      // Try alternative format: "YYYY-MM-DD HH:MM" (24-hour format)
      const dateMatch24 = dateValue.match(/(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})/);
      if (dateMatch24) {
        const [, datePart, hour, minute] = dateMatch24;
        const formattedDate = `${datePart}T${hour.padStart(2, '0')}:${minute}`;
        console.log('Converted date (24-hour format):', formattedDate);
        $dateField.val(formattedDate);
      } else {
        // Fallback: try to parse as-is or use original value
        console.warn('Could not parse date format:', dateValue);
        $dateField.val(dateValue);
      }
    }
  }

  // Store the current edit button for use in modal shown event
  let currentEditButton = null;

  // Button click events for View, Edit, Delete using event delegation
  $(document).on('click', '.edit-button', function() {
    const button = $(this);
    currentEditButton = button; // Store for later use
    
    // Debug: Log data attributes to verify they're being read
    console.log('Lifestyle data from database:', {
      isSmoker: button.attr('data-is-smoker'),
      smokingSticks: button.attr('data-smoking-sticks'),
      isAlcoholic: button.attr('data-is-alcoholic'),
      alcoholBottles: button.attr('data-alcohol-bottles'),
      familyPlanning: button.attr('data-family-planning'),
      familyPlanningType: button.attr('data-family-planning-type')
    });
    
    // Check if prediction is "Unspecified" and store for modal check
    const diseasePrediction = button.attr('data-disease') || '';
    if (diseasePrediction && (diseasePrediction.includes('Unspecified') || diseasePrediction.includes('No prediction available'))) {
      // Store in a way that the modal can access it
      $('#referral-id-edit-input').data('unspecified-prediction', true);
    } else {
      $('#referral-id-edit-input').data('unspecified-prediction', false);
    }
    
    $('#editPatientName').val(button.data('patient'));
    
    // Convert date from "YYYY-MM-DD hh:mm A" to "YYYY-MM-DDTHH:MM" for datetime-local input
    // Use attr() instead of data() to get the raw attribute value
    const dateValue = button.attr('data-date') || button.data('date');
    setEditReferralDate(dateValue);
    
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
    $('#editPulseRate').val(button.data('pulserate') || button.data('pulse-rate') || button.data('pulse'));
    $('#editNotes').val(button.data('notes'));
    $('#editSymptoms').val(button.data('symptoms'));
    $('#editworkUp').val(button.data('workup'));
    $('#editDisease').val(button.data('disease'));
    $('#editIcdCode').val(button.data('icd-code') || '');
    
    // Populate Findings dropdown (new merged field with transformation)
    // Check if referral has a disease ID (from database)
    const diseaseId = button.data('disease-id') || '';
    const mhoFindings = button.data('mho-findings') || button.attr('data-mho-findings') || '';
    const finalDiagnosis = mhoFindings || button.data('final-diagnosis') || '';
    
    // Store for use in modal shown event
    window.pendingFindingsData = {
      diseaseId: diseaseId,
      finalDiagnosis: finalDiagnosis
    };
    
    // Lifestyle/Social History fields - pulled from database
    // Read raw attribute value (Django yesno filter outputs "True" or "False" as strings)
    const isSmokerAttr = button.attr('data-is-smoker');
    const isSmoker = isSmokerAttr === 'True';
    $('#editIsSmoker').prop('checked', isSmoker);
    // Add hidden input to preserve checkbox value when disabled
    if (!$('#editIsSmokerHidden').length) {
      $('#editIsSmoker').after('<input type="hidden" name="editIsSmoker" id="editIsSmokerHidden">');
    }
    $('#editIsSmokerHidden').val(isSmoker ? 'on' : '');
    
    const smokingSticks = button.attr('data-smoking-sticks') || '';
    $('#editSmokingSticks').val(smokingSticks);
    // Use readonly instead of disabled so value is submitted
    $('#editSmokingSticks').prop('readonly', !isSmoker).prop('disabled', false);
    if (!isSmoker) {
      $('#editSmokingSticks').addClass('bg-light');
    }
    
    const isAlcoholicAttr = button.attr('data-is-alcoholic');
    const isAlcoholic = isAlcoholicAttr === 'True';
    $('#editIsAlcoholic').prop('checked', isAlcoholic);
    // Add hidden input to preserve checkbox value when disabled
    if (!$('#editIsAlcoholicHidden').length) {
      $('#editIsAlcoholic').after('<input type="hidden" name="editIsAlcoholic" id="editIsAlcoholicHidden">');
    }
    $('#editIsAlcoholicHidden').val(isAlcoholic ? 'on' : '');
    
    const alcoholBottles = button.attr('data-alcohol-bottles') || '';
    $('#editAlcoholBottles').val(alcoholBottles);
    // Use readonly instead of disabled so value is submitted
    $('#editAlcoholBottles').prop('readonly', !isAlcoholic).prop('disabled', false);
    if (!isAlcoholic) {
      $('#editAlcoholBottles').addClass('bg-light');
    }
    
    const isFamilyPlanningAttr = button.attr('data-family-planning');
    const isFamilyPlanning = isFamilyPlanningAttr === 'True';
    $('#editFamilyPlanning').prop('checked', isFamilyPlanning);
    // Add hidden input to preserve checkbox value when disabled
    if (!$('#editFamilyPlanningHidden').length) {
      $('#editFamilyPlanning').after('<input type="hidden" name="editFamilyPlanning" id="editFamilyPlanningHidden">');
    }
    $('#editFamilyPlanningHidden').val(isFamilyPlanning ? 'on' : '');
    
    const familyPlanningType = button.attr('data-family-planning-type') || '';
    $('#editFamilyPlanningType').val(familyPlanningType);
    // Use readonly instead of disabled so value is submitted
    $('#editFamilyPlanningType').prop('readonly', !isFamilyPlanning).prop('disabled', false);
    if (!isFamilyPlanning) {
      $('#editFamilyPlanningType').addClass('bg-light');
    }
    
    // Examined By (Doctor)
    const examinedById = button.attr('data-examined-by') || '';
    $('#editExaminedBy').val(examinedById);
    
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
      
      // Make all Menstrual History fields readonly (not disabled) so values are submitted
      // Text/number inputs: use readonly
      $('#editMenarche').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editNumberOfPartners').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editMenopauseAge').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editLastMenstrualPeriod').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editPeriodDuration').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editPeriodInterval').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editPadsPerDay').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      
      // Checkboxes: keep disabled but add hidden inputs to preserve values
      const sexuallyActiveChecked = $('#editSexuallyActive').is(':checked');
      if (!$('#editSexuallyActiveHidden').length) {
        $('#editSexuallyActive').after('<input type="hidden" name="editSexuallyActive" id="editSexuallyActiveHidden">');
      }
      $('#editSexuallyActiveHidden').val(sexuallyActiveChecked ? 'on' : '');
      $('#editSexuallyActive').prop('disabled', true);
      
      const isMenopauseChecked = $('#editIsMenopause').is(':checked');
      if (!$('#editIsMenopauseHidden').length) {
        $('#editIsMenopause').after('<input type="hidden" name="editIsMenopause" id="editIsMenopauseHidden">');
      }
      $('#editIsMenopauseHidden').val(isMenopauseChecked ? 'on' : '');
      $('#editIsMenopause').prop('disabled', true);
      
      // Make all Pregnancy History fields readonly (not disabled) so values are submitted
      // Text/number inputs: use readonly
      $('#editGravidity').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editParity').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editDeliveryType').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editFullTermBirths').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editPrematureBirths').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editAbortions').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      $('#editLivingChildren').prop('readonly', true).prop('disabled', false).addClass('bg-light');
      
      // Checkboxes: keep disabled but add hidden inputs to preserve values
      const isPregnantChecked = $('#editIsPregnant').is(':checked');
      if (!$('#editIsPregnantHidden').length) {
        $('#editIsPregnant').after('<input type="hidden" name="editIsPregnant" id="editIsPregnantHidden">');
      }
      $('#editIsPregnantHidden').val(isPregnantChecked ? 'on' : '');
      $('#editIsPregnant').prop('disabled', true);
      
    } else {
      $('#menstrualHistorySection').hide();
      $('#pregnancyHistorySection').hide();
    }
    
    // Before form submission, ensure all hidden inputs for disabled checkboxes are updated
    $('#editReferralForm').off('submit.preserveDisabledFields').on('submit.preserveDisabledFields', function() {
      // Update hidden inputs for Lifestyle checkboxes
      if ($('#editIsSmokerHidden').length) {
        $('#editIsSmokerHidden').val($('#editIsSmoker').is(':checked') ? 'on' : '');
      }
      if ($('#editIsAlcoholicHidden').length) {
        $('#editIsAlcoholicHidden').val($('#editIsAlcoholic').is(':checked') ? 'on' : '');
      }
      if ($('#editFamilyPlanningHidden').length) {
        $('#editFamilyPlanningHidden').val($('#editFamilyPlanning').is(':checked') ? 'on' : '');
      }
      
      // Update hidden inputs for Menstrual History checkboxes (if section is visible)
      if ($('#menstrualHistorySection').is(':visible')) {
        if ($('#editSexuallyActiveHidden').length) {
          $('#editSexuallyActiveHidden').val($('#editSexuallyActive').is(':checked') ? 'on' : '');
        }
        if ($('#editIsMenopauseHidden').length) {
          $('#editIsMenopauseHidden').val($('#editIsMenopause').is(':checked') ? 'on' : '');
        }
      }
      
      // Update hidden inputs for Pregnancy History checkboxes (if section is visible)
      if ($('#pregnancyHistorySection').is(':visible')) {
        if ($('#editIsPregnantHidden').length) {
          $('#editIsPregnantHidden').val($('#editIsPregnant').is(':checked') ? 'on' : '');
        }
      }
    });
  });

  // Ensure date is set when modal is fully shown (in case it wasn't set on click)
  // Use a longer delay to ensure loadDraft and other initialization is complete
  $(document).on('shown.bs.modal', '#editReferralModal', function() {
    if (currentEditButton && currentEditButton.length) {
      const dateValue = currentEditButton.attr('data-date') || currentEditButton.data('date');
      if (dateValue) {
        console.log('Setting date on modal shown:', dateValue);
        // Use longer timeout to ensure loadDraft and other modals have finished
        setTimeout(function() {
          setEditReferralDate(dateValue);
          // Also set it again after a bit more delay to ensure it persists
          setTimeout(function() {
            setEditReferralDate(dateValue);
          }, 200);
        }, 300);
      }
    }
  }); 

  $(document).on('click', '.delete-button', function() {
    const button = $(this);
    const referralId = button.data('id');
    const patientName = button.data('patient');
    $('#referral-id-del').val(referralId);
    $('#delete-confirm-text').text(`Are you sure you want to delete the referral of ${patientName}?`);
  });

  // Store button reference for modal event
  let currentViewButton = null;
  
  $(document).on('click', '.view-button', function(e) {
    currentViewButton = $(this);
    // Also populate immediately in case modal opens before event fires
    setTimeout(function() {
      if (currentViewButton && $('#viewReferralModal').hasClass('show')) {
        populateViewModal(currentViewButton);
      }
    }, 100);
  });
  
  // Populate modal when it's about to show (Bootstrap 5 event)
  $('#viewReferralModal').on('show.bs.modal', function(e) {
    // Check if modal was opened from referral history item
    // If so, skip populateViewModal - it will be populated by AJAX via populateReferralModalFromData
    if (window.openingFromReferralHistory) {
      console.log('Modal opened from referral history item - skipping populateViewModal');
      return;
    }
    
    const button = currentViewButton || $(e.relatedTarget);
    if (button && button.length) {
      populateViewModal(button);
    } else {
      // Try to find the button that triggered this
      const triggerButton = $('.view-button').filter(function() {
        return $(this).attr('data-bs-target') === '#viewReferralModal' || 
               $(this).attr('data-target') === '#viewReferralModal';
      }).last();
      if (triggerButton.length) {
        currentViewButton = triggerButton;
        populateViewModal(triggerButton);
      }
    }
  });
  
  // Clear the flag when modal is hidden (safety check)
  $('#viewReferralModal').on('hidden.bs.modal', function() {
    if (window.openingFromReferralHistory) {
      window.openingFromReferralHistory = false;
    }
  });
  
  function getDataValue(button, attrNames, fallback = '') {
    if (!button || !button.length) {
      return fallback;
    }
    
    for (let i = 0; i < attrNames.length; i++) {
      const attrName = attrNames[i];
      if (!attrName) {
        continue;
      }
      
      const attrValue = button.attr(attrName);
      if (attrValue !== undefined && attrValue !== null && attrValue !== '') {
        return attrValue;
      }
      
      const dataKey = attrName.replace(/^data-/, '').replace(/-([a-z])/g, (match, letter) => letter.toUpperCase());
      const dataValue = button.data(dataKey);
      if (dataValue !== undefined && dataValue !== null && dataValue !== '') {
        return dataValue;
      }
    }
    
    return fallback;
  }
  
  // Function to populate view modal
  function populateViewModal(button) {
    console.log('populateViewModal called with button:', button);
    if (!button || !button.length) {
      console.log('No button provided or button is empty');
      return;
    }
    if (!button.hasClass('view-button')) {
      console.log('Button does not have view-button class');
      return;
    }
    
    const $referralModal = $('#viewReferralModal');
    if (!$referralModal.length) {
      console.warn('viewReferralModal not found');
      return;
    }
    
    const modalBody = $referralModal.find('.modal-body');
    const defaultLayout = modalBody.find('#viewReferralDefaultLayout');
    const specialLayout = modalBody.find('#viewReferralSpecialLayout');
    console.log('Modal body found:', modalBody.length);
    console.log('Default layout found:', defaultLayout.length);
    console.log('Special layout found:', specialLayout.length);
    
    // Only check for defaultLayout - specialLayout is optional (for All Patients tab)
    if (!defaultLayout.length) {
      console.warn('Referral modal default layout missing. Continuing anyway...');
      // Don't return - continue with population
    }
    
    const hasBirthData = !!(button.attr('data-birth') || button.data('birth'));
    
    const setFieldValue = (selector, value, fallback = 'N/A') => {
      const $field = $referralModal.find(selector);
      if (!$field.length) {
        console.warn('Field not found:', selector);
        return;
      }
      // Determine final value
      let finalValue;
      if (arguments.length === 3 && fallback === '') {
        // Fallback was explicitly set to empty string - preserve empty values
        // Use value if it exists (even if empty string), otherwise use empty string
        finalValue = (value === undefined || value === null) ? '' : String(value);
      } else {
        // Default behavior: use fallback if value is undefined, null, or empty
        finalValue = (value !== undefined && value !== null && value !== '') ? String(value) : fallback;
      }
      
      // Set the value
      $field.val(finalValue);
      
      // Debug log for Menstrual History and Pregnancy History fields
      if (selector.includes('Menarche') || selector.includes('Period') || selector.includes('Pads') || 
          selector.includes('Menopause') || selector.includes('Partners') ||
          selector.includes('Gravidity') || selector.includes('Parity') || selector.includes('Delivery') ||
          selector.includes('Births') || selector.includes('Abortions') || selector.includes('Children')) {
        console.log('🔵 Setting field:', selector, 
          '| Raw value:', value, 
          '| Type:', typeof value,
          '| Final value:', finalValue,
          '| Field exists:', $field.length > 0,
          '| Field current value:', $field.val());
      }
    };
    
    const setCheckboxValue = (selector, value) => {
      const $field = $referralModal.find(selector);
      if (!$field.length) {
        return;
      }
      const boolValue = value === true || value === 'True' || value === 'true';
      $field.prop('checked', boolValue);
    };
    
    // Check if this is from All Patients tab (has birth data)
    if (hasBirthData && specialLayout.length) {
      // Switch to special layout but keep default markup intact
      if (defaultLayout.length) {
        defaultLayout.addClass('d-none');
      }
      specialLayout.removeClass('d-none');
      specialLayout.empty();
      
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
      
      specialLayout.html(content);
      
      // Update modal title and hide footer
      $('#viewReferralModal .modal-title').html('<i class="bi bi-person-lines-fill mr-2"></i>Patient Information');
      $('#viewReferralModal .modal-footer').hide();
    } else {
      // Ensure default layout is visible and special content hidden (if it exists)
      if (specialLayout.length) {
        specialLayout.addClass('d-none').empty();
      }
      if (defaultLayout.length) {
        defaultLayout.removeClass('d-none');
      }
      
      // Explicitly ensure all section cards are visible (fix for first section being hidden)
      defaultLayout.find('.referral-section-card').removeClass('d-none').css({
        'display': 'block',
        'visibility': 'visible',
        'opacity': '1',
        'height': 'auto',
        'overflow': 'visible'
      });
      
      // Force Patient Information section to be visible
      const patientInfoSection = defaultLayout.find('.patient-info-section');
      if (patientInfoSection.length) {
        patientInfoSection.removeClass('d-none').css({
          'display': 'block',
          'visibility': 'visible',
          'opacity': '1',
          'height': 'auto',
          'overflow': 'visible'
        });
        patientInfoSection.find('.row').css({
          'display': 'flex',
          'visibility': 'visible',
          'opacity': '1'
        });
        patientInfoSection.find('.col-md-4, .modern-form-group, .modern-input-wrapper, input, label').css({
          'display': 'block',
          'visibility': 'visible',
          'opacity': '1'
        });
      }
      
      // Original referral view logic - populate all fields matching edit modal
      console.log('Populating referral view fields...');
      const patientName = getDataValue(button, [
        'data-patient',
        'data-patient-name',
        'data-full-name',
        'data-name',
        'data-vpatient'
      ]);
      const referralDate = getDataValue(button, [
        'data-date',
        'data-referral-date',
        'data-created-at',
        'data-created',
        'data-vbdate'
      ]);
      const referFrom = getDataValue(button, [
        'data-from',
        'data-refer-from',
        'data-facility',
        'data-patient-facility'
      ]);
      const sex = getDataValue(button, [
        'data-sex',
        'data-patient-sex',
        'data-vsex'
      ]);
      const height = getDataValue(button, [
        'data-height',
        'data-patient-height'
      ]);
      const weight = getDataValue(button, [
        'data-weight',
        'data-patient-weight'
      ]);
      
      console.log('Data read:', { patientName, referralDate, referFrom, sex, height, weight });
      
      setFieldValue('#viewReferralPatientName', patientName);
      setFieldValue('#viewReferralDateField', referralDate);
      setFieldValue('#viewReferralFrom', referFrom);
      setFieldValue('#viewReferralSex', sex);
      setFieldValue('#viewReferralHeight', height);
      setFieldValue('#viewReferralWeight', weight);
      
      console.log('Fields populated. Checking if elements exist:', {
        patientName: $referralModal.find('#viewReferralPatientName').length,
        referralDate: $referralModal.find('#viewReferralDateField').length,
        referFrom: $referralModal.find('#viewReferralFrom').length,
        sex: $referralModal.find('#viewReferralSex').length,
        height: $referralModal.find('#viewReferralHeight').length,
        weight: $referralModal.find('#viewReferralWeight').length
      });
      setFieldValue('#viewTemperature', button.attr('data-temperature') || '');
      const systolic = button.attr('data-systolic');
      const diastolic = button.attr('data-diastolic');
      // Handle blood pressure - combine if separate, or use as-is if combined
      let bpValue = '';
      if (systolic && typeof systolic === 'string' && systolic.includes('/')) {
        // Already in format "systolic/diastolic"
        bpValue = systolic;
      } else if (systolic && diastolic) {
        bpValue = `${systolic}/${diastolic}`;
      } else if (systolic) {
        bpValue = systolic;
      }
      setFieldValue('#viewBpSystolic', bpValue, '');
      setFieldValue('#viewRespiratory', button.attr('data-respiratory') || button.data('respiratory') || '', '');
      // Try multiple ways to get pulse rate: data attribute, jQuery data, and various naming conventions
      const pulseRate = button.attr('data-pulserate') || 
                       button.data('pulserate') || 
                       button.attr('data-pulse-rate') || 
                       button.data('pulseRate') || 
                       button.attr('data-pulse') || 
                       button.data('pulse') || '';
      console.log('Pulse Rate from button:', {
        'data-pulserate attr': button.attr('data-pulserate'),
        'pulserate data': button.data('pulserate'),
        'data-pulse-rate attr': button.attr('data-pulse-rate'),
        'pulseRate data': button.data('pulseRate'),
        'final value': pulseRate
      });
      setFieldValue('#viewPulseRate', pulseRate, '');
      setFieldValue('#viewNotes', button.attr('data-notes') || button.attr('data-complaint') || '', '');
      setFieldValue('#viewSymptoms', button.attr('data-symptoms') || '', '');
      setFieldValue('#viewWorkUp', button.attr('data-workup') || '', '');
      setFieldValue('#viewdisease', button.attr('data-disease') || '', '');
      
      // MHO Actions Section - populate from saved data
      const mhoNote = button.attr('data-mho-note') || '';
      const mhoAdvice = button.attr('data-mho-advice') || '';
      const debugMhCount = button.attr('data-debug-mh-count') || '0';
      const debugMhNotesExists = button.attr('data-debug-mh-notes-exists') || 'NO';
      const debugMhAdviceExists = button.attr('data-debug-mh-advice-exists') || 'NO';
      const debugRemarks = button.attr('data-debug-remarks') || '';
      const debugTreatments = button.attr('data-debug-treatments') || '';
      
      console.log('🔍 DEBUG populateViewModal - MHO Data:');
      console.log('  Referral ID:', button.attr('data-id'));
      console.log('  Medical History Count:', debugMhCount);
      console.log('  medical_history_notes exists:', debugMhNotesExists);
      console.log('  medical_history_advice exists:', debugMhAdviceExists);
      console.log('  data-mho-note value:', mhoNote ? mhoNote.substring(0, 100) + '...' : 'EMPTY');
      console.log('  data-mho-advice value:', mhoAdvice ? mhoAdvice.substring(0, 100) + '...' : 'EMPTY');
      console.log('  Fallback remarks:', debugRemarks);
      console.log('  Fallback treatments:', debugTreatments);
      
      const findingsValue = (button.attr('data-mho-findings') || '').trim();
      setFieldValue('#viewMhoFindings', findingsValue, '');
      setFieldValue('#viewMhoNote', mhoNote, '');
      setFieldValue('#viewMhoAdvice', mhoAdvice, '');
      setFieldValue('#viewDiseaseSelect', button.attr('data-disease') || '', '');
      // Removed ICD Code field - replaced with Examined By
      const followup = button.attr('data-followup') || '';
      // Always set the followup field, even if empty, to clear previous values
      setFieldValue('#viewFollowup', followup, '');
      const examinedBy = button.attr('data-examined-by');
      if (examinedBy) {
        // Prioritize data attribute (most reliable)
        let doctorName = button.attr('data-examined-by-name');
        
        if (!doctorName || doctorName.trim() === '') {
          // Fallback: Get doctor name from the select option if available
          const examinedBySelect = $('#editExaminedBy option[value="' + examinedBy + '"]');
          if (examinedBySelect.length) {
            // Select option already has "Dr." prefix (see referral_modal.html line 791)
            doctorName = examinedBySelect.text().trim();
          } else {
            // Last fallback: use examined_by ID (shouldn't happen in normal flow)
            doctorName = examinedBy;
            // Add "Dr." prefix if not already present
            if (doctorName && !doctorName.toLowerCase().startsWith('dr.')) {
              doctorName = 'Dr. ' + doctorName;
            }
          }
        }
        
        setFieldValue('#viewExaminedBy', doctorName || '', '');
      } else {
        setFieldValue('#viewExaminedBy', '', '');
      }
      
      // Lifestyle/Social History fields - Always populate these
      const isSmokerAttr = button.attr('data-is-smoker');
      const isSmoker = isSmokerAttr === 'True';
      setCheckboxValue('#viewIsSmoker', isSmokerAttr);
      setFieldValue('#viewSmokingSticks', button.attr('data-smoking-sticks') || '', '');
      
      const isAlcoholicAttr = button.attr('data-is-alcoholic');
      const isAlcoholic = isAlcoholicAttr === 'True';
      setCheckboxValue('#viewIsAlcoholic', isAlcoholicAttr);
      setFieldValue('#viewAlcoholBottles', button.attr('data-alcohol-bottles') || '', '');
      
      const isFamilyPlanningAttr = button.attr('data-family-planning');
      const isFamilyPlanning = isFamilyPlanningAttr === 'True';
      setCheckboxValue('#viewFamilyPlanning', isFamilyPlanningAttr);
      setFieldValue('#viewFamilyPlanningType', button.attr('data-family-planning-type') || '', '');
      
      // Menstrual History fields - populate first
      // Read all values first to debug
      const menarche = button.attr('data-menarche');
      const numberOfPartners = button.attr('data-number-of-partners');
      const menopauseAge = button.attr('data-menopause-age');
      const periodDuration = button.attr('data-period-duration');
      const periodInterval = button.attr('data-period-interval');
      const padsPerDay = button.attr('data-pads-per-day');
      const lmp = button.attr('data-last-menstrual-period');
      
      console.log('Menstrual History - Raw data from button:', {
        menarche: menarche,
        numberOfPartners: numberOfPartners,
        menopauseAge: menopauseAge,
        periodDuration: periodDuration,
        periodInterval: periodInterval,
        padsPerDay: padsPerDay,
        lmp: lmp
      });
      
      // Set all fields consistently - use the value directly (even if empty) with empty string fallback
      setFieldValue('#viewMenarche', menarche !== undefined ? menarche : '', '');
      const sexuallyActive = button.attr('data-sexually-active');
      setCheckboxValue('#viewSexuallyActive', sexuallyActive);
      setFieldValue('#viewNumberOfPartners', numberOfPartners !== undefined ? numberOfPartners : '', '');
      const isMenopause = button.attr('data-is-menopause');
      setCheckboxValue('#viewIsMenopause', isMenopause);
      setFieldValue('#viewMenopauseAge', menopauseAge !== undefined ? menopauseAge : '', '');
      setFieldValue('#viewLastMenstrualPeriod', lmp !== undefined ? lmp : '', '');
      setFieldValue('#viewPeriodDuration', periodDuration !== undefined ? periodDuration : '', '');
      setFieldValue('#viewPeriodInterval', periodInterval !== undefined ? periodInterval : '', '');
      setFieldValue('#viewPadsPerDay', padsPerDay !== undefined ? padsPerDay : '', '');
      
      // Pregnancy History fields - populate first
      const isPregnant = button.attr('data-is-pregnant');
      setCheckboxValue('#viewIsPregnant', isPregnant);
      setFieldValue('#viewGravidity', button.attr('data-gravidity') || '', '');
      setFieldValue('#viewParity', button.attr('data-parity') || '', '');
      setFieldValue('#viewDeliveryType', button.attr('data-delivery-type') || '', '');
      setFieldValue('#viewFullTermBirths', button.attr('data-full-term-births') || '', '');
      setFieldValue('#viewPrematureBirths', button.attr('data-premature-births') || '', '');
      setFieldValue('#viewAbortions', button.attr('data-abortions') || '', '');
      setFieldValue('#viewLivingChildren', button.attr('data-living-children') || '', '');
      
      setFieldValue('#view-referral-id-input', button.attr('data-id') || '', '');
      
      // Ensure Lifestyle & Social History section is visible - search within modal
      const $lifestyleSection = $referralModal.find('.referral-section-card').filter(function() {
        return $(this).find('#viewIsSmoker, #viewIsAlcoholic').length > 0;
      });
      if ($lifestyleSection.length) {
        $lifestyleSection.show().removeClass('d-none');
        console.log('✅ Lifestyle section shown');
      } else {
        console.warn('⚠️ Lifestyle section not found in modal');
      }
      
      // Show/hide menstrual and pregnancy sections based on sex
      // Make sure sex is read correctly - try both attr and data methods
      const sexValue = button.attr('data-sex') || button.data('sex') || sex || '';
      console.log('View Modal - Sex value from button:', sexValue);
      
      // Find sections within the modal
      const $menstrualSection = $referralModal.find('#viewMenstrualHistorySection');
      const $pregnancySection = $referralModal.find('#viewPregnancyHistorySection');
      
      if (sexValue && sexValue.toString().toLowerCase().trim() === 'female') {
        if ($menstrualSection.length) {
          $menstrualSection.show().removeClass('d-none');
          console.log('✅ Menstrual section shown');
        } else {
          console.warn('⚠️ Menstrual section not found');
        }
        if ($pregnancySection.length) {
          $pregnancySection.show().removeClass('d-none');
          console.log('✅ Pregnancy section shown');
        } else {
          console.warn('⚠️ Pregnancy section not found');
        }
      } else {
        if ($menstrualSection.length) {
          $menstrualSection.hide();
        }
        if ($pregnancySection.length) {
          $pregnancySection.hide();
        }
        console.log('View Modal - Hiding Menstrual and Pregnancy sections (not female)');
      }
      
      // Debug: Log all data attributes to verify they're present
      console.log('View Modal - Lifestyle data:', {
        isSmoker: button.attr('data-is-smoker'),
        smokingSticks: button.attr('data-smoking-sticks'),
        isAlcoholic: button.attr('data-is-alcoholic'),
        alcoholBottles: button.attr('data-alcohol-bottles'),
        familyPlanning: button.attr('data-family-planning'),
        familyPlanningType: button.attr('data-family-planning-type')
      });
      console.log('View Modal - Menstrual data:', {
        menarche: button.attr('data-menarche'),
        sexuallyActive: button.attr('data-sexually-active'),
        numberOfPartners: button.attr('data-number-of-partners'),
        isMenopause: button.attr('data-is-menopause'),
        menopauseAge: button.attr('data-menopause-age'),
        lastMenstrualPeriod: button.attr('data-last-menstrual-period')
      });
      console.log('View Modal - Pregnancy data:', {
        isPregnant: button.attr('data-is-pregnant'),
        gravidity: button.attr('data-gravidity'),
        parity: button.attr('data-parity'),
        deliveryType: button.attr('data-delivery-type')
      });

      // Hide Referred button if status is completed
      const status = button.attr('data-status') || button.data('status') || '';
      const referralId = button.attr('data-id') || button.data('id') || '';
      
      // Hide "Doctor Notes & Actions" section if status is pending or in-progress
      // Only show it when referral is completed
      if (status === 'pending' || status === 'in-progress') {
        $("#viewDoctorNotesSection").hide();
      } else if (status === 'completed') {
        $("#viewDoctorNotesSection").show();
      } else {
        // Default: show for other statuses
        $("#viewDoctorNotesSection").show();
      }
      
      console.log('=== populateViewModal - Setting status and ID ===');
      console.log('Button element:', button[0]);
      console.log('Button attr data-status:', button.attr('data-status'));
      console.log('Button data status:', button.data('status'));
      console.log('Button attr data-id:', button.attr('data-id'));
      console.log('Button data id:', button.data('id'));
      console.log('Final status:', status);
      console.log('Final referralId:', referralId);
      
      // Set hidden fields for Accept button logic
      const statusField = $('#viewReferralStatus');
      const idField = $('#viewReferralId');
      
      console.log('Hidden fields found - Status field:', statusField.length, 'ID field:', idField.length);
      
      if (statusField.length) {
        statusField.val(status);
        console.log('✅ Status field set to:', statusField.val());
      } else {
        console.error('❌ viewReferralStatus field not found in DOM!');
        console.log('Modal body:', $('#viewReferralModal .modal-body').length);
        console.log('All hidden inputs in modal:', $('#viewReferralModal input[type="hidden"]').length);
      }
      
      if (idField.length) {
        idField.val(referralId);
        console.log('✅ ID field set to:', idField.val());
      } else {
        console.error('❌ viewReferralId field not found in DOM!');
      }
      
      // Also store as data attributes on the modal
      $('#viewReferralModal').data('referral-id', referralId);
      $('#viewReferralModal').data('referral-status', status);
      console.log('Modal data attributes set - ID:', $('#viewReferralModal').data('referral-id'), 'Status:', $('#viewReferralModal').data('referral-status'));
      console.log('=== populateViewModal status/ID setting end ===');
      
      const referredButton = $("#viewReferralModal .modal-footer form");
      if (status === "completed") {
        referredButton.hide();
      } else {
        referredButton.show();
      }
      
      // Trigger update for Accept button visibility after a short delay
      setTimeout(function() {
        // Try to call the global function first
        if (typeof window.updateAcceptButton === 'function') {
          window.updateAcceptButton();
        } else {
          // Fallback: manually show/hide the button
          const acceptBtn = $('#acceptReferralBtn');
          if (acceptBtn.length) {
            if (status === 'pending' && referralId) {
              acceptBtn.show();
              acceptBtn.attr('data-referral-id', referralId);
              console.log('Accept button shown for pending referral:', referralId);
            } else {
              acceptBtn.hide();
              console.log('Accept button hidden - status:', status, 'ID:', referralId);
            }
          } else {
            console.log('Accept button not found in DOM');
          }
        }
      }, 150);
    }
  }
}); 