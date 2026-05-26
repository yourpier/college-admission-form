// ====================== ACCORDION ======================
function toggleAccordion(header) {
    const item = header.parentElement;
    item.classList.toggle('active');
}

// ====================== TRANSFeree ======================
function toggleTransferee() {
    const isChecked = document.getElementById('isTransferee').checked;
    const fieldsContainer = document.getElementById('transfereeFields');
    
    if (fieldsContainer) {
        fieldsContainer.style.display = isChecked ? 'block' : 'none';
    }

    const inputs = fieldsContainer.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        if (isChecked) {
            input.setAttribute('required', 'required');
        } else {
            input.removeAttribute('required');
            clearError(input);
        }
    });
}

// ====================== EMAIL VALIDATION ======================
function isValidEmail(email) {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return regex.test(email);
}

function validateEmailField() {
    const emailInput = document.getElementById('primary_contact_email');
    if (!emailInput) return;

    const emailHelp = document.getElementById('emailHelp');

    emailInput.addEventListener('blur', function() {
        if (!this.value) return;

        if (!isValidEmail(this.value)) {
            this.style.borderColor = '#ef4444';
            if (emailHelp) {
                emailHelp.style.color = '#ef4444';
                emailHelp.textContent = "Please enter a valid email address (e.g., example@gmail.com)";
            }
        } else {
            this.style.borderColor = '';
            if (emailHelp) {
                emailHelp.style.color = '#666';
                emailHelp.textContent = "Must be a valid email address";
            }
        }
    });

    // Clear error while typing
    emailInput.addEventListener('input', function() {
        if (this.value === '') {
            this.style.borderColor = '';
        }
    });
}

// ====================== ERROR HANDLING ======================
function showError(input, message) {
    let errorDiv = input.parentElement.querySelector('.error-message');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        input.parentElement.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
    input.style.borderColor = '#ef4444';
    input.style.backgroundColor = '#fef2f2';
}

function clearError(input) {
    const errorDiv = input.parentElement.querySelector('.error-message');
    if (errorDiv) errorDiv.remove();
    input.style.borderColor = '';
    input.style.backgroundColor = '';
}

function clearAllErrors() {
    document.querySelectorAll('.error-message').forEach(el => el.remove());
    document.querySelectorAll('input, textarea, select').forEach(input => {
        input.style.borderColor = '';
        input.style.backgroundColor = '';
    });
}

// ====================== FORM SUBMISSION ======================
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('admissionForm');
    const submitBtn = document.getElementById('submitBtn');

    // Setup email validation
    validateEmailField();

    if (form && submitBtn) {
        form.addEventListener('submit', function(e) {
            clearAllErrors();
            let isValid = true;
            let firstErrorField = null;

            const requiredFields = form.querySelectorAll('[required]');

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    let message = "This field is required";
                    if (field.name === 'course') message = "Previous Course is required";
                    if (field.name === 'reason_for_transfer') message = "Reason for Transfer is required";
                    if (field.name === 'gwa') message = "GWA is required";
                    if (field.name === 'lrn') message = "LRN is required";

                    showError(field, message);
                    if (!firstErrorField) firstErrorField = field;
                }
            });

            if (!isValid) {
                e.preventDefault();
                if (firstErrorField) {
                    firstErrorField.scrollIntoView({ behavior: "smooth", block: "center" });
                    firstErrorField.focus();
                }
                return false;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting... Please wait';
        });
    }

    const firstNameField = document.getElementById('first_name');
    if (firstNameField) firstNameField.focus();

    checkSuccessMessage();
});

// Success Handler
function checkSuccessMessage() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === '1') {
        document.getElementById('successMessage').style.display = 'block';
        document.querySelector('.form-content').style.display = 'none';
        document.getElementById('applicantId').textContent = urlParams.get('id');
    }
}