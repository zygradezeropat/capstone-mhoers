// Register form JavaScript

 document.addEventListener('DOMContentLoaded', function() {
    
    // Image Upload Preview Functionality
    const profilePictureInput = document.getElementById('profile_picture');
    const imagePreview = document.getElementById('imagePreview');
    const previewImage = document.getElementById('previewImage');
    const removeImageBtn = document.getElementById('removeImageBtn');
    
    if (profilePictureInput && imagePreview && previewImage && removeImageBtn) {
        // Handle file selection
        profilePictureInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Validate file type
                if (!file.type.startsWith('image/')) {
                    alert('Please select a valid image file.');
                    profilePictureInput.value = '';
                    return;
                }
                
                // Validate file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    alert('Image size must be less than 5MB.');
                    profilePictureInput.value = '';
                    return;
                }
                
                // Create FileReader to preview image
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                    imagePreview.classList.add('has-image');
                };
                reader.readAsDataURL(file);
            }
        });
        
        // Handle remove image button
        removeImageBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent triggering the file input
            profilePictureInput.value = '';
            previewImage.src = '';
            imagePreview.classList.remove('has-image');
        });
    }
    
         
    // ISO/IEC 27002 Password Validation
    const password1 = document.getElementById('password1');
    const passwordRequirements = document.getElementById('passwordRequirements');
    
    if (password1 && passwordRequirements) {
        // Define validation functions first
        function validatePassword(password) {
            // ISO/IEC 27002 Password Requirements
            const hasMinLength = password.length >= 8;
            const hasUppercase = /[A-Z]/.test(password);
            const hasLowercase = /[a-z]/.test(password);
            const hasNumber = /\d/.test(password);
            const hasSpecial = /[@$!%*?&]/.test(password);

            return hasMinLength && hasUppercase && hasLowercase && hasNumber && hasSpecial;
        }

        function validatePasswordRequirements(password) {
            // Check each requirement
            const requirements = {
                'req-length': password.length >= 8,
                'req-uppercase': /[A-Z]/.test(password),
                'req-lowercase': /[a-z]/.test(password),
                'req-number': /\d/.test(password),
                'req-special': /[@$!%*?&]/.test(password)
            };

            // Update each requirement item
            Object.keys(requirements).forEach(function(reqId) {
                const reqItem = document.getElementById(reqId);
                if (reqItem) {
                    const icon = reqItem.querySelector('.requirement-icon');
                    const isValid = requirements[reqId];

                    // Remove existing classes
                    reqItem.classList.remove('valid', 'invalid');

                    if (isValid) {
                        reqItem.classList.add('valid');
                        icon.classList.remove('fa-times');
                        icon.classList.add('fa-check');
           } else {
                        reqItem.classList.add('invalid');
                        icon.classList.remove('fa-check');
                        icon.classList.add('fa-times');
                    }
                }
            });

            // Set custom validity for form validation
            if (password && !validatePassword(password)) {
                password1.setCustomValidity('Password must meet all security requirements.');
           } else {
                password1.setCustomValidity('');
            }
        }

        // Show requirements when password field is focused
        password1.addEventListener('focus', function() {
            passwordRequirements.style.display = 'block';
        });

        // Hide requirements when password field loses focus (if password is valid)
        password1.addEventListener('blur', function() {
            const password = this.value;
            if (password && validatePassword(password)) {
                setTimeout(() => {
                    passwordRequirements.style.display = 'none';
                }, 200);
            } else if (!password) {
                // Hide if field is empty
                setTimeout(() => {
                    passwordRequirements.style.display = 'none';
                }, 200);
            }
            // Keep visible if password exists but is invalid
        });

        // Real-time password validation
        password1.addEventListener('input', function() {
            const password = this.value;
            validatePasswordRequirements(password);
        });
    }

    // Username validation - check if username already exists
    const usernameInput = document.getElementById('username');
    const usernameIndicators = document.getElementById('username-validation-indicators');
    const usernameError = document.getElementById('username-error');
    const usernameSuccess = document.getElementById('username-success');
    const usernameChecking = document.getElementById('username-checking');
    const usernameLengthError = document.getElementById('username-length-error');
    let usernameCheckTimeout = null;
    
    if (usernameInput) {
        function checkUsernameAvailability(username) {
            const trimmedUsername = username ? username.trim() : '';
            
            // Hide all indicators initially
            if (usernameIndicators) {
                usernameIndicators.style.display = 'none';
            }
            if (usernameError) usernameError.style.display = 'none';
            if (usernameSuccess) usernameSuccess.style.display = 'none';
            if (usernameChecking) usernameChecking.style.display = 'none';
            if (usernameLengthError) usernameLengthError.style.display = 'none';
            
            // Check length first
            if (!trimmedUsername) {
                usernameInput.classList.remove('error');
                const formGroup = usernameInput.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
                usernameInput.setCustomValidity('');
                return;
            }
            
            if (trimmedUsername.length < 3) {
                // Show length error
                if (usernameIndicators) {
                    usernameIndicators.style.display = 'flex';
                }
                if (usernameLengthError) {
                    usernameLengthError.style.display = 'flex';
                }
                usernameInput.classList.add('error');
                const formGroup = usernameInput.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.add('has-error');
                }
                usernameInput.setCustomValidity('Username must be at least 3 characters.');
                return;
            }
            
            // Clear previous timeout
            if (usernameCheckTimeout) {
                clearTimeout(usernameCheckTimeout);
            }
            
            // Show checking indicator
            if (usernameIndicators) {
                usernameIndicators.style.display = 'flex';
            }
            if (usernameChecking) {
                usernameChecking.style.display = 'flex';
            }
            
            // Debounce: wait 500ms after user stops typing
            usernameCheckTimeout = setTimeout(function() {
                fetch(`/accounts/api/check-username/?username=${encodeURIComponent(trimmedUsername)}`)
                    .then(response => response.json())
                    .then(data => {
                        // Hide checking indicator
                        if (usernameChecking) {
                            usernameChecking.style.display = 'none';
                        }
                        
                        if (data.exists) {
                            // Show error
                            if (usernameError) {
                                usernameError.style.display = 'flex';
                            }
                            if (usernameSuccess) {
                                usernameSuccess.style.display = 'none';
                            }
                            usernameInput.classList.add('error');
                            const formGroup = usernameInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.add('has-error');
                            }
                            usernameInput.setCustomValidity('This username is already taken. Please choose a different username.');
                        } else {
                            // Show success
                            if (usernameError) {
                                usernameError.style.display = 'none';
                            }
                            if (usernameSuccess) {
                                usernameSuccess.style.display = 'flex';
                            }
                            usernameInput.classList.remove('error');
                            const formGroup = usernameInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.remove('has-error');
                            }
                            usernameInput.setCustomValidity('');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking username:', error);
                        // Hide indicators on error
                        if (usernameIndicators) {
                            usernameIndicators.style.display = 'none';
                        }
                        if (usernameChecking) {
                            usernameChecking.style.display = 'none';
                        }
                        // Don't block form submission on API error
                        usernameInput.setCustomValidity('');
                    });
            }, 500);
        }
        
        // Check on input (with debounce)
        usernameInput.addEventListener('input', function() {
            const username = this.value.trim();
            checkUsernameAvailability(username);
        });
        
        // Check on blur (immediate check)
        usernameInput.addEventListener('blur', function() {
            const username = this.value.trim();
            
            // Hide checking indicator if visible
            if (usernameChecking) {
                usernameChecking.style.display = 'none';
            }
            
            if (username && username.length >= 3) {
                // Clear timeout and check immediately
                if (usernameCheckTimeout) {
                    clearTimeout(usernameCheckTimeout);
                }
                
                // Show checking indicator
                if (usernameIndicators) {
                    usernameIndicators.style.display = 'flex';
                }
                if (usernameChecking) {
                    usernameChecking.style.display = 'flex';
                }
                
                fetch(`/accounts/api/check-username/?username=${encodeURIComponent(username)}`)
                    .then(response => response.json())
                    .then(data => {
                        // Hide checking indicator
                        if (usernameChecking) {
                            usernameChecking.style.display = 'none';
                        }
                        
                        if (data.exists) {
                            // Show error
                            if (usernameError) {
                                usernameError.style.display = 'flex';
                            }
                            if (usernameSuccess) {
                                usernameSuccess.style.display = 'none';
                            }
                            usernameInput.classList.add('error');
                            const formGroup = usernameInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.add('has-error');
                            }
                            usernameInput.setCustomValidity('This username is already taken. Please choose a different username.');
                        } else {
                            // Show success
                            if (usernameError) {
                                usernameError.style.display = 'none';
                            }
                            if (usernameSuccess) {
                                usernameSuccess.style.display = 'flex';
                            }
                            usernameInput.classList.remove('error');
                            const formGroup = usernameInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.remove('has-error');
                            }
                            usernameInput.setCustomValidity('');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking username:', error);
                        if (usernameIndicators) {
                            usernameIndicators.style.display = 'none';
                        }
                        if (usernameChecking) {
                            usernameChecking.style.display = 'none';
                        }
                        usernameInput.setCustomValidity('');
                    });
            } else if (username && username.length < 3) {
                // Show length error
                if (usernameIndicators) {
                    usernameIndicators.style.display = 'flex';
                }
                if (usernameLengthError) {
                    usernameLengthError.style.display = 'flex';
                }
                usernameInput.classList.add('error');
                const formGroup = usernameInput.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.add('has-error');
                }
                usernameInput.setCustomValidity('Username must be at least 3 characters.');
            } else {
                // Hide all indicators if empty
                if (usernameIndicators) {
                    usernameIndicators.style.display = 'none';
                }
                usernameInput.setCustomValidity('');
            }
        });
    }

    // Email validation - check if email already exists
    const emailInput = document.getElementById('email');
    let emailCheckTimeout = null;
    
    if (emailInput) {
        function checkEmailAvailability(email) {
            // Basic email format check first
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!email || !emailPattern.test(email)) {
                emailInput.setCustomValidity('');
                return;
            }
            
            // Clear previous timeout
            if (emailCheckTimeout) {
                clearTimeout(emailCheckTimeout);
            }
            
            // Debounce: wait 500ms after user stops typing
            emailCheckTimeout = setTimeout(function() {
                fetch(`/accounts/api/check-email/?email=${encodeURIComponent(email)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            emailInput.classList.add('error');
                            const formGroup = emailInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.add('has-error');
                            }
                            emailInput.setCustomValidity('This email is already registered. Please use a different email.');
                        } else {
                            emailInput.classList.remove('error');
                            const formGroup = emailInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.remove('has-error');
                            }
                            emailInput.setCustomValidity('');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking email:', error);
                        emailInput.setCustomValidity('');
                    });
            }, 500);
        }
        
        // Check on input (with debounce)
        emailInput.addEventListener('input', function() {
            const email = this.value.trim();
            checkEmailAvailability(email);
        });
        
        // Check on blur (immediate check)
        emailInput.addEventListener('blur', function() {
            const email = this.value.trim();
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (email && emailPattern.test(email)) {
                // Clear timeout and check immediately
                if (emailCheckTimeout) {
                    clearTimeout(emailCheckTimeout);
                }
                
                fetch(`/accounts/api/check-email/?email=${encodeURIComponent(email)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            emailInput.classList.add('error');
                            const formGroup = emailInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.add('has-error');
                            }
                            emailInput.setCustomValidity('This email is already registered. Please use a different email.');
                        } else {
                            emailInput.classList.remove('error');
                            const formGroup = emailInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.remove('has-error');
                            }
                            emailInput.setCustomValidity('');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking email:', error);
                        emailInput.setCustomValidity('');
                    });
            }
        });
    }

    // Phone number validation - must start with 09 and be exactly 11 digits, and check if exists
    const phoneInput = document.getElementById('phone');
    const phoneValidationIndicators = document.getElementById('phone-validation-indicators');
    const phonePrefixError = document.getElementById('phone-prefix-error');
    const phoneLengthError = document.getElementById('phone-length-error');
    let phoneCheckTimeout = null;
    
    // Function to update phone validation indicators
    function updatePhoneIndicators(phone) {
        if (!phone || phone.length === 0) {
            // Hide indicators if phone is empty
            if (phoneValidationIndicators) {
                phoneValidationIndicators.style.display = 'none';
            }
            if (phonePrefixError) phonePrefixError.style.display = 'none';
            if (phoneLengthError) phoneLengthError.style.display = 'none';
            return;
        }
        
        const hasLengthError = phone.length !== 11;
        const hasPrefixError = phone.length > 0 && !phone.startsWith('09');
        
        // Show/hide indicators container
        if (phoneValidationIndicators) {
            if (hasLengthError || hasPrefixError) {
                phoneValidationIndicators.style.display = 'flex';
            } else {
                phoneValidationIndicators.style.display = 'none';
            }
        }
        
        // Show/hide prefix error
        if (phonePrefixError) {
            if (hasPrefixError) {
                phonePrefixError.style.display = 'flex';
            } else {
                phonePrefixError.style.display = 'none';
            }
        }
        
        // Show/hide length error
        if (phoneLengthError) {
            if (hasLengthError) {
                phoneLengthError.style.display = 'flex';
            } else {
                phoneLengthError.style.display = 'none';
            }
        }
    }
    
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            let phone = this.value.replace(/[^0-9]/g, '');
            
            // Enforce "09" prefix - if user types anything else first, replace with "09"
            if (phone.length === 0) {
                // Field is empty, allow typing
            } else if (phone.length === 1) {
                // If first digit is not 0, replace with "09"
                if (phone !== '0') {
                    phone = '09';
                } else {
                    phone = '0';
                }
            } else if (phone.length === 2) {
                // If first two digits are not "09", force "09"
                if (!phone.startsWith('09')) {
                    phone = '09';
                }
            } else if (phone.length > 2 && !phone.startsWith('09')) {
                // If user pastes or types something that doesn't start with 09, force it
                phone = '09' + phone.substring(2).replace(/[^0-9]/g, '');
            }
            
            // Limit to 11 digits
            if (phone.length > 11) {
                phone = phone.substring(0, 11);
            }
            
            this.value = phone;
            
            // Update validation indicators
            updatePhoneIndicators(phone);
            
            // Validate: must start with 09 and be exactly 11 digits
            this.setCustomValidity('');
            if (phone && phone.length !== 11) {
                this.classList.add('error');
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.add('has-error');
                }
                this.setCustomValidity('Phone number must be exactly 11 digits.');
            } else if (phone && phone.length === 11 && !phone.startsWith('09')) {
                this.classList.add('error');
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.add('has-error');
                }
                this.setCustomValidity('Phone number must start with 09.');
            } else if (phone && phone.length === 11 && phone.startsWith('09')) {
                this.classList.remove('error');
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
                this.setCustomValidity('');
                
                // Check if phone number already exists (with debounce)
                if (phoneCheckTimeout) {
                    clearTimeout(phoneCheckTimeout);
                }
                
                phoneCheckTimeout = setTimeout(function() {
                    fetch(`/accounts/api/check-phone/?phone=${encodeURIComponent(phone)}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.exists) {
                                phoneInput.classList.add('error');
                                const formGroup = phoneInput.closest('.form-group');
                                if (formGroup) {
                                    formGroup.classList.add('has-error');
                                }
                                phoneInput.setCustomValidity('This phone number is already registered. Please use a different phone number.');
                            } else {
                                phoneInput.classList.remove('error');
                                const formGroup = phoneInput.closest('.form-group');
                                if (formGroup) {
                                    formGroup.classList.remove('has-error');
                                }
                                phoneInput.setCustomValidity('');
                            }
                        })
                        .catch(error => {
                            console.error('Error checking phone:', error);
                            phoneInput.setCustomValidity('');
                        });
                }, 500);
            } else if (!phone || phone.length === 0) {
                // Remove error state if empty
                this.classList.remove('error');
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
            }
        });

        phoneInput.addEventListener('blur', function() {
            const phone = this.value.replace(/[^0-9]/g, '');
            
            // Update validation indicators
            updatePhoneIndicators(phone);
            
            // Clear timeout for immediate check
            if (phoneCheckTimeout) {
                clearTimeout(phoneCheckTimeout);
            }
            
            if (phone && phone.length !== 11) {
                this.classList.add('error');
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.add('has-error');
                }
                this.setCustomValidity('Phone number must be exactly 11 digits.');
            } else if (phone && !phone.startsWith('09')) {
                this.classList.add('error');
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.add('has-error');
                }
                this.setCustomValidity('Phone number must start with 09.');
            } else if (phone && phone.length === 11 && phone.startsWith('09')) {
                this.classList.remove('error');
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
                this.setCustomValidity('');
            } else if (!phone || phone.length === 0) {
                // Remove error state if empty
                this.classList.remove('error');
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
            }
        });
        
        // Also update indicators on focus if there's a value
        phoneInput.addEventListener('focus', function() {
            const phone = this.value.replace(/[^0-9]/g, '');
            if (phone && phone.length > 0) {
                updatePhoneIndicators(phone);
            }
        });
    }

    // Registration Number validation - check if already exists
    const registrationNumberInput = document.getElementById('registration_number');
    let registrationNumberCheckTimeout = null;
    
    if (registrationNumberInput) {
        function checkRegistrationNumberAvailability(registrationNumber) {
            // Only check if format is valid (XX-XXX)
            const exactFormat = /^\d{2}-\d{3}$/;
            if (!exactFormat.test(registrationNumber)) {
                registrationNumberInput.setCustomValidity('');
                return;
            }
            
            // Clear timeout if exists
            if (registrationNumberCheckTimeout) {
                clearTimeout(registrationNumberCheckTimeout);
            }
            
            // Check availability with debounce
            registrationNumberCheckTimeout = setTimeout(function() {
                fetch(`/accounts/api/check-registration-number/?registration_number=${encodeURIComponent(registrationNumber)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            registrationNumberInput.classList.add('error');
                            const formGroup = registrationNumberInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.add('has-error');
                            }
                            registrationNumberInput.setCustomValidity('This registration number is already registered. Please use a different registration number.');
                        } else {
                            registrationNumberInput.classList.remove('error');
                            const formGroup = registrationNumberInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.remove('has-error');
                            }
                            registrationNumberInput.setCustomValidity('');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking registration number:', error);
                        registrationNumberInput.setCustomValidity('');
                    });
            }, 500);
        }
        
        // Check on input (with debounce)
        registrationNumberInput.addEventListener('input', function() {
            const registrationNumber = this.value.trim();
            checkRegistrationNumberAvailability(registrationNumber);
        });
        
        // Check on blur (immediate check)
        registrationNumberInput.addEventListener('blur', function() {
            const registrationNumber = this.value.trim();
            const exactFormat = /^\d{2}-\d{3}$/;
            
            if (registrationNumber && exactFormat.test(registrationNumber)) {
                // Clear timeout and check immediately
                if (registrationNumberCheckTimeout) {
                    clearTimeout(registrationNumberCheckTimeout);
                }
                
                fetch(`/accounts/api/check-registration-number/?registration_number=${encodeURIComponent(registrationNumber)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            registrationNumberInput.classList.add('error');
                            const formGroup = registrationNumberInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.add('has-error');
                            }
                            registrationNumberInput.setCustomValidity('This registration number is already registered. Please use a different registration number.');
                        } else {
                            registrationNumberInput.classList.remove('error');
                            const formGroup = registrationNumberInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.remove('has-error');
                            }
                            registrationNumberInput.setCustomValidity('');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking registration number:', error);
                        registrationNumberInput.setCustomValidity('');
                    });
            }
        });
    }

    // Accreditation Number validation - check if already exists
    const accreditationNumberInput = document.getElementById('accreditation_number');
    let accreditationNumberCheckTimeout = null;
    
    if (accreditationNumberInput) {
        function checkAccreditationNumberAvailability(accreditationNumber) {
            // Only check if format is valid (XX-XXX)
            const exactFormat = /^\d{2}-\d{3}$/;
            if (!exactFormat.test(accreditationNumber)) {
                accreditationNumberInput.setCustomValidity('');
                return;
            }
            
            // Clear timeout if exists
            if (accreditationNumberCheckTimeout) {
                clearTimeout(accreditationNumberCheckTimeout);
            }
            
            // Check availability with debounce
            accreditationNumberCheckTimeout = setTimeout(function() {
                fetch(`/accounts/api/check-accreditation-number/?accreditation_number=${encodeURIComponent(accreditationNumber)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            accreditationNumberInput.classList.add('error');
                            const formGroup = accreditationNumberInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.add('has-error');
                            }
                            accreditationNumberInput.setCustomValidity('This accreditation number is already registered. Please use a different accreditation number.');
                        } else {
                            accreditationNumberInput.classList.remove('error');
                            const formGroup = accreditationNumberInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.remove('has-error');
                            }
                            accreditationNumberInput.setCustomValidity('');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking accreditation number:', error);
                        accreditationNumberInput.setCustomValidity('');
                    });
            }, 500);
        }
        
        // Check on input (with debounce)
        accreditationNumberInput.addEventListener('input', function() {
            const accreditationNumber = this.value.trim();
            checkAccreditationNumberAvailability(accreditationNumber);
        });
        
        // Check on blur (immediate check)
        accreditationNumberInput.addEventListener('blur', function() {
            const accreditationNumber = this.value.trim();
            const exactFormat = /^\d{2}-\d{3}$/;
            
            if (accreditationNumber && exactFormat.test(accreditationNumber)) {
                // Clear timeout and check immediately
                if (accreditationNumberCheckTimeout) {
                    clearTimeout(accreditationNumberCheckTimeout);
                }
                
                fetch(`/accounts/api/check-accreditation-number/?accreditation_number=${encodeURIComponent(accreditationNumber)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            accreditationNumberInput.classList.add('error');
                            const formGroup = accreditationNumberInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.add('has-error');
                            }
                            accreditationNumberInput.setCustomValidity('This accreditation number is already registered. Please use a different accreditation number.');
                        } else {
                            accreditationNumberInput.classList.remove('error');
                            const formGroup = accreditationNumberInput.closest('.form-group');
                            if (formGroup) {
                                formGroup.classList.remove('has-error');
                            }
                            accreditationNumberInput.setCustomValidity('');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking accreditation number:', error);
                        accreditationNumberInput.setCustomValidity('');
                    });
            }
        });
    }

    // Password visibility toggle functionality
    const togglePassword1 = document.getElementById('togglePassword1');
    const togglePassword2 = document.getElementById('togglePassword2');
    const password2 = document.getElementById('password2');

    // Toggle password 1 visibility
    if (togglePassword1 && password1) {
        togglePassword1.addEventListener('click', function() {
            const type = password1.getAttribute('type') === 'password' ? 'text' : 'password';
            password1.setAttribute('type', type);
            
            // Toggle icon between eye (visible) and eye-slash (hidden)
            if (type === 'text') {
                togglePassword1.classList.remove('fa-eye-slash');
                togglePassword1.classList.add('fa-eye');
            } else {
                togglePassword1.classList.remove('fa-eye');
                togglePassword1.classList.add('fa-eye-slash');
            }
        });
    }

    // Toggle password 2 visibility
    if (togglePassword2 && password2) {
        togglePassword2.addEventListener('click', function() {
            const type = password2.getAttribute('type') === 'password' ? 'text' : 'password';
            password2.setAttribute('type', type);
            
            // Toggle icon between eye (visible) and eye-slash (hidden)
            if (type === 'text') {
                togglePassword2.classList.remove('fa-eye-slash');
                togglePassword2.classList.add('fa-eye');
            } else {
                togglePassword2.classList.remove('fa-eye');
                togglePassword2.classList.add('fa-eye-slash');
            }
        });
    }

    // Password match validation
    function validatePasswordMatch() {
        if (password1 && password2) {
            const pwd1 = password1.value;
            const pwd2 = password2.value;
            
            // Clear previous validity
            password2.setCustomValidity('');
            
            // Check if passwords match (only if both have values)
            if (pwd2 && pwd1 !== pwd2) {
                password2.setCustomValidity('Passwords do not match');
            } else {
                password2.setCustomValidity('');
            }
        }
    }

    // Validate password match when password1 changes
    if (password1) {
        password1.addEventListener('input', function() {
            validatePasswordMatch();
        });
    }

    // Validate password match when password2 changes
    if (password2) {
        password2.addEventListener('input', function() {
            validatePasswordMatch();
        });

        // Also validate on blur
        password2.addEventListener('blur', function() {
            validatePasswordMatch();
            if (this.value && password1.value && this.value !== password1.value) {
                this.classList.add('error');
                const formGroup = this.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.add('has-error');
                }
            }
        });
    }

    // Privacy consent checkbox validation
    const privacyConsentCheckbox = document.getElementById('privacy_consent');
    if (privacyConsentCheckbox) {
        // Remove error styling when checkbox is checked
        privacyConsentCheckbox.addEventListener('change', function() {
            const consentContainer = this.closest('.form-check');
            if (this.checked) {
                if (consentContainer) {
                    consentContainer.style.border = '1px solid #e2e8f0';
                    consentContainer.style.background = '#f8fafc';
                }
                this.setCustomValidity('');
            }
        });
    }

    // Form submission validation
    const form = document.querySelector('.register-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            // First, remove all error classes
            const allFields = form.querySelectorAll('.form-input, .form-select');
            allFields.forEach(function(field) {
                field.classList.remove('error');
                const formGroup = field.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
            });
            
            // Check privacy consent checkbox first
            const privacyConsent = document.getElementById('privacy_consent');
            if (privacyConsent && !privacyConsent.checked) {
                e.preventDefault();
                e.stopPropagation();
                
                // Add error styling to checkbox container
                const consentContainer = privacyConsent.closest('.form-check');
                if (consentContainer) {
                    consentContainer.style.border = '2px solid #dc2626';
                    consentContainer.style.background = '#fef2f2';
                }
                
                // Show error message
                privacyConsent.setCustomValidity('You must agree to the Data Privacy Terms and Agreement to register.');
                privacyConsent.reportValidity();
                
                // Scroll to checkbox
                privacyConsent.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                return false;
            }
            
            // Check all required fields and add red border to empty ones
            const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
            let hasEmptyFields = false;
            
            requiredFields.forEach(function(field) {
                // Skip hidden fields or disabled fields that are conditionally shown
                if (field.type === 'hidden' || 
                    field.style.display === 'none' || 
                    (field.closest('.form-group') && field.closest('.form-group').style.display === 'none')) {
                    return;
                }
                
                // Check if field is empty
                let isEmpty = false;
                
                if (field.tagName === 'SELECT') {
                    // For select fields, check if value is empty or default option
                    isEmpty = !field.value || field.value === '' || 
                             (field.options[field.selectedIndex] && 
                              field.options[field.selectedIndex].hasAttribute('disabled') &&
                              field.options[field.selectedIndex].hasAttribute('selected'));
                } else if (field.type === 'file') {
                    // For file inputs, check if files are selected
                    isEmpty = !field.files || field.files.length === 0;
                } else {
                    // For text inputs, check if value is empty after trim
                    isEmpty = !field.value || field.value.trim() === '';
                }
                
                // Also check if field is disabled (for cascading dropdowns)
                if (field.disabled && field.hasAttribute('required')) {
                    // Check if it should be enabled based on parent selections
                    const regionSelect = document.getElementById('region');
                    const provinceSelect = document.getElementById('province');
                    const municipalitySelect = document.getElementById('municipality');
                    const barangaySelect = document.getElementById('barangay');
                    const purokInput = document.getElementById('purok');
                    
                    // If it's a cascading dropdown that should be enabled, mark as empty
                    if (field === provinceSelect && regionSelect && !regionSelect.value) {
                        isEmpty = true;
                    } else if (field === municipalitySelect && provinceSelect && !provinceSelect.value) {
                        isEmpty = true;
                    } else if (field === barangaySelect && municipalitySelect && !municipalitySelect.value) {
                        isEmpty = true;
                    } else if (field === purokInput && barangaySelect && !barangaySelect.value) {
                        isEmpty = true;
                    } else {
                        // If disabled but shouldn't be required yet, skip
                        return;
                    }
                }
                
                if (isEmpty) {
                    hasEmptyFields = true;
                    field.classList.add('error');
                    const formGroup = field.closest('.form-group');
                    if (formGroup) {
                        formGroup.classList.add('has-error');
                    }
                }
            });
            
            // Check privacy consent checkbox
            const privacyConsentCheckbox = document.getElementById('privacy_consent');
            if (privacyConsentCheckbox && !privacyConsentCheckbox.checked) {
                e.preventDefault();
                e.stopPropagation();
                
                // Add error styling to checkbox container
                const consentContainer = privacyConsentCheckbox.closest('.form-check');
                if (consentContainer) {
                    consentContainer.style.border = '2px solid #dc2626';
                    consentContainer.style.background = '#fef2f2';
                }
                
                // Show error message
                privacyConsentCheckbox.setCustomValidity('You must agree to the Data Privacy Terms and Agreement to register.');
                privacyConsentCheckbox.reportValidity();
                
                // Scroll to checkbox
                privacyConsentCheckbox.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                return false;
            } else if (privacyConsentCheckbox && privacyConsentCheckbox.checked) {
                // Remove error styling if checkbox is checked
                const consentContainer = privacyConsentCheckbox.closest('.form-check');
                if (consentContainer) {
                    consentContainer.style.border = '1px solid #e2e8f0';
                    consentContainer.style.background = '#f8fafc';
                }
                privacyConsentCheckbox.setCustomValidity('');
            }
            
            // If there are empty required fields, prevent submission and focus on first error
            if (hasEmptyFields) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus on first invalid field
                const firstError = form.querySelector('.error');
                if (firstError) {
                    firstError.focus();
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                
                return false;
            }
            
            let hasErrors = false;
            
            // Validate username length first
            if (usernameInput && usernameInput.value.trim()) {
                const username = usernameInput.value.trim();
                if (username.length < 3) {
                    e.preventDefault();
                    usernameInput.classList.add('error');
                    const formGroup = usernameInput.closest('.form-group');
                    if (formGroup) {
                        formGroup.classList.add('has-error');
                    }
                    usernameInput.focus();
                    usernameInput.setCustomValidity('Username must be at least 3 characters.');
                    return false;
                }
                
                // Check if there's already a custom error (from blur validation)
                if (usernameInput.validity.customError) {
                    e.preventDefault();
                    usernameInput.classList.add('error');
                    const formGroup = usernameInput.closest('.form-group');
                    if (formGroup) {
                        formGroup.classList.add('has-error');
                    }
                    usernameInput.focus();
                    return false;
                }
            }
            
            // Validate email
            if (emailInput && emailInput.value.trim()) {
                // Check if there's already a custom error (from blur validation)
                if (emailInput.validity.customError) {
                    e.preventDefault();
                    emailInput.classList.add('error');
                    const formGroup = emailInput.closest('.form-group');
                    if (formGroup) {
                        formGroup.classList.add('has-error');
                    }
                    emailInput.focus();
                    return false;
                }
            }
            
            // Validate phone number
            if (phoneInput) {
                const phone = phoneInput.value.replace(/[^0-9]/g, '');
                // Update phone indicators on form submit
                updatePhoneIndicators(phone);
                
                if (phone.length !== 11) {
                    e.preventDefault();
                    phoneInput.classList.add('error');
                    const formGroup = phoneInput.closest('.form-group');
                    if (formGroup) {
                        formGroup.classList.add('has-error');
                    }
                    phoneInput.focus();
                    phoneInput.setCustomValidity('Phone number must be exactly 11 digits.');
                    return false;
                } else if (!phone.startsWith('09')) {
                    e.preventDefault();
                    phoneInput.classList.add('error');
                    const formGroup = phoneInput.closest('.form-group');
                    if (formGroup) {
                        formGroup.classList.add('has-error');
                    }
                    phoneInput.focus();
                    phoneInput.setCustomValidity('Phone number must start with 09.');
                    return false;
                }
                
                // Check if there's already a custom error (from blur validation)
                if (phoneInput.validity.customError) {
                    e.preventDefault();
                    phoneInput.classList.add('error');
                    const formGroup = phoneInput.closest('.form-group');
                    if (formGroup) {
                        formGroup.classList.add('has-error');
                    }
                    phoneInput.focus();
                    return false;
                }
            }

            // Validate password match
            if (password1 && password2) {
                validatePasswordMatch();
                if (password2.value && password1.value !== password2.value) {
                    e.preventDefault();
                    password2.classList.add('error');
                    const formGroup = password2.closest('.form-group');
                    if (formGroup) {
                        formGroup.classList.add('has-error');
                    }
                    password2.focus();
                    password2.setCustomValidity('Passwords do not match');
                    return false;
                }
            }

            // Validate BHW registration and accreditation numbers (must be XX-XXX format)
            const mainRole = mainRoleSelect ? mainRoleSelect.value : '';
            if (mainRole === 'BHW') {
                const exactFormat = /^\d{2}-\d{3}$/;
                
                if (registrationNumberInput && registrationNumberInput.value) {
                    if (!exactFormat.test(registrationNumberInput.value.trim())) {
                        e.preventDefault();
                        registrationNumberInput.classList.add('error');
                        const formGroup = registrationNumberInput.closest('.form-group');
                        if (formGroup) {
                            formGroup.classList.add('has-error');
                        }
                        registrationNumberInput.focus();
                        registrationNumberInput.setCustomValidity('Registration Number must be exactly 2 digits, dash, 3 digits (e.g., 32-424)');
                        return false;
                    }
                    
                    // Check if there's already a custom error (from blur validation)
                    if (registrationNumberInput.validity.customError) {
                        e.preventDefault();
                        registrationNumberInput.classList.add('error');
                        const formGroup = registrationNumberInput.closest('.form-group');
                        if (formGroup) {
                            formGroup.classList.add('has-error');
                        }
                        registrationNumberInput.focus();
                        return false;
                    }
                }
                
                if (accreditationNumberInput && accreditationNumberInput.value) {
                    if (!exactFormat.test(accreditationNumberInput.value.trim())) {
                        e.preventDefault();
                        accreditationNumberInput.classList.add('error');
                        const formGroup = accreditationNumberInput.closest('.form-group');
                        if (formGroup) {
                            formGroup.classList.add('has-error');
                        }
                        accreditationNumberInput.focus();
                        accreditationNumberInput.setCustomValidity('Accreditation Number must be exactly 2 digits, dash, 3 digits (e.g., 32-424)');
                        return false;
                    }
                    
                    // Check if there's already a custom error (from blur validation)
                    if (accreditationNumberInput.validity.customError) {
                        e.preventDefault();
                        accreditationNumberInput.classList.add('error');
                        const formGroup = accreditationNumberInput.closest('.form-group');
                        if (formGroup) {
                            formGroup.classList.add('has-error');
                        }
                        accreditationNumberInput.focus();
                        return false;
                    }
                }
            }
            
            // Final availability checks before submission (username, email, phone, registration_number, accreditation_number)
            const needsFinalCheck = (
                (usernameInput && usernameInput.value.trim() && usernameInput.value.trim().length >= 3 && !usernameInput.validity.customError) ||
                (emailInput && emailInput.value.trim() && !emailInput.validity.customError) ||
                (phoneInput && phoneInput.value.replace(/[^0-9]/g, '').length === 11 && phoneInput.value.replace(/[^0-9]/g, '').startsWith('09') && !phoneInput.validity.customError) ||
                (mainRole === 'BHW' && registrationNumberInput && registrationNumberInput.value.trim() && /^\d{2}-\d{3}$/.test(registrationNumberInput.value.trim()) && !registrationNumberInput.validity.customError) ||
                (mainRole === 'BHW' && accreditationNumberInput && accreditationNumberInput.value.trim() && /^\d{2}-\d{3}$/.test(accreditationNumberInput.value.trim()) && !accreditationNumberInput.validity.customError)
            );
            
            if (needsFinalCheck) {
                // Prevent default submission to do async checks
                e.preventDefault();
                const formToSubmit = this;
                const username = usernameInput ? usernameInput.value.trim() : '';
                const email = emailInput ? emailInput.value.trim() : '';
                const phone = phoneInput ? phoneInput.value.replace(/[^0-9]/g, '') : '';
                
                // Array to store all promises
                const checks = [];
                
                // Check username
                if (username && username.length >= 3 && !usernameInput.validity.customError) {
                    checks.push(
                        fetch(`/accounts/api/check-username/?username=${encodeURIComponent(username)}`)
                            .then(response => response.json())
                            .then(data => ({ type: 'username', exists: data.exists }))
                    );
                }
                
                // Check email
                if (email && !emailInput.validity.customError) {
                    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (emailPattern.test(email)) {
                        checks.push(
                            fetch(`/accounts/api/check-email/?email=${encodeURIComponent(email)}`)
                                .then(response => response.json())
                                .then(data => ({ type: 'email', exists: data.exists }))
                        );
                    }
                }
                
                // Check phone
                if (phone && phone.length === 11 && phone.startsWith('09') && !phoneInput.validity.customError) {
                    checks.push(
                        fetch(`/accounts/api/check-phone/?phone=${encodeURIComponent(phone)}`)
                            .then(response => response.json())
                            .then(data => ({ type: 'phone', exists: data.exists }))
                    );
                }
                
                // Check registration number (only if BHW role)
                if (mainRole === 'BHW' && registrationNumberInput && registrationNumberInput.value.trim()) {
                    const registrationNumber = registrationNumberInput.value.trim();
                    const exactFormat = /^\d{2}-\d{3}$/;
                    if (exactFormat.test(registrationNumber) && !registrationNumberInput.validity.customError) {
                        checks.push(
                            fetch(`/accounts/api/check-registration-number/?registration_number=${encodeURIComponent(registrationNumber)}`)
                                .then(response => response.json())
                                .then(data => ({ type: 'registration_number', exists: data.exists }))
                        );
                    }
                }
                
                // Check accreditation number (only if BHW role)
                if (mainRole === 'BHW' && accreditationNumberInput && accreditationNumberInput.value.trim()) {
                    const accreditationNumber = accreditationNumberInput.value.trim();
                    const exactFormat = /^\d{2}-\d{3}$/;
                    if (exactFormat.test(accreditationNumber) && !accreditationNumberInput.validity.customError) {
                        checks.push(
                            fetch(`/accounts/api/check-accreditation-number/?accreditation_number=${encodeURIComponent(accreditationNumber)}`)
                                .then(response => response.json())
                                .then(data => ({ type: 'accreditation_number', exists: data.exists }))
                        );
                    }
                }
                
                // Wait for all checks to complete
                Promise.all(checks)
                    .then(results => {
                        let hasError = false;
                        
                        results.forEach(result => {
                            if (result.exists) {
                                hasError = true;
                                if (result.type === 'username') {
                                    usernameInput.classList.add('error');
                                    const formGroup = usernameInput.closest('.form-group');
                                    if (formGroup) {
                                        formGroup.classList.add('has-error');
                                    }
                                    usernameInput.setCustomValidity('This username is already taken. Please choose a different username.');
                                    usernameInput.focus();
                                } else if (result.type === 'email') {
                                    emailInput.classList.add('error');
                                    const formGroup = emailInput.closest('.form-group');
                                    if (formGroup) {
                                        formGroup.classList.add('has-error');
                                    }
                                    emailInput.setCustomValidity('This email is already registered. Please use a different email.');
                                    emailInput.focus();
                                } else if (result.type === 'phone') {
                                    phoneInput.classList.add('error');
                                    const formGroup = phoneInput.closest('.form-group');
                                    if (formGroup) {
                                        formGroup.classList.add('has-error');
                                    }
                                    phoneInput.setCustomValidity('This phone number is already registered. Please use a different phone number.');
                                    phoneInput.focus();
                                } else if (result.type === 'registration_number') {
                                    registrationNumberInput.classList.add('error');
                                    const formGroup = registrationNumberInput.closest('.form-group');
                                    if (formGroup) {
                                        formGroup.classList.add('has-error');
                                    }
                                    registrationNumberInput.setCustomValidity('This registration number is already registered. Please use a different registration number.');
                                    registrationNumberInput.focus();
                                } else if (result.type === 'accreditation_number') {
                                    accreditationNumberInput.classList.add('error');
                                    const formGroup = accreditationNumberInput.closest('.form-group');
                                    if (formGroup) {
                                        formGroup.classList.add('has-error');
                                    }
                                    accreditationNumberInput.setCustomValidity('This accreditation number is already registered. Please use a different accreditation number.');
                                    accreditationNumberInput.focus();
                                }
                            }
                        });
                        
                        if (!hasError) {
                            // All checks passed, submit the form
                            if (usernameInput) usernameInput.setCustomValidity('');
                            if (emailInput) emailInput.setCustomValidity('');
                            if (phoneInput) phoneInput.setCustomValidity('');
                            if (registrationNumberInput) registrationNumberInput.setCustomValidity('');
                            if (accreditationNumberInput) accreditationNumberInput.setCustomValidity('');
                            formToSubmit.submit();
                        }
                    })
                    .catch(error => {
                        console.error('Error checking availability:', error);
                        // On error, allow submission (server will validate)
                        if (usernameInput) usernameInput.setCustomValidity('');
                        if (emailInput) emailInput.setCustomValidity('');
                        if (phoneInput) phoneInput.setCustomValidity('');
                        if (registrationNumberInput) registrationNumberInput.setCustomValidity('');
                        if (accreditationNumberInput) accreditationNumberInput.setCustomValidity('');
                        formToSubmit.submit();
                    });
                
                return false;
            }
        });
    }

    // Cascading Location Dropdowns (Region -> Province -> City -> Barangay)
    const regionSelect = document.getElementById('region');
    const provinceSelect = document.getElementById('province');
    const municipalitySelect = document.getElementById('municipality');
    const barangaySelect = document.getElementById('barangay');
    const purokInput = document.getElementById('purok');
    let userRole = null; // Will be set based on role selection

    // Initialize location dropdowns
    if (regionSelect && provinceSelect && municipalitySelect && barangaySelect) {
        // Load regions on page load
        loadRegions();
        
        // Region change handler - enable province selection when region is selected
        regionSelect.addEventListener('change', function() {
            const selectedRegion = this.value;
            if (selectedRegion) {
                // Enable province dropdown and load provinces for selected region
                provinceSelect.disabled = false;
                loadProvinces(selectedRegion);
                // Clear dependent fields
                provinceSelect.innerHTML = '<option value="" disabled selected>Select Province</option>';
                municipalitySelect.innerHTML = '<option value="" disabled selected>Select City/Municipality</option>';
                municipalitySelect.disabled = true;
                barangaySelect.innerHTML = '<option value="" disabled selected>Select Barangay</option>';
                barangaySelect.disabled = true;
                if (purokInput) {
                    purokInput.value = '';
                    purokInput.disabled = true;
                }
            } else {
                // Disable province and all dependent fields if no region selected
                provinceSelect.innerHTML = '<option value="" disabled selected>Select Province</option>';
                provinceSelect.disabled = true;
                municipalitySelect.innerHTML = '<option value="" disabled selected>Select City/Municipality</option>';
                municipalitySelect.disabled = true;
                barangaySelect.innerHTML = '<option value="" disabled selected>Select Barangay</option>';
                barangaySelect.disabled = true;
                if (purokInput) {
                    purokInput.value = '';
                    purokInput.disabled = true;
                }
            }
        });

        // Province change handler
        provinceSelect.addEventListener('change', function() {
            const selectedProvince = this.value;
            if (selectedProvince) {
                loadCities(selectedProvince);
                // Clear city and barangay when province changes
                municipalitySelect.innerHTML = '<option value="" disabled selected>Select City/Municipality</option>';
                municipalitySelect.disabled = false;
                barangaySelect.innerHTML = '<option value="" disabled selected>Select Barangay</option>';
                barangaySelect.disabled = true;
                if (purokInput) {
                    purokInput.value = '';
                    purokInput.disabled = true;
                }
                
                // If BHW role is selected, auto-select New Corella after cities load
                if (userRole === 'BHW') {
                    setTimeout(() => handleRoleBasedCitySelection(), 500);
                }
            } else {
                municipalitySelect.innerHTML = '<option value="" disabled selected>Select City/Municipality</option>';
                municipalitySelect.disabled = true;
                barangaySelect.innerHTML = '<option value="" disabled selected>Select Barangay</option>';
                barangaySelect.disabled = true;
                if (purokInput) {
                    purokInput.value = '';
                    purokInput.disabled = true;
                }
            }
        });

        // City change handler
        municipalitySelect.addEventListener('change', function() {
            const selectedCity = this.value;
            const selectedProvince = provinceSelect.value;
            if (selectedCity && selectedProvince) {
                loadBarangays(selectedCity, selectedProvince);
                // Clear barangay when city changes
                barangaySelect.innerHTML = '<option value="" disabled selected>Select Barangay</option>';
                barangaySelect.disabled = false;
                if (purokInput) {
                    purokInput.value = '';
                    purokInput.disabled = true;
                }
            } else {
                barangaySelect.innerHTML = '<option value="" disabled selected>Select Barangay</option>';
                barangaySelect.disabled = true;
                if (purokInput) purokInput.disabled = true;
            }
        });

        // Barangay change handler
        barangaySelect.addEventListener('change', function() {
            const selectedBarangay = this.value;
            if (selectedBarangay && purokInput) {
                purokInput.disabled = false;
            } else if (purokInput) {
                purokInput.value = '';
                purokInput.disabled = true;
            }
        });

        // Listen for role changes to handle BHW auto-selection
        const mainRoleSelect = document.getElementById('main_role');
        if (mainRoleSelect) {
            mainRoleSelect.addEventListener('change', function() {
                userRole = this.value;
                // If province is already selected, trigger city auto-selection for BHW
                if (userRole === 'BHW' && provinceSelect.value) {
                    handleRoleBasedCitySelection();
                } else if (userRole === 'DOCTOR') {
                    // Enable city selection for doctors
                    municipalitySelect.disabled = false;
                }
            });
            
            // Check initial role value
            if (mainRoleSelect.value) {
                userRole = mainRoleSelect.value;
                if (userRole === 'BHW' && provinceSelect.value) {
                    handleRoleBasedCitySelection();
                }
            }
        }
        
        // Initialize: Disable province and dependent fields until region is selected
        provinceSelect.disabled = true;
        municipalitySelect.disabled = true;
        barangaySelect.disabled = true;
        if (purokInput) {
            purokInput.disabled = true;
        }
    }

    // Load regions from API
    function loadRegions() {
        if (!regionSelect) {
            console.error('Region select element not found');
            return;
        }
        
        regionSelect.innerHTML = '<option value="" disabled selected>Loading regions...</option>';
        regionSelect.disabled = true;
        
        fetch('/facilities/api/psgc-regions/')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Regions data received:', data);
                regionSelect.innerHTML = '<option value="" disabled selected>Select Region</option>';
                
                // Handle both array and object responses
                let regionsList = [];
                if (Array.isArray(data)) {
                    regionsList = data;
                } else if (data && typeof data === 'object') {
                    // Check if it's an error response
                    if (data.error) {
                        console.error('API returned error:', data.error);
                        regionSelect.innerHTML = '<option value="" disabled selected>Error: ' + data.error + '</option>';
                        regionSelect.disabled = false;
                        return;
                    }
                    // Try to extract array from object
                    if (Array.isArray(data.data)) {
                        regionsList = data.data;
                    } else if (Array.isArray(data.results)) {
                        regionsList = data.results;
                    }
                }
                
                if (regionsList.length > 0) {
                    regionsList.forEach(region => {
                        const option = document.createElement('option');
                        // Handle both object and string formats
                        const regionName = typeof region === 'string' ? region : (region.name || region.region_name || '');
                        // FIX: Use region code as value (not name) so backend can match properly
                        const regionValue = typeof region === 'string' ? region : (region.code || region.region_code || region.name || '');
                        option.value = regionValue;  // This should be the code (e.g., "11" for Region XI)
                        option.textContent = regionName;  // This is the display name (e.g., "Region XI (Davao Region)")
                        regionSelect.appendChild(option);
                    });
                    console.log(`Loaded ${regionsList.length} regions`);
                } else {
                    console.warn('No regions found in response');
                    regionSelect.innerHTML = '<option value="" disabled selected>No regions available</option>';
                }
                regionSelect.disabled = false;
            })
            .catch(error => {
                console.error('Error loading regions:', error);
                regionSelect.innerHTML = '<option value="" disabled selected>Error loading regions. Please refresh the page.</option>';
                regionSelect.disabled = false;
            });
    }
    
    // Load provinces from API (filtered by region if provided)
    function loadProvinces(region = null) {
        if (!provinceSelect) return;
        
        provinceSelect.innerHTML = '<option value="" disabled selected>Loading provinces...</option>';
        provinceSelect.disabled = true;
        
        // Build API URL with optional region parameter
        let apiUrl = '/facilities/api/psgc-provinces/';
        if (region) {
            apiUrl += `?region=${encodeURIComponent(region)}`;
        }
        
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                provinceSelect.innerHTML = '<option value="" disabled selected>Select Province</option>';
                if (Array.isArray(data) && data.length > 0) {
                    data.forEach(province => {
                        const option = document.createElement('option');
                        option.value = province.name;
                        option.textContent = province.name;
                        provinceSelect.appendChild(option);
                    });
                }
                provinceSelect.disabled = false;
            })
            .catch(error => {
                console.error('Error loading provinces:', error);
                provinceSelect.innerHTML = '<option value="" disabled selected>Error loading provinces</option>';
                provinceSelect.disabled = false;
            });
    }

    // Load cities based on selected province
    function loadCities(province) {
        municipalitySelect.innerHTML = '<option value="" disabled selected>Loading cities...</option>';
        municipalitySelect.disabled = true;
        
        const provinceQuery = encodeURIComponent(province);
        fetch(`/facilities/api/psgc-cities/?province=${provinceQuery}`)
            .then(response => response.json())
            .then(data => {
                municipalitySelect.innerHTML = '<option value="" disabled selected>Select City/Municipality</option>';
                if (Array.isArray(data) && data.length > 0) {
                    data.forEach(city => {
                        const option = document.createElement('option');
                        option.value = city.name;
                        option.textContent = city.name;
                        municipalitySelect.appendChild(option);
                    });
                } else {
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = 'No cities found';
                    option.disabled = true;
                    municipalitySelect.appendChild(option);
                }
                municipalitySelect.disabled = false;
            })
            .catch(error => {
                console.error('Error loading cities:', error);
                municipalitySelect.innerHTML = '<option value="" disabled selected>Error loading cities</option>';
                municipalitySelect.disabled = false;
            });
    }

    // Load barangays based on selected city and province
    function loadBarangays(city, province) {
        barangaySelect.innerHTML = '<option value="" disabled selected>Loading barangays...</option>';
        barangaySelect.disabled = true;
        
        const cityQuery = encodeURIComponent(city);
        const provinceQuery = encodeURIComponent(province);
        fetch(`/facilities/api/psgc-barangays/?city=${cityQuery}&province=${provinceQuery}`)
            .then(response => response.json())
            .then(data => {
                barangaySelect.innerHTML = '<option value="" disabled selected>Select Barangay</option>';
                if (Array.isArray(data) && data.length > 0) {
                    data.forEach(barangay => {
                        const option = document.createElement('option');
                        option.value = barangay.name;
                        option.textContent = barangay.name;
                        barangaySelect.appendChild(option);
                    });
                } else {
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = 'No barangays found';
                    option.disabled = true;
                    barangaySelect.appendChild(option);
                }
                barangaySelect.disabled = false;
            })
            .catch(error => {
                console.error('Error loading barangays:', error);
                barangaySelect.innerHTML = '<option value="" disabled selected>Error loading barangays</option>';
                barangaySelect.disabled = false;
            });
    }

    // Handle role-based city selection (BHW auto-selects New Corella)
    function handleRoleBasedCitySelection() {
        if (userRole === 'BHW') {
            // If province is already selected, trigger city loading and auto-select
            if (provinceSelect.value) {
                // Trigger city load if not already loaded
                if (municipalitySelect.options.length <= 1) {
                    loadCities(provinceSelect.value);
                }
                // Wait for cities to load, then auto-select New Corella
                const checkCity = setInterval(() => {
                    const newCorellaOption = Array.from(municipalitySelect.options).find(
                        opt => opt.textContent.toLowerCase().includes('new corella')
                    );
                    if (newCorellaOption && newCorellaOption.value && !municipalitySelect.disabled) {
                        municipalitySelect.value = newCorellaOption.value;
                        municipalitySelect.dispatchEvent(new Event('change'));
                        municipalitySelect.disabled = true; // Disable for BHW
                        clearInterval(checkCity);
                    }
                }, 100);
                
                // Stop checking after 5 seconds
                setTimeout(() => clearInterval(checkCity), 5000);
            }
        } else if (userRole === 'DOCTOR') {
            // Enable city selection for doctors
            municipalitySelect.disabled = false;
        }
    }
    


    // Show/hide role-based sections based on role selection
    const mainRoleSelect = document.getElementById('main_role');
    const doctorInfoSection = document.getElementById('doctor-info-section');
    const bhwInfoSection = document.getElementById('bhw-info-section');
    const assignedFacilityGroup = document.getElementById('assigned-facility-group');
    const specializationInput = document.getElementById('specialization');
    const licenseNumberInput = document.getElementById('license_number');
    // registrationNumberInput and accreditationNumberInput are already declared above
    const assignedFacilitySelect = document.getElementById('assigned_facility');
    
    if (mainRoleSelect) {
        function toggleRoleBasedSections() {
            const selectedRole = mainRoleSelect.value;
            
            // Handle BHW Professional Information section
            if (bhwInfoSection) {
                if (selectedRole === 'BHW') {
                    bhwInfoSection.style.display = 'block';
                    // Make registration and accreditation numbers required when BHW is selected
                    if (registrationNumberInput) {
                        registrationNumberInput.setAttribute('required', 'required');
                    }
                    if (accreditationNumberInput) {
                        accreditationNumberInput.setAttribute('required', 'required');
                    }
                } else {
                    bhwInfoSection.style.display = 'none';
                    // Remove required attribute and clear values when BHW is not selected
                    if (registrationNumberInput) {
                        registrationNumberInput.removeAttribute('required');
                        registrationNumberInput.value = '';
                    }
                    if (accreditationNumberInput) {
                        accreditationNumberInput.removeAttribute('required');
                        accreditationNumberInput.value = '';
                    }
                }
            }
            
            // Handle Doctor Information section
            const doctorFacilitySelect = document.getElementById('assigned_facility_doctor');
            if (doctorInfoSection) {
                if (selectedRole === 'DOCTOR') {
                    doctorInfoSection.style.display = 'block';
                    // Make specialization and license number required when doctor is selected
                    if (specializationInput) {
                        specializationInput.setAttribute('required', 'required');
                    }
                    if (licenseNumberInput) {
                        licenseNumberInput.setAttribute('required', 'required');
                    }
                    // Auto-select MHO facility when doctor is selected
                    if (doctorFacilitySelect) {
                        doctorFacilitySelect.value = 'MHO';
                        doctorFacilitySelect.setAttribute('required', 'required');
                    }
                } else {
                    doctorInfoSection.style.display = 'none';
                    // Remove required attribute and clear values when doctor is not selected
                    if (specializationInput) {
                        specializationInput.removeAttribute('required');
                        specializationInput.value = '';
                    }
                    if (licenseNumberInput) {
                        licenseNumberInput.removeAttribute('required');
                        licenseNumberInput.value = '';
                    }
                    if (doctorFacilitySelect) {
                        doctorFacilitySelect.removeAttribute('required');
                        doctorFacilitySelect.value = '';
                    }
                }
            }
            
            // Handle Assigned Facility dropdown
            if (assignedFacilityGroup) {
                if (selectedRole === 'BHW') {
                    assignedFacilityGroup.style.display = 'block';
                    // Make assigned facility required when BHW is selected
                    if (assignedFacilitySelect) {
                        assignedFacilitySelect.setAttribute('required', 'required');
                    }
                } else {
                    assignedFacilityGroup.style.display = 'none';
                    // Remove required attribute and clear value when BHW is not selected
                    if (assignedFacilitySelect) {
                        assignedFacilitySelect.removeAttribute('required');
                        assignedFacilitySelect.value = '';
                    }
                }
            }
        }
        
        // Check on page load
        toggleRoleBasedSections();
        
        // Check when role changes
        mainRoleSelect.addEventListener('change', toggleRoleBasedSections);
    }

    // Format Registration Number and Accreditation Number (strict format: XX-XXX)
    function formatNumberWithDash(input) {
        if (!input) return;
        
        input.addEventListener('input', function(e) {
            // Remove all non-numeric characters except dash
            let value = e.target.value.replace(/[^0-9-]/g, '');
            
            // Ensure only one dash
            const parts = value.split('-');
            if (parts.length > 2) {
                value = parts[0] + '-' + parts.slice(1).join('');
            }
            
            // Strict format: Exactly 2 digits before dash, 3 after (XX-XXX)
            if (parts.length === 2) {
                // Limit to 2 digits before dash
                if (parts[0].length > 2) {
                    parts[0] = parts[0].substring(0, 2);
                }
                // Limit to 3 digits after dash
                if (parts[1].length > 3) {
                    parts[1] = parts[1].substring(0, 3);
                }
                value = parts[0] + '-' + parts[1];
            } else if (parts[0].length >= 2 && !value.includes('-')) {
                // Auto-add dash after 2 digits
                const beforeDash = parts[0].substring(0, 2);
                const afterDash = parts[0].substring(2, 5);
                value = beforeDash + (afterDash ? '-' + afterDash : '-');
            }
            
            e.target.value = value;
        });
        
        // Validate on blur - must be exactly XX-XXX format
        input.addEventListener('blur', function(e) {
            const value = e.target.value.trim();
            const exactFormat = /^\d{2}-\d{3}$/;
            
            if (value && !exactFormat.test(value)) {
                e.target.setCustomValidity('Format must be exactly 2 digits, dash, 3 digits (e.g., 32-424)');
                e.target.reportValidity();
            } else {
                e.target.setCustomValidity('');
            }
        });
    }
    
    if (registrationNumberInput) {
        formatNumberWithDash(registrationNumberInput);
    }
    
    if (accreditationNumberInput) {
        formatNumberWithDash(accreditationNumberInput);
    }

    // Field validation with red error indicators
    function validateField(field) {
        const formGroup = field.closest('.form-group');
        const inputWrapper = field.closest('.input-wrapper');
        let isValid = true;
        let errorMessage = '';

        // Remove previous error state
        field.classList.remove('error');
        if (formGroup) {
            formGroup.classList.remove('has-error');
        }

        // Check if field is required and empty
        if (field.hasAttribute('required')) {
            const value = field.value.trim();
            if (!value) {
                isValid = false;
                errorMessage = 'This field is required';
            }
        }

        // Check field type specific validation
        if (field.value.trim() !== '') {
            // Email validation
            if (field.type === 'email') {
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailPattern.test(field.value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid email address';
                }
            }

            // Phone validation
            if (field.id === 'phone' || field.name === 'phone') {
                const phonePattern = /^09[0-9]{9}$/;
                if (!phonePattern.test(field.value)) {
                    isValid = false;
                    errorMessage = 'Phone number must start with 09 and be exactly 11 digits';
                }
            }

            // Password validation
            if (field.id === 'password1' || field.name === 'password1') {
                const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
                if (!passwordPattern.test(field.value)) {
                    isValid = false;
                    errorMessage = 'Password does not meet requirements';
                }
            }

            // Password match validation
            if (field.id === 'password2' || field.name === 'password2') {
                const password1 = document.getElementById('password1');
                if (password1 && field.value !== password1.value) {
                    isValid = false;
                    errorMessage = 'Passwords do not match';
                }
            }

            // Pattern validation
            if (field.hasAttribute('pattern')) {
                const pattern = new RegExp(field.getAttribute('pattern'));
                if (!pattern.test(field.value)) {
                    isValid = false;
                    const title = field.getAttribute('title');
                    errorMessage = title || 'Invalid format';
                }
            }

            // Select validation (check if default/empty option is selected)
            if (field.tagName === 'SELECT') {
                // Skip validation if field is disabled
                if (field.disabled) {
                    return true;
                }
                if (field.value === '' || field.value === null || field.value === '') {
                    if (field.hasAttribute('required')) {
                        isValid = false;
                        errorMessage = 'Please select an option';
                    }
                }
            }
        }

        // Apply error state
        if (!isValid) {
            field.classList.add('error');
            if (formGroup) {
                formGroup.classList.add('has-error');
                
                // Remove existing error message
                const existingError = formGroup.querySelector('.error-message');
                if (existingError) {
                    existingError.remove();
                }
                
                // Add error message
                if (errorMessage) {
                    const errorMsg = document.createElement('span');
                    errorMsg.className = 'error-message';
                    errorMsg.textContent = errorMessage;
                    formGroup.appendChild(errorMsg);
                }
            }
            field.setCustomValidity(errorMessage);
        } else {
            field.classList.remove('error');
            if (formGroup) {
                formGroup.classList.remove('has-error');
                const existingError = formGroup.querySelector('.error-message');
                if (existingError) {
                    existingError.remove();
                }
            }
            field.setCustomValidity('');
        }

        return isValid;
    }

    // Validate all required fields
    function validateAllFields() {
        const form = document.querySelector('.register-form');
        if (!form) return false;

        const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
        let allValid = true;

        requiredFields.forEach(function(field) {
            // Skip hidden fields or disabled fields that are conditionally shown
            if (field.type === 'hidden' || 
                field.disabled || 
                field.style.display === 'none' || 
                (field.closest('.form-group') && field.closest('.form-group').style.display === 'none')) {
                return;
            }

            if (!validateField(field)) {
                allValid = false;
            }
        });

        // Additional validations
        const password1 = document.getElementById('password1');
        const password2 = document.getElementById('password2');
        
        if (password1 && password2 && password1.value && password2.value) {
            if (password1.value !== password2.value) {
                validateField(password2);
                allValid = false;
            }
        }

        return allValid;
    }

    // Add blur event listeners to all form fields
    const formFields = document.querySelectorAll('.form-input, .form-select');
    formFields.forEach(function(field) {
        field.addEventListener('blur', function() {
            validateField(field);
        });

        field.addEventListener('input', function() {
            // Remove error state on input (real-time validation)
            if (field.classList.contains('error')) {
                validateField(field);
            }
        });
    });

    // Validate on form submit
    const registerForm = document.querySelector('.register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            // First, remove all error classes
            const allFields = registerForm.querySelectorAll('.form-input, .form-select');
            allFields.forEach(function(field) {
                field.classList.remove('error');
                const formGroup = field.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
            });
            
            // Check all required fields and add red border to empty ones
            const requiredFields = registerForm.querySelectorAll('input[required], select[required], textarea[required]');
            let hasEmptyFields = false;
            
            requiredFields.forEach(function(field) {
                // Skip hidden fields or disabled fields that are conditionally shown
                if (field.type === 'hidden' || 
                    field.style.display === 'none' || 
                    (field.closest('.form-group') && field.closest('.form-group').style.display === 'none')) {
                    return;
                }
                
                // Check if field is empty
                let isEmpty = false;
                
                if (field.tagName === 'SELECT') {
                    // For select fields, check if value is empty or default option
                    isEmpty = !field.value || field.value === '' || 
                             (field.options[field.selectedIndex] && 
                              field.options[field.selectedIndex].hasAttribute('disabled') &&
                              field.options[field.selectedIndex].hasAttribute('selected'));
                } else if (field.type === 'file') {
                    // For file inputs, check if files are selected
                    isEmpty = !field.files || field.files.length === 0;
                } else {
                    // For text inputs, check if value is empty after trim
                    isEmpty = !field.value || field.value.trim() === '';
                }
                
                // Also check if field is disabled (for cascading dropdowns)
                if (field.disabled && field.hasAttribute('required')) {
                    // Check if it should be enabled based on parent selections
                    const regionSelect = document.getElementById('region');
                    const provinceSelect = document.getElementById('province');
                    const municipalitySelect = document.getElementById('municipality');
                    const barangaySelect = document.getElementById('barangay');
                    const purokInput = document.getElementById('purok');
                    
                    // If it's a cascading dropdown that should be enabled, mark as empty
                    if (field === provinceSelect && regionSelect && !regionSelect.value) {
                        isEmpty = true;
                    } else if (field === municipalitySelect && provinceSelect && !provinceSelect.value) {
                        isEmpty = true;
                    } else if (field === barangaySelect && municipalitySelect && !municipalitySelect.value) {
                        isEmpty = true;
                    } else if (field === purokInput && barangaySelect && !barangaySelect.value) {
                        isEmpty = true;
                    } else {
                        // If disabled but shouldn't be required yet, skip
                        return;
                    }
                }
                
                if (isEmpty) {
                    hasEmptyFields = true;
                    field.classList.add('error');
                    const formGroup = field.closest('.form-group');
                    if (formGroup) {
                        formGroup.classList.add('has-error');
                    }
                }
            });
            
            // Check privacy consent checkbox
            const privacyConsentCheckbox = document.getElementById('privacy_consent');
            if (privacyConsentCheckbox && !privacyConsentCheckbox.checked) {
                e.preventDefault();
                e.stopPropagation();
                
                // Add error styling to checkbox container
                const consentContainer = privacyConsentCheckbox.closest('.form-check');
                if (consentContainer) {
                    consentContainer.style.border = '2px solid #dc2626';
                    consentContainer.style.background = '#fef2f2';
                }
                
                // Show error message
                privacyConsentCheckbox.setCustomValidity('You must agree to the Data Privacy Terms and Agreement to register.');
                privacyConsentCheckbox.reportValidity();
                
                // Scroll to checkbox
                privacyConsentCheckbox.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                return false;
            } else if (privacyConsentCheckbox && privacyConsentCheckbox.checked) {
                // Remove error styling if checkbox is checked
                const consentContainer = privacyConsentCheckbox.closest('.form-check');
                if (consentContainer) {
                    consentContainer.style.border = '1px solid #e2e8f0';
                    consentContainer.style.background = '#f8fafc';
                }
                privacyConsentCheckbox.setCustomValidity('');
            }
            
            // If there are empty required fields, prevent submission
            if (hasEmptyFields) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus on first invalid field
                const firstError = registerForm.querySelector('.error');
                if (firstError) {
                    firstError.focus();
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                
                return false;
            }
            
            // Continue with existing validation
            if (!validateAllFields()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus on first invalid field
                const firstError = registerForm.querySelector('.error');
                if (firstError) {
                    firstError.focus();
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                
                return false;
            }
        });
    }
});
