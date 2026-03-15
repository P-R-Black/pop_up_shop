// Sign-in / Registration modal flow
/*
   Modal Flow:
   1. Initial Screen (signUpTitleOptionsContainer)
      ├→ Email Verification (emailVerificationContainer)
         ├→ Login (emailLoginContainer)
         │  ├→ 2FA (twoFactorAuthContainer)
         │  └→ Forgot Password (forgotPasswordContainer)
         ├→ Registration (emailRegistrationContainer)
         │  └→ Check Email (emailRegistrationCompleteContainer)
         └→ Restore Account (accountPreviouslyDeletedContainer)
   */


// Sign Up Modal
const signUpModal = document.getElementById('signUpModal');
const signUpModalBtn = document.querySelectorAll('.signUpModalBtn');
const closeSignUpModal = document.querySelector('.closeSignUpModal');


// Variables For Signup/Register Modal Home
const signUpTitleOptionsContainer = document.querySelector('.sign_up_title_options_container');
const emailSignUpButton = document.querySelector('.emailSignUpButton');

// Variables for Register/Login by Email
const emailVerificationContainer = document.querySelector('.email_verification_container');
const emailInput = document.getElementById('id_email_check');
const emailSubmitButton = document.querySelector('.emailSubmitButton');

const emailRegistrationContainer = document.querySelector('.register_by_email_container')
const registrationSubmitButton = document.querySelector('.registrationSubmitButton');
const emailRegistrationCompleteContainer = document.querySelector('.register_by_email_complete_container')

const accountPreviouslyDeletedContainer = document.querySelector('.restore_deleted_account_container')


// Variables for container to enter password and sign-in
const emailLoginContainer = document.querySelector('.email_login_container');
const loginSubmitButton = document.querySelector('.loginSubmitButton');
const signUpOptionsFormPasswordInput = document.querySelector('.sign_up_options_form_password'); // class inherted from custom form


// Variables for container to enter 6-digit code
const signUpEmailConfirmContainer = document.querySelector('.sign_up_email_confirm_container');
const confirmSubmitBtn = document.querySelector('.confirm_submit_button');
const confirmInputs = document.querySelectorAll('.confirmation_input input');

// Variable for password reset
const emailPasswordResetInput = document.getElementById('email_password_reset_form'); // class inherted from custom form

// Variables for Register/Login by Facebook
const fbBtn = document.getElementById("facebookSignUpButton");
const fbUrl = document.getElementById("facebookLoginUrl").value;
const socialVerificationContainer = document.querySelector('.social_registration_container')

// Google Sign Button and Values
const googleBtn = document.getElementById("googleSignUpButton");
const googleUrl = document.getElementById("googleLoginUrl").value;


// Timer Display for 2 factor auth 
const timerDisplay = document.querySelector('#code_timer');

let emailOnFile;




document.addEventListener("DOMContentLoaded", () => {

    if (!fbBtn || !fbUrl || !googleBtn || !googleUrl) return;

    fbBtn.addEventListener("click", (e) => {
        e.preventDefault();

        openPopUp(fbUrl)


    });


    googleBtn.addEventListener('click', (e) => {
        e.preventDefault()
        console.log('google Button Clicked')
        openPopUp(googleUrl)

    })


    const firstFocusable = signUpModal.querySelector('button, input, a, [tabindex]:not([tabindex="-1"])')
    // Opens Register / Login Modal
    if (signUpModalBtn) {
        signUpModal.dataset.triggerElement = document.activeElement;

        signUpModalBtn.forEach((sub) => {
            sub.addEventListener('click', () => {
                signUpModal.style.display = 'block';
                signUpModal.setAttribute('aria-hidden', 'false');

                // move focus into modal
                firstFocusable.focus();

                // Trap focus within modal
                trapFocus(signUpModal);
            })
        })
    } else {
        console.warn('signup button not found in the DOM.');
    }

    if (closeSignUpModal) {
        // Close the modal when the close span is clicked
        closeSignUpModal.addEventListener('click', function () {
            signUpModal.style.display = 'none';
        });
    } else {
        console.warn('closeModal span not found in the DOM.');
    }

    // Close the modal when clicking outside of it
    if (signUpModal) {
        window.addEventListener('click', function (event) {
            if (event.target === signUpModal) {
                signUpModal.style.display = 'none';
                signUpModal.setAttribute('aria-hidden', 'true');

                const triggerElement = this.document.querySelector(`[data-trigger="${modal.id}"]`) || this.document.getElementById(signUpModal.dataset.triggerElement);

                if (triggerElement) {
                    triggerElement.focus();
                }
            }
        });
    } else {
        console.warn('bidModal not found in the DOM.');
    }


    // Trap focus within modal
    function trapFocus(element) {
        const focusableElements = element.querySelectorAll(
            'button:not([disabled]), [href], input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        element.addEventListener('keydown', function (e) {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    // shift + Tab (backwards)
                    if (document.activeElement === firstFocusable) {
                        lastFocusable.focus();
                        e.preventDefault();
                    }
                } else {
                    // Tab (forwards)
                    if (document.activeElement === lastFocusable) {
                        firstFocusable.focus()
                        e.preventDefault();
                    }
                }
            }
            if (e.key === 'Escape') {
                closeSignUpModal();
            }
        })
    }




    // From Sign in Modal Home
    if (emailSignUpButton) {
        emailSignUpButton.addEventListener('click', () => {
            console.log('email clicked')
            newMoveForwardSignIn(signUpTitleOptionsContainer, emailVerificationContainer)
        })
    }

    // CONTINUE WITH EMAIL CONTAINER
    // enter email, if on file go to password container
    // enter email, if not on file, go to register container
    // back modal button user back to modal home page with google, facebook, email sign-in options


    // Disable Email Submit Button
    emailInput.addEventListener('input', () => {
        emailSubmitButton.disabled = !emailInput.value.includes('@');

    });


    // Email submitted and checked if on file.
    // If not on file, take to register
    // If email on file, take to password entry
    if (emailSubmitButton) {
        emailSubmitButton.addEventListener('click', (e) => {
            console.log('button clicked!')
            e.preventDefault();

            const form = emailSubmitButton.closest('form');
            const formData = new FormData(form);
            const emailProvidedSigninPopup = document.querySelectorAll('.email_provided_signin_popup');

            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    console.log('data is', data)
                    console.log('data.status is', data.status)

                    if (data.status === false) {
                        // move forward to password login container
                        newMoveForwardSignIn(emailVerificationContainer, emailLoginContainer)
                        emailProvidedSigninPopup.forEach((epp) => epp.innerHTML = formData.get('email'));

                    } else if (data.status === true) {
                        const email = formData.get('email');
                        sessionStorage.setItem('auth_email', email);

                        // Go to registration container
                        newMoveForwardSignIn(emailVerificationContainer, emailRegistrationContainer)
                        emailProvidedSigninPopup.forEach((epp) => epp.innerHTML = formData.get('email'));

                        // Pre-fill email in registration form
                        const registrationEmailInput = document.querySelector('#id_reg_email');
                        if (registrationEmailInput) {
                            registrationEmailInput.value = email;
                        }

                    } else if (data.status == 'inactive') {
                        // Email on file but not verified, got check email container
                        newMoveForwardSignIn(emailVerificationContainer, emailRegistrationCompleteContainer)

                    } else if (data.status == 'deleted') {
                        // Email still on file after being deleted
                        newMoveForwardSignIn(emailVerificationContainer, accountPreviouslyDeletedContainer)
                        emailProvidedSigninPopup.forEach((epp) => {
                            epp.innerHTML = formData.get('email')
                            emailOnFile = epp.innerHTML;
                        });

                    } else {
                        console.error('Unexpected response:', data);
                    }
                })
                .catch(error => {
                    console.error('Error submitting email:', error);
                });
        });
    }


    // LOGIN CONTAINER
    // if we go back should go back to EMAIL Container where user enters email
    // after password "submit button is pressed" -> forward should be the 6-digit code page
    // after Password Entered, 2f Auth Form


    // Disable Password Submit Button
    signUpOptionsFormPasswordInput.addEventListener('input', () => {
        loginSubmitButton.disabled = signUpOptionsFormPasswordInput.value.length < 8;
    });

    // After Password Entered, 2f Auth Form
    if (loginSubmitButton) {
        loginSubmitButton.addEventListener('click', (e) => {
            e.preventDefault()
            console.log("I've been clicked!")

            const form = loginSubmitButton.closest('form');
            const formData = new FormData(form);


            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data['authenticated'] === true) {
                        newMoveForwardSignIn(emailLoginContainer, signUpEmailConfirmContainer);
                        setTimeout(() => {
                            const fiveMinutes = 5 * 60;
                            startCodeTimer(fiveMinutes, timerDisplay)
                        }, 100)


                    } else if (data['authenticated'] === false) {
                        console.error('Unexpected response:', data);
                        const loginUserOptionsError = document.querySelector('.login_user_options_error');
                        loginUserOptionsError.style.display = "block";
                        loginUserOptionsError.textContent = "Invalid Credentials Provided";
                        loginUserOptionsError.style.fontSize = "20px"
                        if (data.error === "Invalid credentials. Attempt 5/5") {
                            loginUserOptionsError.textContent = "Too many failed attempts. Try again in 15 minutes"
                        } else {
                            loginUserOptionsError.textContent = "Invalid Credentials Provided"
                        }
                    } else if (data['authenticated'] === false && data['locked_out'] === true) {
                        loginUserOptionsError.style.textAlign = "center"
                        loginUserOptionsError.textContent = data.error

                    }
                })
                .catch(error => {
                    console.error('Error submitting password', error)
                })
        })
    }



    // CONFIRMATION CONTAINER FOR 6-DIGIT CODE
    // if submit approved, user signed in
    // if back button hit, user goes back to Password Entry Container

    // 2f auth confirmation
    if (confirmSubmitBtn) {
        confirmSubmitBtn.addEventListener('click', (e) => {
            console.log('confirm_submit_button clicked!')
            e.preventDefault();

            const code = Array.from(confirmInputs).map(input => input.value.trim()).join('');

            console.log('code', code)

            if (code.length != 6) {
                alert("Please enter the full 6-digit code.");
                return;
            }
            const csrfToken = getCookie('csrftoken'); // <- use cookie


            if (!csrfToken) {
                console.error('CSRF token not found.')
                return;
            }

            fetch('/pop_accounts/auth/verify-code/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ code })
            })
                .then(async (response) => {
                    console.log('response in confirmSubmitBtn', response)
                    const data = await response.json();
                    console.log('data', data)
                    if (!response.ok) {
                        throw new Error(data.error || `HTTP error! status: ${response.status}`);
                    }
                    return data;
                })
                .then(data => {
                    if (data.verified) {
                        if (signUpModal) signUpModal.style.display = 'none';
                        window.location.reload()
                    } else {
                        alert(data.error || 'Invalid code.');
                    }
                })
                .catch(err => {
                    console.error('Two-Factor Authentication verification failed', err);
                    alert(err.message || 'Something went wrong.')
                });
        });
    }

    // 2FA Tab On Input Entry
    document.querySelectorAll('.code-input').forEach((input, index, inputs) => {
        input.addEventListener('input', () => {
            if (input.value.length === input.maxLength && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }
        });

    });

    // Backspace to empty input for 2FA
    document.querySelectorAll('.code-input').forEach((input, index, inputs) => {
        input.addEventListener('input', () => {
            if (input.value.length === input.maxLength && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !input.value && index > 0) {
                inputs[index - 1].focus();
            }
        });
    });


    // Submit Registration Form
    if (registrationSubmitButton) {
        registrationSubmitButton.addEventListener('click', function (e) {
            e.preventDefault();
            const form = registrationSubmitButton.closest('form');
            const formData = new FormData(form);

            // Inject email from sessionStorage if not in form
            const storedEmail = sessionStorage.getItem('auth_email');

            if (storedEmail) {
                formData.set('email', storedEmail);  // Ensure it’s part of the POST data
            }

            fetch('/pop_accounts/auth/register/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.registered) {
                        newMoveForwardSignIn(emailRegistrationContainer, emailRegistrationCompleteContainer)
                    } else if (data.errors) {
                        displayFormErrorsTwo(data.errors);
                    }
                })
                .catch(error => {
                    console.error('Error submitting registration form:', error);
                });
        });
    }


    // Forgot password
    const passwordForgetLink = document.querySelector('.passwordForgetLink');
    const passwordForgetContainer = document.querySelector('.forgot_password_container'); // this is the next container


    if (passwordForgetLink) {
        passwordForgetLink.addEventListener('click', () => {
            console.log('forgot password has been called!')
            newMoveForwardSignIn(emailLoginContainer, passwordForgetContainer)
        })
    }


    // Enter email for password reset
    const emailPasswordResetInput = document.querySelector('.email_password_reset_form'); // class inherted from custom form
    const resetPasswordBtn = document.querySelector('.resetPasswordBtn')

    // Forgot your password container
    const forgotPasswordEmailCheckContainer = document.querySelector('.forgot_password_email_check_container')


    // makes "continue" button in forgot password container pressable
    emailPasswordResetInput.addEventListener('input', () => {
        resetPasswordBtn.disabled = !emailPasswordResetInput.value.includes('@');
    })

    if (resetPasswordBtn) {
        resetPasswordBtn.addEventListener('click', (e) => {

            e.preventDefault();

            console.log('resetPasswordBtn button clicked!')

            const email = emailPasswordResetInput.value.trim();

            // Client side validation
            if (!email || !email.includes('@')) {
                alert('Please enter a valid email address');
                return;
            }


            const csrfToken = getCookie('csrftoken');
            const originalButtonText = resetPasswordBtn.textContent;
            const resetSpinner = document.getElementById('resetSpinner');



            // Show spiner
            resetSpinner.style.display = 'block'
            // Disable button so user can't click twice
            resetPasswordBtn.disabled = true
            resetPasswordBtn.textContent = 'Sending...';


            fetch('/pop_accounts/auth/send-reset-link/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ email })
            })
                .then(response => {
                    if (response.status == 429) {
                        console.log('Reset Password test 429 response:', response)
                        throw new Error('Too many atttempts. Please try again later.')
                    }
                    return response.json()
                })
                .then(data => {
                    if (data.success) {
                        console.log('Reset Password test data.success:', data)
                        newMoveForwardSignIn(passwordForgetContainer, forgotPasswordEmailCheckContainer)
                        announceScreenChange('Password reset link sent. Please check your email.')
                    } else {
                        console.log('Reset Password test else block:', data)
                        // Show error message
                        const errorMessage = data.error || 'Unable to send reset link. Please try again.'

                        // Display error in UI (create error container if needed)
                        const errorContainer = document.querySelector('.password-reset-error');
                        if (errorContainer) {
                            errorContainer.textContent = errorMessage;
                            errorContainer.style.display = 'block';
                            errorContainer.setAttribute('role', 'alert');
                        }

                        // Also show alert as fallback
                        alert(errorMessage);
                    }
                })
                .catch(error => {
                    console.error('Error sending password reset link:', error);
                })
                .finally(() => {
                    // Hide spiner, reset button text, re-enable button
                    if (resetSpinner) {
                        resetSpinner.style.display = 'none';
                    }
                    resetPasswordBtn.disabled = false;
                    resetPasswordBtn.textContent = originalButtonText
                })
        })
    }


    // Resend 6-digit code for 2 factor auth.
    const resendLink = document.getElementById('resend_code_link');
    const statusMessage = document.getElementById('resend_status_message');
    resendLink.addEventListener('click', (e) => {
        e.preventDefault();

        resendLink.style.pointerEvents = 'none';
        resendLink.style.opacity = ' 0.5';
        statusMessage.style.display = 'none';

        fetch('/pop_accounts/resend-code/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    statusMessage.textContent = "A new code was sent!"
                    statusMessage.style.display = "block";
                    confirmSubmitBtn.classList.remove('disabled_button');
                    confirmSubmitBtn.disabled = false
                    confirmSubmitBtn.innerText = "Submit"

                    // Resetart the timer
                    startCodeTimer(5 * 60, timerDisplay);

                    setTimeout(() => {
                        resendLink.style.pointerEvents = 'auto';
                        resendLink.style.opacity = '1';
                        statusMessage.style.display = 'none'
                    }, 15000);
                } else {
                    statusMessage.textContent = data.error || "Something went wrong."
                    statusMessage.style.color = 'red';
                    statusMessage.style.display = 'block';
                }
            }).catch(err => {
                statusMessage.textContent = "Error resending code.";
                statusMessage.style.color = "red";
                statusMessage.style.display = "block"
            })
    })




    const restoreDeletedAccount = document.getElementById('restoreDeletedAccount');
    const notRestoreDeletedAccount = document.getElementById('notRestoreDeletedAccount');

    if (notRestoreDeletedAccount) {
        notRestoreDeletedAccount.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('they said no! so take them back to email screen')
        })
    }

    if (restoreDeletedAccount) {
        restoreDeletedAccount.addEventListener('click', (e) => {
            e.preventDefault()
            fetch("/pop_accounts/restore-account/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({ email: emailOnFile })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.status) {
                        newMoveForwardSignIn(accountPreviouslyDeletedContainer, emailRegistrationCompleteContainer)
                    }
                })
        })
    }


    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function () {
            // Get the target input ID from data-target attribute
            const targetId = this.getAttribute('data-target');
            const passwordInput = document.getElementById(targetId);

            if (!passwordInput) {
                console.error('Password input not found:', targetId);
                return;
            }

            const isPressed = this.getAttribute('aria-pressed') === 'true';
            const icon = this.querySelector('i');

            // Toggle password visibility
            passwordInput.type = isPressed ? 'password' : 'text';

            // Update button state
            this.setAttribute('aria-pressed', !isPressed);
            this.setAttribute('aria-label', isPressed ?
                this.getAttribute('aria-label').replace('Hide', 'Show') :
                this.getAttribute('aria-label').replace('Show', 'Hide')
            );

            // Toggle icon
            if (icon) {
                if (isPressed) {
                    icon.classList.remove('bx-hide');
                    icon.classList.add('bx-show');
                } else {
                    icon.classList.remove('bx-show');
                    icon.classList.add('bx-hide');
                }
            }
        });
    });

})

const ANIMATION_DURATION = 300;

const newMoveForwardSignIn = (containerToHide, containerToShow) => {

    // Show container first so it gets a width
    containerToShow.style.display = 'block';
    containerToShow.style.visibility = 'hidden';
    containerToShow.removeAttribute('hidden');

    // Force browswer to calculate dimensions
    containerToShow.offsetHeight;

    // Now make it visible and start animation
    containerToShow.style.visibility = 'visible';
    containerToShow.classList.remove('hide_container');
    containerToShow.classList.add('show_container');
    containerToShow.setAttribute('aria-hidden', 'false');

    // Small delay to ensure width is calcuated
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            // Now start the animation
            containerToShow.classList.add('slide_in_right');
            containerToHide.classList.add('slide_out_left');
        });
    });

    // Clean up after animation
    setTimeout(() => {
        containerToHide.classList.remove('show_container', 'slide_out_left');
        containerToHide.classList.add('hide_container');
        containerToHide.setAttribute('hidden', '');
        containerToHide.setAttribute('aria-hidden', 'true');

        // Must Clear inline styles
        containerToHide.style.display = '';
        containerToHide.style.visibility = '';

        containerToShow.classList.remove('slide_in_right');

        // Clear inline styles on shown container too
        containerToShow.style.display = '';
        containerToShow.style.visibility = '';

    }, ANIMATION_DURATION)

    // Accessibility
    switchToScreen(containerToShow);

    const heading = containerToShow.querySelector('h3');
    if (heading) {
        announceScreenChange(heading.textContent);
    }


}


function newMoveBackwardSignIn(nameOfContainerToHide, nameOfContainerToShow) {

    const containerToHide = document.querySelector(nameOfContainerToHide);
    const containerToShow = document.querySelector(nameOfContainerToShow);

    // Remove hidden attribute First (gives it width)
    containerToShow.removeAttribute('hidden');
    containerToShow.classList.remove('hide_container');
    containerToShow.classList.add('show_container');
    containerToShow.setAttribute('aria-hidden', 'false');

    // Force reflow to calculate dimentions
    containerToHide.style.visibility = 'hidden'
    containerToHide.classList.add('slide_out_right');
    containerToShow.classList.add('slide_in_left');

    // clean up after animation completes
    setTimeout(() => {
        containerToHide.classList.remove('show_container', 'slide_out_right');
        containerToHide.classList.add('hide_container');
        containerToHide.setAttribute('hidden', '');
        containerToHide.setAttribute('aria-hidden', 'true');

        // Must Clear inline styles
        containerToHide.style.display = '';
        containerToHide.style.visibility = '';

        containerToShow.classList.remove('slide_in_left');

        // Clear inline styles on shown container too
        containerToShow.style.display = '';
        containerToShow.style.visibility = '';

    }, ANIMATION_DURATION);

    // Accessibility
    switchToScreen(containerToShow);
    const heading = containerToShow.querySelector('h3');
    if (heading) {
        announceScreenChange('Back to ' + heading.textContent)
    }

}

// Update aria-labelledby when screen changes
function switchToScreen(screenElement) {
    const h3Heading = screenElement.querySelector('h3');
    if (h3Heading && h3Heading.id) {
        signUpModal.setAttribute('aria-labelledby', h3Heading.id);

        // Focus on first input or heading
        const firstInput = screenElement.querySelector('input, button');
        if (firstInput) {
            firstInput.focus();
        }
    }
}

// Announce Screen Change
function announceScreenChange(message) {
    const announcer = document.getElementById('modalAnnouncer');
    announcer.textContent = message;

    // Clear after announcement
    setTimeout(() => {
        announcer.textContent = '';
    }, 1000);
}

// Usage
function showRegistrationForm() {
    // Show the form
    announceScreenChange('Create account form loaded')
}




// 2F Auth Timer
let countdownInterval = null; // global reference to active interval
const startCodeTimer = (duration, display) => {
    let timer = duration;

    // clear any existing interval
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }

    countdownInterval = setInterval(() => {
        const minutes = Math.floor(timer / 60)
        const seconds = timer % 60;

        display.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        if (--timer < 0) {
            clearInterval(countdownInterval);
            countdownInterval = null; // reset global variable

            display.textContent = "Time Has Expired, Request Another";
            display.style.textAlign = "center";

            // Optional Disable from submissions or show a message

            if (confirmSubmitBtn) {
                confirmSubmitBtn.disabled = true;

                confirmSubmitBtn.innerText = "Code Expired";
                confirmSubmitBtn.classList.add('disabled_button');
                confirmSubmitBtn.style.width = "128px";
            }
        }
    }, 1000);
}



// Opens PopUp For Facebook & Google for Social Sign-in
function openPopUp(socialUrl) {
    const width = 550, height = 600;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;

    const socialPopup = window.open(
        socialUrl,
        "socialPopUp",
        `width=${width},height=${height}, top=${top}, left=${left}`
    );

    if (!socialPopup) {
        return;
    }

    pollLoginStatus(socialPopup)

}


// Polls Social Login For User Data Need to Update UI
function pollLoginStatus(socialPopup) {
    let loginProcessing = false;
    let checkCount = 0;

    const checkLoginStatus = setInterval(async () => {
        checkCount++;

        try {
            const response = await fetch('/pop_accounts/social-login-complete/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });


            if (response.ok) {
                const userData = await response.json();

                console.log(`checkCount: ${checkCount}: userData: ${userData}`)

                if (userData.authenticated && !loginProcessing) {
                    loginProcessing = true;
                    clearInterval(checkLoginStatus);

                    updateNavigationWithUserData(userData);

                    // Close popup
                    setTimeout(() => {
                        try {
                            socialPopup.close();
                        } catch (error) {
                            console.error(error);
                        }
                    }, 1500);
                    return;
                }
            } else {
                console.log(`Response not OK`);
            }
        } catch (error) {
            console.log(`Fetch error:`, error.message);
        }

        // Stop checking after 5 minutes
        if (checkCount > 600) {
            console.log('Authentication checking timeout after 10 minutes');
            clearInterval(checkLoginStatus);
        }
    }, 500);
}



// Updates UI After Social Log-in
function updateNavigationWithUserData(userData) {

    // Update greeting
    const greetingsBox = document.getElementById("greetings_box_name");
    const greetingsContainer = document.getElementById("greetings_container");
    if (greetingsBox && greetingsContainer) {
        greetingsBox.textContent = `Hello ${userData.firstName}`;
        greetingsContainer.style.display = "block";
    }

    // Remove login/signup buttons
    const loginBtn = document.getElementById("login_button");
    const signupBtn = document.getElementById("signup_button");

    if (loginBtn) {
        loginBtn.remove();
    }
    if (signupBtn) {
        signupBtn.remove();
    }

    // Add logout button
    const menuLinks = document.getElementById("menu-links");

    if (menuLinks && !document.querySelector('a[href*="dashboard"]')) {
        let dashboardLink;

        if (userData.isStaff) {
            dashboardLink = `
                <li class="nav-link">
                    <a href="/pop_accounts/dashboard-admin/">
                        <i class='bx bxs-user-detail icon' aria-hidden="trueß"></i>
                        <span class="text nav-text">Dashboard</span>
                    </a>
                </li>
            `;
            console.log('Adding admin dashboard link');
        } else {
            dashboardLink = `
                <li class="nav-link">
                    <a href="/pop_accounts/dashboard/">
                        <i class='bx bxs-user-detail icon'></i>
                        <span class="text nav-text">Dashboard</span>
                    </a>
                </li>
            `;
        }

        // Insert dashboard after Home (find the Home link and insert after it)
        const homeLink = document.querySelector('a[href="/"]')?.closest('li');
        if (homeLink) {
            homeLink.insertAdjacentHTML("afterend", dashboardLink);
        } else {
            // Fallback: insert at beginning of menu
            menuLinks.insertAdjacentHTML("afterbegin", dashboardLink);
        }
    }

    if (menuLinks && !document.getElementById("logout_form")) {
        const csrfToken = getCSRFToken();

        if (!csrfToken) {
            console.error('CSRF token not found - logout may fail');
            return;
        }

        const logoutForm = `
                    <li class="nav-link">
                        <button type="submit" onclick="performLogout(event)">
                            <i class='bx bx-log-out icon' aria-hidden="true"></i>
                            <span class="text nav-text">Log out</span>
                        </button>
                    </li>
            `;

        // Insert before the Dark Mode li element instead of at the end
        const darkModeElement = document.querySelector("li.mode");
        if (darkModeElement) {
            darkModeElement.insertAdjacentHTML("beforebegin", logoutForm);
        } else {
            // Fallback: add at end if Dark Mode element not found
            menuLinks.insertAdjacentHTML("beforeend", logoutForm);
        }

    }


    // Close login modal
    if (signUpModal) {
        signUpModal.style.display = 'none';
        // Remove any modal backdrop if it exists
        const modalBackdrop = document.querySelector('.modal-backdrop');
        if (modalBackdrop) {
            modalBackdrop.remove();
        }
        // Remove fade class and hide modal
        signUpModal.classList.remove('show');
        signUpModal.setAttribute('aria-hidden', 'true');

        console.log('Sign up modal closed');
    }
}



function getCSRFToken() {
    // Method 1: From cookie
    const name = 'csrftoken';
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

    // Method 2: From meta tag (fallback)
    if (!cookieValue) {
        const csrfMeta = document.querySelector('[name=csrfmiddlewaretoken]');
        cookieValue = csrfMeta ? csrfMeta.getAttribute('content') : null;
    }

    return cookieValue;
}




async function performLogout(event) {
    event.preventDefault();
    try {
        const csrfToken = getCSRFToken();

        if (!csrfToken) {
            window.location.href = '/';
            return;
        }

        const response = await fetch('/pop_accounts/logout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
            },
            body: `csrfmiddlewaretoken=${encodeURIComponent(csrfToken)}`,
            credentials: 'same-origin'
        });

        // Always redirect, don't wait for response parsing
        if (response.ok) {
            window.location.href = '/'; // redirect home
        } else {
            window.location.href = '/';
        }

    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/';
    }
}