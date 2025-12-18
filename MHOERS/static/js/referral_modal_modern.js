// Modern Referral Modal JavaScript

(function() {
  'use strict';
  
  // Wait for jQuery to be available
  function waitForJQuery(callback) {
    if (typeof jQuery !== 'undefined' && typeof $ !== 'undefined') {
      callback();
    } else {
      setTimeout(function() { waitForJQuery(callback); }, 50);
    }
  }
  
  // Initialize when jQuery is ready
  waitForJQuery(function() {
    var $ = window.jQuery || window.$;
    
    // Get CSRF token for AJAX requests
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
    
    // Set up CSRF token for all AJAX requests
    $.ajaxSetup({
      beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
          xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
      }
    });

    // Vital Signs Normal Ranges
    const VITAL_RANGES = {
    temperature: { min: 36.1, max: 37.2, unit: '°C' },
    bp_systolic: { min: 90, max: 120, unit: 'mmHg' },
    bp_diastolic: { min: 60, max: 80, unit: 'mmHg' },
    respiratory: { min: 12, max: 20, unit: '/min' },
    pulse: { min: 60, max: 100, unit: '/min' }
    };

    // Auto-save functionality
    let autoSaveTimer;
    const AUTO_SAVE_DELAY = 30000; // 30 seconds
    const DRAFT_STORAGE_KEY = 'referral_draft_';

    // Initialize when modal is shown
    $(document).on('shown.bs.modal', '#editReferralModal', function() {
    console.log('Edit referral modal opened');
    const referralId = $('#referral-id-edit-input').val();
    
    // Remove any vital indicator color classes from edit modal fields
    $('#editReferralModal .vital-sign-wrapper .form-control').removeClass('vital-normal vital-warning vital-critical');
    $('#editReferralModal .vital-indicator').hide();
    
    // Store original findings select HTML for transformation
    const $container = $('#editFindingsContainer');
    if ($container.length && !$container.data('original-html')) {
      $container.data('original-html', $container.html());
      console.log('Stored original findings HTML on modal open');
    }
    
    // Ensure event handler is attached when modal opens
    $(document).off('change', '#editFindingsSelect').on('change', '#editFindingsSelect', handleFindingsFieldChange);
    console.log('Attached findings change handler on modal open');
    
    // Check if prediction is "Unspecified" and show helper alert
    checkForUnspecifiedPrediction();
    
    // Always load diseases when modal opens
    setTimeout(function() {
      console.log('Loading diseases for modal...');
      loadAllDiseases();
      
      // Re-attach handler after diseases are loaded (in case select was replaced)
      setTimeout(function() {
        $(document).off('change', '#editFindingsSelect').on('change', '#editFindingsSelect', handleFindingsFieldChange);
        console.log('Re-attached findings change handler after disease load');
      }, 300);
    }, 200);
    
    if (referralId) {
      // Small delay to ensure form is populated
      setTimeout(function() {
        loadDraft(referralId);
        setupAutoSave(referralId);
        setupValidation();
        updateVitalIndicators();
        updateFormProgress();
        // Check again after form is populated
        checkForUnspecifiedPrediction();
        
        // Populate findings field if data is pending
        if (window.pendingFindingsData) {
          const findingsData = window.pendingFindingsData;
          const $findingsContainer = $('#editFindingsContainer');
          const $hiddenFindings = $('#editMhoFindings');
          
          if (findingsData.diseaseId) {
            // Disease from database - select it in dropdown
            const $select = $('#editFindingsSelect');
            if ($select.length) {
              $select.val(findingsData.diseaseId);
              // Trigger change to load disease details and set hidden field
              $select.trigger('change');
            }
          } else if (findingsData.finalDiagnosis && findingsData.finalDiagnosis.trim()) {
            // Custom findings - transform to input
            const originalHTML = $findingsContainer.data('original-html') || $findingsContainer.html();
            if (!$findingsContainer.data('original-html')) {
              $findingsContainer.data('original-html', originalHTML);
            }
            
            // Transform to input
            $findingsContainer.html(
              '<input type="text" class="form-control" id="editFindingsInput" name="findings_other" placeholder="Enter findings manually..." required>'
            );
            
            // Set the value
            const $input = $('#editFindingsInput');
            $input.val(findingsData.finalDiagnosis);
            $hiddenFindings.val(findingsData.finalDiagnosis);
            
            // Attach input handler
            $input.on('input', function() {
              $hiddenFindings.val($(this).val());
            });
          }
          
          // Clear pending data
          window.pendingFindingsData = null;
        }
      }, 200);
    }
  });
  
    // Clean up when modal is hidden - restore original state
    $(document).on('hidden.bs.modal', '#editReferralModal', function() {
    const $container = $('#editFindingsContainer');
    const originalHTML = $container.data('original-html');
    if (originalHTML && $('#editFindingsInput').length) {
      // Restore dropdown if it was transformed
      $container.html(originalHTML);
    }
  });
  
    // Function to check if prediction is "Unspecified" and show alert
    function checkForUnspecifiedPrediction() {
        let isUnspecified = false;
        
        // Check if stored flag from edit button click
        const storedFlag = $('#referral-id-edit-input').data('unspecified-prediction');
        if (storedFlag === true) {
            isUnspecified = true;
        }
        
        // Also check if the edit button that opened the modal has "Unspecified" in data-disease
        const referralId = $('#referral-id-edit-input').val();
        if (referralId) {
            const editButton = $('.edit-button').filter(function() {
                return $(this).data('id') === referralId || $(this).attr('data-id') === referralId;
            });
            
            if (editButton.length > 0) {
                const prediction = editButton.attr('data-disease') || '';
                if (prediction && (prediction.includes('Unspecified') || prediction.includes('No prediction available'))) {
                    isUnspecified = true;
                }
            }
        }
        
        // Also check if ICD code field shows "Unspecified"
        const icdCodeValue = $('#editIcdCode').val() || '';
        if (icdCodeValue && icdCodeValue.includes('Unspecified')) {
            isUnspecified = true;
        }
        
        // Show or hide the alert
        if (isUnspecified) {
            $('#unspecifiedPredictionAlert').slideDown(300);
        } else {
            $('#unspecifiedPredictionAlert').slideUp(300);
        }
    }

  // Also update vitals when edit button is clicked (before modal shows)
  $(document).on('click', '.edit-button', function() {
    // Update vitals after a short delay to allow form population
    setTimeout(function() {
      updateVitalIndicators();
    }, 200);
  });

  // Handle conditional enabling of lifestyle fields
  $(document).on('change', '#editIsSmoker', function() {
    $('#editSmokingSticks').prop('disabled', !$(this).is(':checked'));
    if (!$(this).is(':checked')) {
      $('#editSmokingSticks').val('');
    }
  });

  $(document).on('change', '#editIsAlcoholic', function() {
    $('#editAlcoholBottles').prop('disabled', !$(this).is(':checked'));
    if (!$(this).is(':checked')) {
      $('#editAlcoholBottles').val('');
    }
  });

  $(document).on('change', '#editFamilyPlanning', function() {
    $('#editFamilyPlanningType').prop('disabled', !$(this).is(':checked'));
    if (!$(this).is(':checked')) {
      $('#editFamilyPlanningType').val('');
    }
  });

  // Clean up when modal is hidden
  $(document).on('hidden.bs.modal', '#editReferralModal', function() {
    clearAutoSaveTimer();
  });

  // Load draft from localStorage
  function loadDraft(referralId) {
    const draftKey = DRAFT_STORAGE_KEY + referralId;
    const draft = localStorage.getItem(draftKey);
    
    if (draft) {
      try {
        const data = JSON.parse(draft);
        $('#editMhoFindings').val(data.findings || '');
        $('#editMhoNote').val(data.note || '');
        $('#editMhoAdvice').val(data.advice || '');
        $('#editFollowup').val(data.followup || '');
        
        showAutoSaveIndicator('Draft restored', 'success');
      } catch (e) {
        console.error('Error loading draft:', e);
      }
    }
  }

  // Setup auto-save
  function setupAutoSave(referralId) {
    const formFields = ['#editMhoFindings', '#editMhoNote', '#editMhoAdvice', '#editFollowup'];
    
    formFields.forEach(field => {
      $(field).on('input', function() {
        clearAutoSaveTimer();
        showAutoSaveIndicator('Saving...', 'saving');
        
        autoSaveTimer = setTimeout(() => {
          saveDraft(referralId);
        }, AUTO_SAVE_DELAY);
      });
    });
  }

  // Save draft to localStorage
  function saveDraft(referralId) {
    const draftKey = DRAFT_STORAGE_KEY + referralId;
    const draft = {
      findings: $('#editMhoFindings').val(),
      note: $('#editMhoNote').val(),
      advice: $('#editMhoAdvice').val(),
      followup: $('#editFollowup').val(),
      timestamp: new Date().toISOString()
    };
    
    try {
      localStorage.setItem(draftKey, JSON.stringify(draft));
      showAutoSaveIndicator('Draft saved', 'success');
    } catch (e) {
      console.error('Error saving draft:', e);
      showAutoSaveIndicator('Save failed', 'error');
    }
  }

  // Clear draft after successful submission
  function clearDraft(referralId) {
    const draftKey = DRAFT_STORAGE_KEY + referralId;
    localStorage.removeItem(draftKey);
  }

  // Show auto-save indicator
  function showAutoSaveIndicator(message, type) {
    let indicator = $('#auto-save-indicator');
    
    if (indicator.length === 0) {
      indicator = $('<div id="auto-save-indicator" class="auto-save-indicator"></div>');
      $('body').append(indicator);
    }
    
    indicator.removeClass('saving error').addClass(type);
    indicator.html(`<i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'hourglass-split'}"></i> ${message}`);
    indicator.addClass('show');
    
    if (type === 'success') {
      setTimeout(() => {
        indicator.removeClass('show');
      }, 2000);
    }
  }

  // Clear auto-save timer
  function clearAutoSaveTimer() {
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
      autoSaveTimer = null;
    }
  }

  // Setup form validation
  function setupValidation() {
    // Real-time validation for textareas
    $('#editMhoFindings, #editMhoNote, #editMhoAdvice').on('blur', function() {
      validateField($(this));
    });

    // Validate follow-up date
    $('#editFollowup').on('change', function() {
      validateDateField($(this));
    });

    // Validate on form submit
    $('#editReferralForm').on('submit', function(e) {
      if (!validateForm()) {
        e.preventDefault();
        return false;
      }
      
      // Clear draft on successful submission
      const referralId = $('#referral-id-edit-input').val();
      if (referralId) {
        clearDraft(referralId);
      }
    });
  }

  // Validate individual field
  function validateField($field) {
    const value = $field.val().trim();
    const minLength = 3;
    
    $field.removeClass('is-valid is-invalid');
    $field.next('.invalid-feedback').remove();
    
    if (value.length > 0 && value.length < minLength) {
      $field.addClass('is-invalid');
      $field.after(`<div class="invalid-feedback">Please enter at least ${minLength} characters</div>`);
      return false;
    } else if (value.length >= minLength) {
      $field.addClass('is-valid');
      return true;
    }
    
    return true; // Empty is valid (optional fields)
  }

  // Validate date field
  function validateDateField($field) {
    const value = $field.val();
    
    $field.removeClass('is-valid is-invalid');
    $field.next('.invalid-feedback').remove();
    
    if (value) {
      const selectedDate = new Date(value);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (selectedDate < today) {
        $field.addClass('is-invalid');
        $field.after('<div class="invalid-feedback">Follow-up date cannot be in the past</div>');
        return false;
      } else {
        $field.addClass('is-valid');
        return true;
      }
    }
    
    return true; // Empty is valid (optional field)
  }

  // Validate entire form
  function validateForm() {
    let isValid = true;
    
    // Validate all textareas
    $('#editMhoFindings, #editMhoNote, #editMhoAdvice').each(function() {
      if (!validateField($(this))) {
        isValid = false;
      }
    });
    
    // Validate follow-up date
    if (!validateDateField($('#editFollowup'))) {
      isValid = false;
    }
    
    if (!isValid) {
      showAutoSaveIndicator('Please fix errors before submitting', 'error');
      // Scroll to first error
      $('.is-invalid').first().focus();
    }
    
    return isValid;
  }

  // Update vital signs indicators
  function updateVitalIndicators() {
    // Temperature
    const temp = parseFloat($('#editTemperature').val());
    if (!isNaN(temp)) {
      updateVitalIndicator('#editTemperature', temp, VITAL_RANGES.temperature);
    }

    // Blood Pressure
    const bpText = $('#editBpSystolic').val();
    if (bpText) {
      const bpMatch = bpText.match(/(\d+)\/(\d+)/);
      if (bpMatch) {
        const systolic = parseInt(bpMatch[1]);
        const diastolic = parseInt(bpMatch[2]);
        updateVitalIndicator('#editBpSystolic', systolic, VITAL_RANGES.bp_systolic);
        // Could add separate indicator for diastolic if needed
      }
    }

    // Respiratory Rate
    const resp = parseInt($('#editRespiratory').val());
    if (!isNaN(resp)) {
      updateVitalIndicator('#editRespiratory', resp, VITAL_RANGES.respiratory);
    }

    // Pulse Rate
    const pulse = parseInt($('#editPulseRate').val());
    if (!isNaN(pulse)) {
      updateVitalIndicator('#editPulseRate', pulse, VITAL_RANGES.pulse);
    }
  }

  // Update individual vital indicator
  function updateVitalIndicator(selector, value, range) {
    // Disable vital indicator colors in edit modal
    const $input = $(selector);
    if ($input.closest('#editReferralModal').length > 0) {
      // Remove any existing vital classes from edit modal inputs
      $input.removeClass('vital-normal vital-warning vital-critical');
      return;
    }
    
    const $wrapper = $(selector).closest('.vital-sign-wrapper');
    if ($wrapper.length === 0) {
      // Create wrapper if it doesn't exist
      $(selector).wrap('<div class="vital-sign-wrapper"></div>');
      const $newWrapper = $(selector).closest('.vital-sign-wrapper');
      $newWrapper.append('<span class="vital-indicator"></span>');
    }
    
    const $indicator = $(selector).closest('.vital-sign-wrapper').find('.vital-indicator');
    
    let status = 'normal';
    if (value < range.min || value > range.max) {
      // Check if critical or warning
      const deviation = Math.max(
        Math.abs(value - range.min),
        Math.abs(value - range.max)
      );
      const rangeSize = range.max - range.min;
      
      if (deviation > rangeSize * 0.5) {
        status = 'critical';
      } else {
        status = 'warning';
      }
    }
    
    // Update classes
    $indicator.removeClass('vital-normal vital-warning vital-critical')
              .addClass('vital-' + status);
    $input.removeClass('vital-normal vital-warning vital-critical')
          .addClass('vital-' + status);
  }

  // Calculate form completion progress
  function updateFormProgress() {
    const fields = ['#editMhoFindings', '#editMhoNote', '#editMhoAdvice', '#editFollowup'];
    let filledCount = 0;
    
    fields.forEach(field => {
      const value = $(field).val().trim();
      if (value.length > 0) {
        filledCount++;
      }
    });
    
    const progress = (filledCount / fields.length) * 100;
    $('.form-progress-bar').css('width', progress + '%');
  }

  // Initialize progress tracking
  $('#editMhoFindings, #editMhoNote, #editMhoAdvice, #editFollowup').on('input', function() {
    updateFormProgress();
  });

  // Keyboard shortcuts
  $(document).on('keydown', '#editReferralModal', function(e) {
    // Ctrl+S or Cmd+S to save draft
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      const referralId = $('#referral-id-edit-input').val();
      if (referralId) {
        saveDraft(referralId);
      }
    }
    
    // Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      $('#editReferralForm').submit();
    }
  });

  // Show loading state on submit
  $('#editReferralForm').on('submit', function() {
    const $submitBtn = $(this).find('button[type="submit"]');
    $submitBtn.addClass('btn-loading');
  });

  // ============================================
  // Disease Database Integration
  // ============================================
  let diseaseSearchTimeout;
  
  // Load all diseases when modal opens (only if dropdown is empty)
  function loadAllDiseases() {
    console.log('Checking diseases in dropdown...');
    // Check both old and new select elements
    const select = $('#editDiseaseSelect');
    const findingsSelect = $('#editFindingsSelect');
    
    // Use new findings select if it exists, otherwise fall back to old one
    const targetSelect = findingsSelect.length > 0 ? findingsSelect : select;
    
    // Check if select exists
    if (targetSelect.length === 0) {
      console.error('Disease select element not found!');
      return;
    }
    
    // If dropdown already has options (populated from template), don't reload
    if (targetSelect.find('option').length > 2) { // More than "Select" and "Other"
      console.log('Diseases already populated from template, skipping AJAX load');
      return;
    }
    
    // Otherwise, load via AJAX as fallback
    console.log('Loading diseases via AJAX...');
    $.ajax({
      url: '/referrals/api/search-diseases/',
      method: 'GET',
      data: { q: '' }, // Empty query to get all diseases
      success: function(response) {
        console.log('Diseases loaded:', response);
        // Remove "Other" option temporarily, will add it back
        const otherOption = targetSelect.find('option[value="other"]');
        targetSelect.empty().append('<option value="">Select Findings</option>');
        
        if (response.diseases && response.diseases.length > 0) {
          console.log('Found ' + response.diseases.length + ' diseases');
          response.diseases.forEach(function(disease) {
            targetSelect.append(
              $('<option></option>')
                .attr('value', disease.id)
                .attr('data-icd', disease.icd_code)
                .attr('data-symptoms', disease.common_symptoms || '')
                .attr('data-treatment', disease.treatment_protocol || '')
                .attr('data-guidelines', disease.treatment_guidelines || '')
                .text(disease.name + ' (' + disease.icd_code + ')')
            );
          });
        } else {
          console.warn('No diseases found in response');
          targetSelect.append('<option value="">No diseases in database</option>');
        }
        
        // Add "Other" option back at the end
        targetSelect.append('<option value="other">Other</option>');
        
        // Ensure event handler is attached after AJAX load
        if (targetSelect.attr('id') === 'editFindingsSelect') {
          console.log('Re-attaching change handler after AJAX load');
          // Event delegation should still work, but ensure it's set
          $(document).off('change', '#editFindingsSelect').on('change', '#editFindingsSelect', handleFindingsFieldChange);
        }
      },
      error: function(xhr, status, error) {
        console.error('Error loading diseases:', error);
        console.error('Status:', status);
        console.error('Response:', xhr.responseText);
        targetSelect.empty().append('<option value="">Error loading diseases - Check console</option>');
        targetSelect.append('<option value="other">Other</option>');
        
        // Ensure event handler is attached after error
        if (targetSelect.attr('id') === 'editFindingsSelect') {
          $(document).off('change', '#editFindingsSelect').on('change', '#editFindingsSelect', handleFindingsFieldChange);
        }
      }
    });
  }
  
  // Disease search functionality
  $('#searchDiseaseBtn').on('click', function() {
    const query = $('#editIcdCode').val() || prompt('Enter disease name or ICD code:');
    if (query) {
      searchDiseases(query);
    } else {
      // If no query, reload all diseases
      loadAllDiseases();
    }
  });
  
  // Auto-search when ICD code is entered
  $('#editIcdCode').on('input', function() {
    const query = $(this).val();
    if (query.length >= 3) {
      clearTimeout(diseaseSearchTimeout);
      diseaseSearchTimeout = setTimeout(() => {
        searchDiseases(query);
      }, 500);
    } else if (query.length === 0) {
      // If cleared, reload all diseases
      loadAllDiseases();
    }
  });
  
  // Disease selection change (old - keep for backward compatibility if needed)
  $('#editDiseaseSelect').on('change', function() {
    const diseaseId = $(this).val();
    if (diseaseId) {
      loadDiseaseDetails(diseaseId);
    } else {
      $('#diseaseVerificationPanel').hide();
    }
  });
  
  // Function to handle findings field transformation
  function handleFindingsFieldChange() {
    console.log('handleFindingsFieldChange called');
    const selectedValue = $('#editFindingsSelect').val();
    console.log('Selected value:', selectedValue);
    const $container = $('#editFindingsContainer');
    const $hiddenFindings = $('#editMhoFindings');
    
    if (!$container.length) {
      console.error('editFindingsContainer not found!');
      return;
    }
    
    if (selectedValue === 'other') {
      console.log('Transforming to input field');
      // Transform dropdown to input field
      // Store original HTML if not already stored
      if (!$container.data('original-html')) {
        $container.data('original-html', $container.html());
        console.log('Stored original HTML');
      }
      
      // Get current value if input already exists (in case user switches back and forth)
      const currentInputValue = $('#editFindingsInput').val() || '';
      
      // Replace select with input
      $container.html(
        '<input type="text" class="form-control" id="editFindingsInput" name="findings_other" placeholder="Enter findings manually..." required autofocus>'
      );
      console.log('Replaced with input field');
      
      // Set value if it existed
      if (currentInputValue) {
        $('#editFindingsInput').val(currentInputValue);
      }
      
      // Focus on the new input
      setTimeout(function() {
        $('#editFindingsInput').focus();
      }, 100);
      
      // Update hidden field when input changes
      $(document).off('input', '#editFindingsInput').on('input', '#editFindingsInput', function() {
        const inputValue = $(this).val();
        $hiddenFindings.val(inputValue);
      });
      
      // Set initial hidden field value
      $hiddenFindings.val(currentInputValue || '');
      
      // Hide disease verification panel
      $('#diseaseVerificationPanel').hide();
    } else if (selectedValue && selectedValue !== '') {
      console.log('Disease selected:', selectedValue);
      // Disease selected - restore dropdown if it was transformed
      const originalHTML = $container.data('original-html');
      if (originalHTML && $('#editFindingsInput').length) {
        console.log('Restoring dropdown from input');
        $container.html(originalHTML);
        // Re-select the disease
        $('#editFindingsSelect').val(selectedValue);
        // Re-attach change handler using event delegation
        $(document).off('change', '#editFindingsSelect').on('change', '#editFindingsSelect', handleFindingsFieldChange);
      }
      
      // Get disease name and set it to hidden findings field
      const selectedOption = $('#editFindingsSelect option:selected');
      if (selectedOption.length) {
        const diseaseName = selectedOption.text().split(' (')[0]; // Get name without ICD code
        $hiddenFindings.val(diseaseName);
      }
      
      // Load disease details for verification panel
      loadDiseaseDetails(selectedValue);
    } else {
      console.log('Nothing selected');
      // Nothing selected - restore dropdown if it was transformed
      const originalHTML = $container.data('original-html');
      if (originalHTML && $('#editFindingsInput').length) {
        console.log('Restoring dropdown (empty selection)');
        $container.html(originalHTML);
        // Re-attach change handler using event delegation
        $(document).off('change', '#editFindingsSelect').on('change', '#editFindingsSelect', handleFindingsFieldChange);
      }
      
      $hiddenFindings.val('');
      $('#diseaseVerificationPanel').hide();
    }
  }
  
  // New Findings dropdown with "Other" option - transforms to input
  // Use event delegation to ensure it works even if element is dynamically added
  $(document).on('change', '#editFindingsSelect', handleFindingsFieldChange);
  
  // Update hidden findings field when "Other" input changes (using event delegation)
  $(document).on('input', '#editFindingsInput', function() {
    const inputValue = $(this).val();
    $('#editMhoFindings').val(inputValue);
  });
  
  // Before form submission, ensure hidden field is populated
  $('#editReferralForm').on('submit', function(e) {
    const $findingsSelect = $('#editFindingsSelect');
    const $findingsInput = $('#editFindingsInput');
    const $hiddenFindings = $('#editMhoFindings');
    
    // Check if we're in "Other" mode (input exists) or dropdown mode (select exists)
    if ($findingsInput.length && $findingsInput.is(':visible')) {
      // "Other" mode - use input value
      const inputValue = $findingsInput.val();
      if (inputValue && inputValue.trim()) {
        $hiddenFindings.val(inputValue.trim());
      } else {
        e.preventDefault();
        alert('Please enter findings.');
        $findingsInput.focus();
        return false;
      }
    } else if ($findingsSelect.length && $findingsSelect.val() && $findingsSelect.val() !== '') {
      // Disease selected - ensure hidden field has disease name
      const selectedOption = $findingsSelect.find('option:selected');
      const diseaseName = selectedOption.text().split(' (')[0];
      $hiddenFindings.val(diseaseName);
    } else {
      // Nothing selected
      e.preventDefault();
      alert('Please select findings or enter custom findings.');
      return false;
    }
  });
  
  function searchDiseases(query) {
    $.ajax({
      url: '/referrals/api/search-diseases/',
      method: 'GET',
      data: { q: query },
      success: function(response) {
        const select = $('#editDiseaseSelect');
        select.empty().append('<option value="">-- Select Disease --</option>');
        
        if (response.diseases && response.diseases.length > 0) {
          response.diseases.forEach(function(disease) {
            select.append(
              $('<option></option>')
                .attr('value', disease.id)
                .attr('data-icd', disease.icd_code)
                .attr('data-symptoms', disease.common_symptoms || '')
                .attr('data-treatment', disease.treatment_protocol || '')
                .attr('data-guidelines', disease.treatment_guidelines || '')
                .text(disease.name + ' (' + disease.icd_code + ')')
            );
          });
        } else {
          select.append('<option value="">No diseases found</option>');
        }
      },
      error: function(xhr, status, error) {
        console.error('Error searching diseases:', error);
        const select = $('#editDiseaseSelect');
        select.empty().append('<option value="">Error searching diseases</option>');
      }
    });
  }
  
  function loadDiseaseDetails(diseaseId) {
    // Check both old and new select elements
    const oldSelect = $('#editDiseaseSelect');
    const newSelect = $('#editFindingsSelect');
    const targetSelect = newSelect.length > 0 ? newSelect : oldSelect;
    
    const selectedOption = targetSelect.find('option:selected');
    const icdCode = selectedOption.attr('data-icd');
    const symptoms = selectedOption.attr('data-symptoms');
    const treatment = selectedOption.attr('data-treatment');
    const guidelines = selectedOption.attr('data-guidelines');
    
    // If we have data attributes from template, use them first
    if (icdCode && (symptoms || treatment || guidelines)) {
      // Populate ICD code
      $('#editIcdCode').val(icdCode);
      
      // Show verification panel with data from template
      $('#diseaseSymptoms').text(symptoms || 'Not specified');
      $('#diseaseTreatment').text(treatment || 'Not specified');
      $('#diseaseGuidelines').text(guidelines || 'Not specified');
      $('#diseaseVerificationPanel').show();
      
      // Default to warning (we don't have verification info from template)
      const panelHeader = $('#diseaseVerificationPanel .card-header');
      panelHeader
        .removeClass('bg-success')
        .addClass('bg-warning')
        .html('<i class="bi bi-exclamation-triangle"></i> Disease Information (Verification status unknown)');
      
      // Optionally fetch full details including verification info via AJAX
      $.ajax({
        url: '/referrals/api/disease/' + diseaseId + '/',
        method: 'GET',
        success: function(disease) {
          // Update verification status if available
          const panelHeader = $('#diseaseVerificationPanel .card-header');
          if (!disease.verified_by || disease.verified_by === 'Not verified') {
            panelHeader
              .removeClass('bg-success')
              .addClass('bg-warning')
              .html('<i class="bi bi-exclamation-triangle"></i> Disease Not Yet Verified by Doctor');
          } else {
            panelHeader
              .removeClass('bg-warning')
              .addClass('bg-success')
              .html('<i class="bi bi-check-circle"></i> Verified Disease Information');
          }
        },
        error: function() {
          // Keep the default warning state if AJAX fails
          console.log('Could not fetch verification status, using default');
        }
      });
    } else {
      // Fallback to AJAX if data attributes are not available
      $.ajax({
        url: '/referrals/api/disease/' + diseaseId + '/',
        method: 'GET',
        success: function(disease) {
          // Populate ICD code
          $('#editIcdCode').val(disease.icd_code);
          
          // Show verification panel
          $('#diseaseSymptoms').text(disease.common_symptoms);
          $('#diseaseTreatment').text(disease.treatment_protocol);
          $('#diseaseGuidelines').text(disease.treatment_guidelines);
          $('#diseaseVerificationPanel').show();
          
          // Highlight that verification is recommended
          const panelHeader = $('#diseaseVerificationPanel .card-header');
          if (!disease.verified_by || disease.verified_by === 'Not verified') {
            panelHeader
              .removeClass('bg-success')
              .addClass('bg-warning')
              .html('<i class="bi bi-exclamation-triangle"></i> Disease Not Yet Verified by Doctor');
          } else {
            panelHeader
              .removeClass('bg-warning')
              .addClass('bg-success')
              .html('<i class="bi bi-check-circle"></i> Verified Disease Information');
          }
        },
        error: function() {
          console.error('Error loading disease details');
        }
      });
    }
  }
  
  }); // End of waitForJQuery callback

})();

