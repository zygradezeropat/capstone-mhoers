 document.addEventListener('DOMContentLoaded', function() {
         const mainRoleSelect = document.getElementById('main_role');
         const bhwSubRoleSelect = document.getElementById('bhw_sub_role');
         const mhoSubRoleSelect = document.getElementById('mho_sub_role');
         const bhwSubRoleDiv = document.getElementById('bhw-sub-role');
         const mhoSubRoleDiv = document.getElementById('mho-sub-role');
         
         // Professional sections
         const bhwSection = document.getElementById('bhw-professional');
         const nurseSection = document.getElementById('nurse-professional');
         const mhoDoctorSection = document.getElementById('mho-doctor-professional');
         const mhoNurseSection = document.getElementById('mho-nurse-professional');
         
         function hideAllProfessionalSections() {
           bhwSection.style.display = 'none';
           bhwSection.classList.remove('show');
           nurseSection.style.display = 'none';
           nurseSection.classList.remove('show');
           mhoDoctorSection.style.display = 'none';
           mhoDoctorSection.classList.remove('show');
           mhoNurseSection.style.display = 'none';
           mhoNurseSection.classList.remove('show');
         }
         
         function showProfessionalSection(section) {
           hideAllProfessionalSections();
           section.style.display = 'block';
           setTimeout(() => section.classList.add('show'), 10);
         }
         
         function toggleProfessionalSections() {
           console.log('toggleProfessionalSections called, main role:', mainRoleSelect.value);
           hideAllProfessionalSections();
           
           if (mainRoleSelect.value === 'BHW') {
             // Show BHW sub-role dropdown, hide MHO sub-role
             bhwSubRoleDiv.style.display = 'block';
             mhoSubRoleDiv.style.display = 'none';
             mhoSubRoleSelect.value = '';
             
             // Check if BHW sub-role is already selected
             if (bhwSubRoleSelect.value === 'BHW') {
               showProfessionalSection(bhwSection);
             } else if (bhwSubRoleSelect.value === 'BHW_NURSE') {
               showProfessionalSection(nurseSection);
             }
           } else if (mainRoleSelect.value === 'MHO') {
             // Show MHO sub-role dropdown, hide BHW sub-role
             mhoSubRoleDiv.style.display = 'block';
             bhwSubRoleDiv.style.display = 'none';
             bhwSubRoleSelect.value = '';
             
             // Check if MHO sub-role is already selected
             if (mhoSubRoleSelect.value === 'MHO_DOCTOR') {
               showProfessionalSection(mhoDoctorSection);
             } else if (mhoSubRoleSelect.value === 'MHO_NURSE') {
               showProfessionalSection(mhoNurseSection);
             }
           } else {
             // Hide all sub-role dropdowns
             bhwSubRoleDiv.style.display = 'none';
             mhoSubRoleDiv.style.display = 'none';
             bhwSubRoleSelect.value = '';
             mhoSubRoleSelect.value = '';
           }
         }
         
         function handleBHWSubRole() {
           if (bhwSubRoleSelect.value === 'BHW') {
             showProfessionalSection(bhwSection);
           } else if (bhwSubRoleSelect.value === 'BHW_NURSE') {
             showProfessionalSection(nurseSection);
           } else {
             hideAllProfessionalSections();
           }
         }
         
         function handleMHOSubRole() {
           if (mhoSubRoleSelect.value === 'MHO_DOCTOR') {
             showProfessionalSection(mhoDoctorSection);
           } else if (mhoSubRoleSelect.value === 'MHO_NURSE') {
             showProfessionalSection(mhoNurseSection);
           } else {
             hideAllProfessionalSections();
           }
         }
         
         // Add event listeners
         mainRoleSelect.addEventListener('change', toggleProfessionalSections);
         bhwSubRoleSelect.addEventListener('change', handleBHWSubRole);
         mhoSubRoleSelect.addEventListener('change', handleMHOSubRole);
         
         // Check initial values on page load
         toggleProfessionalSections();
         
         // Add click listener to button for debugging
         const submitButton = document.querySelector('.register-button');
         submitButton.addEventListener('click', function(e) {
           console.log('Submit button clicked');
         });
         
         // Form validation
         const form = document.querySelector('.register-form');
         form.addEventListener('submit', function(e) {
           console.log('Form submission started');
           
           const mainRole = mainRoleSelect.value;
           const bhwSubRole = bhwSubRoleSelect.value;
           const mhoSubRole = mhoSubRoleSelect.value;
           
           console.log('Main role:', mainRole);
           console.log('BHW sub-role:', bhwSubRole);
           console.log('MHO sub-role:', mhoSubRole);
           
           // Validate main role selection
           if (!mainRole) {
             e.preventDefault();
             alert('Please select a main role (BHW or MHO)');
             console.log('Validation failed: No main role selected');
             return false;
           }
           
           // Validate sub-role selection
           if (mainRole === 'BHW' && !bhwSubRole) {
             e.preventDefault();
             alert('Please select a BHW type');
             console.log('Validation failed: No BHW sub-role selected');
             return false;
           }
           
           if (mainRole === 'MHO' && !mhoSubRole) {
             e.preventDefault();
             alert('Please select an MHO type');
             console.log('Validation failed: No MHO sub-role selected');
             return false;
           }
           
           // Validate password match
           const password1 = document.getElementById('password1').value;
           const password2 = document.getElementById('password2').value;
           if (password1 !== password2) {
             e.preventDefault();
             alert('Passwords do not match');
             console.log('Validation failed: Passwords do not match');
             return false;
           }
           
           console.log('Form validation passed, submitting...');
           return true;
         });
       });