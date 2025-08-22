// Wait for the DOM to be fully loaded before executing any code
document.addEventListener('DOMContentLoaded', function() {
    // Get references to important DOM elements
    const searchForm = document.getElementById('patientSearchForm');
    const searchInput = document.getElementById('patientSearchInput');
    const searchResults = document.getElementById('searchResults');
    const searchResultsBody = document.getElementById('searchResultsBody');
    const noResults = document.getElementById('noResults');
    const patientCards = document.querySelector('.row:last-child'); // Get the row containing the cards
    const dateFilterSection = document.getElementById('dateFilterSection');
    const dateFilter = document.getElementById('dateFilter');

    // Hide cards initially when page loads
    if (patientCards) {
        patientCards.style.display = 'none';
    }

    // Function to get CSRF token from cookies (required for Django POST requests)
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

    // Function to update all cards with patient data
    function updatePatientDetails(patient, selectedDate = '') {
        try {
            // Check if there are any visit dates (completed referrals)
            if (!patient.visit_dates || patient.visit_dates.length === 0) {
                // Hide the cards and date filter section
                if (patientCards) {
                    patientCards.style.display = 'none';
                }
                if (dateFilterSection) {
                    dateFilterSection.style.display = 'none';
                }
                
                // Show "No data available" message
                const noDataMessage = document.getElementById('noDataAvailable');
                if (noDataMessage) {
                    noDataMessage.style.display = 'block';
                } else {
                    // Create and show a no data message if it doesn't exist
                    const messageDiv = document.createElement('div');
                    messageDiv.id = 'noDataAvailable';
                    messageDiv.className = 'alert alert-info text-center mt-3';
                    messageDiv.innerHTML = '<i class="bi bi-info-circle me-2"></i>No data available for this patient';
                    
                    // Insert the message after the search results
                    const searchResultsContainer = searchResults.parentElement;
                    if (searchResultsContainer) {
                        searchResultsContainer.appendChild(messageDiv);
                    }
                }
                return;
            }

            // Show the cards and date filter section
            if (patientCards) {
                patientCards.style.display = 'flex';
            }
            if (dateFilterSection) {
                dateFilterSection.style.display = 'block';
            }
            
            // Hide any existing no data message
            const noDataMessage = document.getElementById('noDataAvailable');
            if (noDataMessage) {
                noDataMessage.style.display = 'none';
            }

            // Update date filter dropdown with available visit dates
            if (patient.visit_dates && patient.visit_dates.length > 0) {
                dateFilter.innerHTML =
                    patient.visit_dates.map(date => {
                        // Format date to be more readable (e.g., "January 1, 2024")
                        const formattedDate = new Date(date).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                        });
                        // Mark the currently selected date as selected in the dropdown
                        const isSelected = date === selectedDate ? 'selected' : '';
                        return `<option value="${date}" ${isSelected}>${formattedDate}</option>`;
                    }).join('');
            } else {
                dateFilter.innerHTML = '<option value="">No visit dates available</option>';
            }

            // Update Subjective Card (Chief Complaint and Symptoms)
            const subjectiveCard = document.querySelector('.card-header.bg-primary').nextElementSibling;
            if (subjectiveCard) {
                const chiefComplaint = subjectiveCard.querySelector('h6:first-of-type').nextElementSibling;
                const symptoms = subjectiveCard.querySelector('h6:nth-of-type(2)').nextElementSibling;
               
                if (chiefComplaint) {
                    chiefComplaint.textContent = patient.chief_complaint || 'No chief complaint recorded';
                }
                
                if (symptoms) {
                    symptoms.textContent = patient.symptoms || 'No symptoms recorded';
                }
            }

            // Update Objective Card (Vital Signs and Work Up Details)
            const objectiveCard = document.querySelector('.card-header.bg-info').nextElementSibling;
            if (objectiveCard && patient.vital_signs) {
                const vitalSignsList = objectiveCard.querySelector('ul');
                if (vitalSignsList) {
                  vitalSignsList.innerHTML = `
                      <li>BP: <strong>${
                        patient.vital_signs.bp || "N/A"
                      }</strong></li>
                      <li>HR: <strong>${
                        patient.vital_signs.hr || "N/A"
                      }</strong></li>
                      <li>TEMP: <strong>${
                        patient.vital_signs.temp || "N/A"
                      }</strong></li>
                      <li>O2 SAT: <strong>${
                        patient.vital_signs.o2_sat || "N/A"
                      }</strong></li>
                      <li>RR: <strong>${
                        patient.vital_signs.resp_rate || "N/A"
                      }</strong></li>
                      <li>Weight: <strong>${
                        patient.vital_signs.weight || "N/A"
                      } kg</strong></li>
                      <li>Height: <strong>${
                        patient.vital_signs.height || "N/A"
                      } cm</strong></li>
                    `;
                }
                  

            }

            // Update Assessment Card
            const assessmentCard = document.querySelector('.card-header.bg-warning').nextElementSibling;
            if (assessmentCard) {
                const diagnosis = assessmentCard.querySelector('p:first-of-type');
                if (diagnosis) {
                    diagnosis.innerHTML = `<strong>${patient.work_up_details || 'No assessment recorded'}</strong>`;
                }
            }

            // Update Plan Card (Medication and Advice)
            const planCard = document.querySelector('.card-header.bg-success').nextElementSibling;
            if (planCard) {
                const medication = planCard.querySelector('h6:first-of-type').nextElementSibling;
                const advice = planCard.querySelector('h6:nth-of-type(2)').nextElementSibling;
                
                if (medication) {
                    if (patient.medical_history_note) {
                        medication.innerHTML = `<strong>${patient.medical_history_note}</strong>`;
                    } else {
                        medication.innerHTML = '<strong>No medication recorded</strong>';
                    }
                }
                
                if (advice) {
                    advice.textContent =
                      patient.medical_history_advice || "No advice recorded";
                }
            }
        } catch (error) {
            console.error('Error updating patient details:', error);
            alert('Error updating patient details. Please try again.');
        }
    }

    // Function to fetch patient details from the server
    function fetchPatientDetails(patientId, selectedDate = '') {
        console.log('Fetching details for patient:', patientId, 'Date:', selectedDate);
        
        // Construct URL with optional date parameter
        let url = `/patients/api/patient/${patientId}/`;
        if (selectedDate) {
            url += `?date=${selectedDate}`;
        }
        
        // Make API request to get patient details
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Network response was not ok');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Received patient data:', data);
            if (data.error) {
                throw new Error(data.error);
            }
            // Update the UI with the received patient data
            updatePatientDetails(data, selectedDate);
        })
        .catch(error => {
            console.error('Error fetching patient details:', error);
            alert(`Error loading patient details: ${error.message}`);
        });
    }

    // Add event listener for date filter changes
    if (dateFilter) {
        dateFilter.addEventListener('change', function() {
            const selectedPatientId = this.dataset.patientId;
            if (selectedPatientId) {
                // When date is changed, fetch patient details for the selected date
                fetchPatientDetails(selectedPatientId, this.value);
            }
        });
    }

    // Handle patient search form submission
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const searchTerm = searchInput.value.trim();
        
        if (searchTerm) {
            // Hide cards and date filter when searching
            if (patientCards) {
                patientCards.style.display = 'none';
            }
            if (dateFilterSection) {
                dateFilterSection.style.display = 'none';
            }

            // Show loading state
            searchResultsBody.innerHTML = '<tr><td colspan="2" class="text-center">Searching...</td></tr>';
            searchResults.style.display = 'block';
            noResults.style.display = 'none';

            // Make API request to search for patients
            fetch(`/patients/api/patients/search/?q=${encodeURIComponent(searchTerm)}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                if (data.patients && data.patients.length > 0) {
                    // Display search results
                    searchResultsBody.innerHTML = data.patients.map(patient => `
                        <tr data-id="${patient.patients_id}" class="align-middle patient-row" style="cursor: pointer;">
                            <td>
                                <div class="d-flex align-items-center">
                                    <div class="avatar-circle bg-primary-soft me-3">
                                        <i class="bi bi-person-circle text-primary fs-4"></i>
                                    </div>
                                    <div>
                                        <h6 class="mb-1 text-dark">${patient.first_name} ${patient.middle_name} ${patient.last_name}</h6>
                                        <span class="badge badge-pill badge-light">ID: #${patient.patients_id}</span>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    `).join('');
                    searchResults.style.display = 'block';
                    noResults.style.display = 'none';
                } else {
                    // Show no results message
                    searchResults.style.display = 'none';
                    noResults.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error searching patients:', error);
                searchResultsBody.innerHTML = `<tr><td colspan="2" class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${error.message || 'Error searching patients. Please try again.'}
                </td></tr>`;
                searchResults.style.display = 'block';
                noResults.style.display = 'none';
            });
        }
    });

    // Add event delegation for patient row clicks
    searchResultsBody.addEventListener('click', function(e) {
        const row = e.target.closest('.patient-row');
        if (row) {
            const patientId = row.dataset.id;
            // Store the selected patient ID in the date filter
            if (dateFilter) {
                dateFilter.dataset.patientId = patientId;
            }
            // Fetch and display patient details
            fetchPatientDetails(patientId);
        }
    });
}); 