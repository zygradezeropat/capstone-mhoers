// Modern Referral Modal JavaScript

(function() {
  'use strict';

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
    const referralId = $('#referral-id-edit-input').val();
    if (referralId) {
      // Small delay to ensure form is populated
      setTimeout(function() {
        loadDraft(referralId);
        setupAutoSave(referralId);
        setupValidation();
        updateVitalIndicators();
        updateFormProgress();
      }, 100);
    }
  });

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
  }

  // Update individual vital indicator
  function updateVitalIndicator(selector, value, range) {
    const $wrapper = $(selector).closest('.vital-sign-wrapper');
    if ($wrapper.length === 0) {
      // Create wrapper if it doesn't exist
      $(selector).wrap('<div class="vital-sign-wrapper"></div>');
      const $newWrapper = $(selector).closest('.vital-sign-wrapper');
      $newWrapper.append('<span class="vital-indicator"></span>');
    }
    
    const $indicator = $(selector).closest('.vital-sign-wrapper').find('.vital-indicator');
    const $input = $(selector);
    
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

})();

