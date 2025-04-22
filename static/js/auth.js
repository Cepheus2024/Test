/**
 * Authentication JavaScript
 * Handles login, registration, and profile functionality
 */

// Initialize authentication functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize registration form validation
    initializeRegistrationValidation();
    
    // Initialize profile form functionality
    initializeProfileForm();
    
    // Initialize login form
    initializeLoginForm();
});

/**
 * Initializes registration form validation
 */
function initializeRegistrationValidation() {
    const registrationForm = document.getElementById('registrationForm');
    
    if (registrationForm) {
        const passwordInput = document.getElementById('password');
        const confirmPasswordInput = document.getElementById('confirm_password');
        const passwordMatch = document.getElementById('passwordMatch');
        
        // Function to check if passwords match
        function checkPasswordsMatch() {
            if (confirmPasswordInput.value && passwordInput.value !== confirmPasswordInput.value) {
                passwordMatch.innerHTML = 'Passwords do not match';
                passwordMatch.className = 'form-text text-danger';
                return false;
            } else if (confirmPasswordInput.value) {
                passwordMatch.innerHTML = 'Passwords match';
                passwordMatch.className = 'form-text text-success';
                return true;
            } else {
                passwordMatch.innerHTML = '';
                return false;
            }
        }
        
        // Add event listeners for password validation
        confirmPasswordInput.addEventListener('input', checkPasswordsMatch);
        passwordInput.addEventListener('input', function() {
            if (confirmPasswordInput.value) {
                checkPasswordsMatch();
            }
        });
        
        // Validate form on submission
        registrationForm.addEventListener('submit', function(e) {
            // Check if fields are valid
            let isValid = true;
            
            // Username validation
            const usernameInput = document.getElementById('username');
            if (usernameInput.value.trim() === '') {
                isValid = false;
                highlightInvalidField(usernameInput, 'Username is required');
            } else {
                removeInvalidHighlight(usernameInput);
            }
            
            // Email validation
            const emailInput = document.getElementById('email');
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(emailInput.value)) {
                isValid = false;
                highlightInvalidField(emailInput, 'Valid email is required');
            } else {
                removeInvalidHighlight(emailInput);
            }
            
            // Password validation
            if (passwordInput.value.length < 6) {
                isValid = false;
                highlightInvalidField(passwordInput, 'Password must be at least 6 characters');
            } else {
                removeInvalidHighlight(passwordInput);
            }
            
            // Confirm password validation
            if (passwordInput.value !== confirmPasswordInput.value) {
                isValid = false;
                highlightInvalidField(confirmPasswordInput, 'Passwords do not match');
            } else {
                removeInvalidHighlight(confirmPasswordInput);
            }
            
            // Full name validation
            const fullnameInput = document.getElementById('fullname');
            if (fullnameInput.value.trim() === '') {
                isValid = false;
                highlightInvalidField(fullnameInput, 'Full name is required');
            } else {
                removeInvalidHighlight(fullnameInput);
            }
            
            // Prevent form submission if invalid
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
}

/**
 * Highlights an invalid form field
 * @param {HTMLElement} element - The form input element
 * @param {string} message - The error message
 */
function highlightInvalidField(element, message) {
    element.classList.add('is-invalid');
    
    // Add or update feedback message
    let feedbackElement = element.nextElementSibling;
    if (!feedbackElement || !feedbackElement.classList.contains('invalid-feedback')) {
        feedbackElement = document.createElement('div');
        feedbackElement.className = 'invalid-feedback';
        element.parentNode.insertBefore(feedbackElement, element.nextSibling);
    }
    
    feedbackElement.textContent = message;
}

/**
 * Removes invalid highlight from a form field
 * @param {HTMLElement} element - The form input element
 */
function removeInvalidHighlight(element) {
    element.classList.remove('is-invalid');
    element.classList.add('is-valid');
    
    // Remove any existing feedback
    const feedbackElement = element.nextElementSibling;
    if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
        feedbackElement.textContent = '';
    }
}

/**
 * Initializes profile form functionality
 */
function initializeProfileForm() {
    const profileForm = document.getElementById('profileForm');
    
    if (profileForm) {
        // Implement profile form validation and functionality
        profileForm.addEventListener('submit', function(e) {
            // Basic validation
            const fullnameInput = document.getElementById('fullname');
            if (fullnameInput && fullnameInput.value.trim() === '') {
                e.preventDefault();
                highlightInvalidField(fullnameInput, 'Full name is required');
            }
        });
    }
}

/**
 * Initializes login form functionality
 */
function initializeLoginForm() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // Validate username and password fields
            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');
            let isValid = true;
            
            if (usernameInput.value.trim() === '') {
                isValid = false;
                highlightInvalidField(usernameInput, 'Username is required');
            } else {
                removeInvalidHighlight(usernameInput);
            }
            
            if (passwordInput.value === '') {
                isValid = false;
                highlightInvalidField(passwordInput, 'Password is required');
            } else {
                removeInvalidHighlight(passwordInput);
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
}
