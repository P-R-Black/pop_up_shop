const body = document.querySelector('body')
const sidebar = body.querySelector('.sidebar')
const toggle = body.querySelector('.toggle')
const searchBtn = body.querySelector('.search-box')
const modeSwitch = body.querySelector('.toggle-switch')
const modeText = body.querySelector('.mode-text')
const navLogoText = body.querySelector('.logo-text')

const mobileMoon = body.querySelector('.mobile-moon')
const mobileSun = body.querySelector('.mobile-sun')
const mobileSearchBox = body.querySelector('.mobile-search-box')
const mobileSearchIcon = body.querySelector('#mobile-search-icon')


const signUpModal = document.getElementById('signUpModal');
const signUpModalBtn = document.querySelectorAll('.signUpModalBtn');
const closeSignUpModal = document.querySelector('.closeSignUpModal');

const timerDisplay = document.querySelector('#code_timer');


// 2f auth confirmation
const confirmSubmitBtn = document.querySelector('.confirm_submit_button');
const confirmInputs = document.querySelectorAll('.confirmation_input input');



function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        if (cookie.trim().startsWith(name + '=')) {
            return decodeURIComponent(cookie.trim().split('=')[1]);
        }
    }
    return '';
}


// sign-up moddal
document.addEventListener('DOMContentLoaded', function () {
    // Get the modal, button, and close span


    // if (signUpModalBtn) {
    //     signUpModalBtn.forEach((sub) => {
    //         sub.addEventListener('click', () => {
    //             signUpModal.style.display = 'block';
    //         })
    //     })
    // } else {
    //     console.warn('bidButton not found in the DOM.');
    // }


    // if (closeSignUpModal) {
    //     // Close the modal when the close span is clicked
    //     closeSignUpModal.addEventListener('click', function () {
    //         signUpModal.style.display = 'none';
    //     });
    // } else {
    //     console.warn('closeModal span not found in the DOM.');
    // }

    // // Close the modal when clicking outside of it
    // if (signUpModal) {
    //     window.addEventListener('click', function (event) {
    //         if (event.target === signUpModal) {
    //             signUpModal.style.display = 'none';
    //         }
    //     });
    // } else {
    //     console.warn('bidModal not found in the DOM.');
    // }
});


// sign up email modal 
document.addEventListener('DOMContentLoaded', function () {
    const backChevron = document.getElementById('backChevron');
    const signUpTitleOptionsContainer = document.querySelector('.sign_up_title_options_container');
    const emailVerificationContainer = document.querySelector('.email_verification_container');
    const emailSignUpButton = document.querySelector('.emailSignUpButton');

    const signUpEmailContainer = document.querySelector('.sign_up_email_container');
    const signUpEmailInput = document.querySelector('.sign_up_options_form_email');
    const emailSubmitButton = document.querySelector('.emailSubmitButton');

    const emailLoginContainer = document.querySelector('.email_login_container');

    const confirmContainerBackChevron = document.getElementById('confirmContainerBackChevron');

    const confirmContainerBackChevronTwo = document.getElementById('confirmContainerBackChevronTwo');
    const confirmContainerBackChevronThree = document.getElementById('confirmContainerBackChevronThree');
    const confirmContainerBackChevronFour = document.getElementById('confirmContainerBackChevronFour');

    const confirmContainerBackChevronSix = document.getElementById('confirmContainerBackChevronSix');
    const signUpEmailConfirmContainer = document.querySelector('.sign_up_email_confirm_container');

    const signUpOptionsFormPasswordInput = document.querySelector('.sign_up_options_form_password')
    // const passwordSubmitButton = document.querySelector('.passwordSubmitButton');
    const loginSubmitButton = document.querySelector('.loginSubmitButton');
    // const modal = document.querySelector('.sign_up_modal');

    const confirmContainerBackChevronFive = document.getElementById('confirmContainerBackChevronFive')
    const forgotPasswordEmailCheckContainer = document.querySelector('.forgot_password_email_check_container')


    if (signUpModalBtn) {
        signUpModalBtn.forEach((sub) => {
            sub.addEventListener('click', () => {
                signUpModal.style.display = 'block';
                // signUpTitleOptionsContainer.classList.add('show_container')
                // signUpTitleOptionsContainer.classList.add('sign_up_title_options_container')
                // emailVerificationContainer.classList.add('email_verification_container')
                // emailVerificationContainer.classList.add('hide_container')
            })
        })
    } else {
        console.warn('bidButton not found in the DOM.');
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
            }
        });
    } else {
        console.warn('bidModal not found in the DOM.');
    }


    // if (passwordSubmitButton) {
    //     passwordSubmitButton.addEventListener('click', (e) => {
    //         e.preventDefault()
    //         signUpEmailContainer.classList.remove('show_container')
    //         signUpEmailContainer.classList.add('shift_left_again')

    //         signUpEmailConfirmContainer.classList.remove('hide_container')
    //         signUpEmailConfirmContainer.classList.add('show_container')


    //     })
    // }


    if (confirmContainerBackChevron) {
        confirmContainerBackChevron.addEventListener('click', () => {
            emailVerificationContainer.classList.add('show_container')
            emailVerificationContainer.classList.remove('shift_left')
            signUpEmailContainer.classList.add('hide_container')
            signUpEmailContainer.classList.remove('show_container')
        })
    }


    if (confirmContainerBackChevronTwo) {
        confirmContainerBackChevronTwo.addEventListener('click', (e) => {
            e.preventDefault();
            signUpEmailContainer.classList.remove('show_container')
            signUpEmailContainer.classList.add('hide_container')

            emailVerificationContainer.classList.remove('shift_left')
            emailVerificationContainer.classList.add('show_container')


        })
    }

    if (confirmContainerBackChevronFive) {
        confirmContainerBackChevronFive.addEventListener('click', (e) => {
            e.preventDefault()
            console.log('clicked on Five!')
            passwordForgetContainer.classList.add('show_forgot_password_container')
            passwordForgetContainer.classList.remove('hide_forgot_password_container')

            forgotPasswordEmailCheckContainer.classList.remove('show_forgot_password_email_check_container')
            forgotPasswordEmailCheckContainer.classList.add('forgot_password_email_check_container')


        })
    }



    // Email submitted and checked if on file.
    // If not on file, take to register
    // If email on file, take to password entry
    if (emailSubmitButton) {
        emailSubmitButton.addEventListener('click', (e) => {
            e.preventDefault();

            const form = emailSubmitButton.closest('form');
            const formData = new FormData(form);
            const emailProvidedSigninPopup = document.querySelectorAll('.email_provided_signin_popup')

            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === false) {
                        // Go to password login container
                        emailVerificationContainer.classList.remove('show_container');
                        emailVerificationContainer.classList.add('shift_left');
                        emailLoginContainer.classList.remove('hide_email_login_container');
                        emailLoginContainer.classList.add('show_email_login_container');

                        emailProvidedSigninPopup.forEach((epp) => epp.innerHTML = formData.get('email'));
                    } else if (data.status === true) {
                        const email = formData.get('email');
                        sessionStorage.setItem('auth_email', email);
                        // Go to registration container
                        emailVerificationContainer.classList.remove('show_container');
                        emailVerificationContainer.classList.add('shift_left');
                        signUpEmailContainer.classList.remove('hide_container');
                        signUpEmailContainer.classList.add('show_container');
                        emailProvidedSigninPopup.forEach((epp) => epp.innerHTML = formData.get('email'));
                        // Pre-fill email in registration form
                        const registrationEmailInput = document.querySelector('#id_reg_email');
                        if (registrationEmailInput) {
                            registrationEmailInput.value = email;
                        }
                    } else {
                        console.error('Unexpected response:', data);
                    }
                })
                .catch(error => {
                    console.error('Error submitting email:', error);
                });
        });
    }



    // After Password Entered, 2f Auth Form
    // if (loginSubmitButton) {
    //     loginSubmitButton.addEventListener('click', (e) => {
    //         console.log('i\'ve been clicked!')
    //         e.preventDefault()
    //         emailLoginContainer.classList.remove('show_email_login_container');
    //         emailLoginContainer.classList.add('hide_email_login_container_to_left');
    //         signUpEmailConfirmContainer.classList.remove('hide_ign_up_email_confirm_container')
    //         signUpEmailConfirmContainer.classList.add('show_sign_up_email_confirm_container')
    //     })
    // }

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
                    console.log('data from loginSubmitButton is', data)
                    if (data['authenticated'] === true) {
                        emailLoginContainer.classList.remove('show_email_login_container');
                        emailLoginContainer.classList.add('hide_email_login_container_to_left');
                        signUpEmailConfirmContainer.classList.remove('hide_ign_up_email_confirm_container')
                        signUpEmailConfirmContainer.classList.add('show_sign_up_email_confirm_container')

                        setTimeout(() => {
                            const fiveMinutes = 1 * 60;
                            startCodeTimer(fiveMinutes, timerDisplay)
                        }, 100)


                    } else if (data['authenticated'] === false) {
                        console.error('Unexpected response:', data);
                        console.error('Unexpected response2:', data.message);
                        const loginUserOptionsError = document.querySelector('.login_user_options_error');
                        loginUserOptionsError.style.display = "block";
                        loginUserOptionsError.textContent = "Invalid Credentials Provided";
                        loginUserOptionsError.style.fontSize = "20px"
                        // if (data.error === "Invalid credentials. Attempt 5/5") {
                        //     loginUserOptionsError.textContent = "Too many failed attempts. Try again in 15 minutes"
                        // } else {
                        //     loginUserOptionsError.textContent = "Invalid Credentials Provided"
                        // }
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

    if (confirmContainerBackChevronSix) {
        confirmContainerBackChevronSix.addEventListener('click', () => {
            signUpEmailConfirmContainer.classList.remove('show_sign_up_email_confirm_container')
            signUpEmailConfirmContainer.classList.add('hide_ign_up_email_confirm_container')
            emailLoginContainer.classList.remove('hide_email_login_container_to_left');
            emailLoginContainer.classList.add('show_email_login_container');


        })
    }

    // 2f auth confirmation
    if (confirmSubmitBtn) {
        confirmSubmitBtn.addEventListener('click', (e) => {
            e.preventDefault();

            const code = Array.from(confirmInputs).map(input => input.value.trim()).join('');

            console.log('code', code)

            if (code.length != 6) {
                alert("Please enter the full 6-digit code.");
                return;
            }
            // const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
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




    if (confirmContainerBackChevronThree) {
        confirmContainerBackChevronThree.addEventListener('click', () => {

            emailLoginContainer.classList.remove('show_email_login_container')
            emailLoginContainer.classList.add('hide_email_login_container')

            emailVerificationContainer.classList.remove('shift_left')
            emailVerificationContainer.classList.add('show_container')


        })
    }



    if (emailSignUpButton) {
        emailSignUpButton.addEventListener('click', () => {
            signUpTitleOptionsContainer.classList.remove('show_container')
            signUpTitleOptionsContainer.classList.add('hide_container')

            emailVerificationContainer.classList.remove('hide_container')
            emailVerificationContainer.classList.add('show_container')
        })
    }

    if (backChevron) {
        backChevron.addEventListener('click', () => {
            emailVerificationContainer.classList.remove('show_container')
            emailVerificationContainer.classList.add('hide_container')
            signUpTitleOptionsContainer.classList.remove('hide_container')
            signUpTitleOptionsContainer.classList.add('show_container')
        })
    }

    // Disable Password Submit Button
    const passwordSubmitBtn = document.getElementById('passwordSubmitBtn');
    signUpOptionsFormPasswordInput.addEventListener('input', () => {
        passwordSubmitBtn.disabled = signUpOptionsFormPasswordInput.value.length < 8;
    });


    // Disable Email Submit Button
    const emailInput = document.getElementById('id_email_check');
    const emailContinueBtn = document.getElementById('emailContinueBtn');
    emailInput.addEventListener('input', () => {
        emailContinueBtn.disabled = !emailInput.value.includes('@');
    });

    // Disable Password Reset Submit Button
    const resetPasswordBtn = document.getElementById('resetPasswordBtn');
    const resetPasswordInput = document.getElementById('id_email_password_reset_form');

    resetPasswordInput.addEventListener('input', () => {
        resetPasswordBtn.disabled = !resetPasswordInput.value.includes('@');
    });




    // Forgot password
    const passwordForgetLink = document.querySelector('.passwordForgetLink');
    const passwordForgetContainer = document.querySelector('.forgot_password_container');


    if (passwordForgetLink) {
        passwordForgetLink.addEventListener('click', () => {
            emailLoginContainer.classList.remove('show_email_login_container');
            emailLoginContainer.classList.add('hide_email_login_container_to_left');
            passwordForgetContainer.classList.add('show_forgot_password_container')


        })
    }


    if (confirmContainerBackChevronFour) {
        confirmContainerBackChevronFour.addEventListener('click', () => {
            passwordForgetContainer.classList.remove('show_forgot_password_container')
            passwordForgetContainer.classList.add('hide_forgot_password_container')

            emailLoginContainer.classList.remove('hide_email_login_container_to_left');
            emailLoginContainer.classList.add('show_email_login_container');

        })
    }




    if (resetPasswordBtn) {
        resetPasswordBtn.addEventListener('click', (e) => {

            e.preventDefault();

            const email = resetPasswordInput.value.trim();
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
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        //alert('Password reset link sent to your email.')
                        passwordForgetContainer.classList.remove('show_forgot_password_container')
                        passwordForgetContainer.classList.add('hide_forgot_password_container')

                        forgotPasswordEmailCheckContainer.classList.remove('hide_forgot_password_email_check_container')
                        forgotPasswordEmailCheckContainer.classList.add('show_forgot_password_email_check_container')

                    } else {
                        alert(data.error || 'Something went wrong')
                    }
                })
                .catch(error => {
                    console.error('Error sending password reset link:', error);
                })
                .finally(() => {
                    // Hide spiner, reset button text, re-enable button
                    resetSpinner.style.display = 'none';
                    resetPasswordBtn.disabled = false;
                    resetPasswordBtn.textContent = originalButtonText
                })
        })
    }

})





// Submit Registration Form
const registrationSubmitButton = document.querySelector('.registrationSubmitButton');

if (registrationSubmitButton) {
    registrationSubmitButton.addEventListener('click', function (e) {
        e.preventDefault();

        console.log('registrationSubmitButton clicked!')

        const form = registrationSubmitButton.closest('form');

        console.log('form.action is:', form.action)

        const formData = new FormData(form);

        // Inject email from sessionStorage if not in form
        const storedEmail = sessionStorage.getItem('auth_email');
        console.log('storedEmail', storedEmail)

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
                console.log('data in js', data)
                if (data.registered) {
                    // Show success UI or redirect
                    console.log('User registered!');
                } else if (data.errors) {
                    displayFormErrorsTwo(data.errors);
                }
            })
            .catch(error => {
                console.error('Error submitting registration form:', error);
            });
    });
}


function displayFormErrorsTwo(errors) {
    console.log('errors', errors);

    const errorContainer = document.querySelector('.registration_form_errors');
    errorContainer.innerHTML = ''; // Clear previous errors
    errorContainer.style.display = 'block';

    let parsedErrors = {};

    try {
        parsedErrors = JSON.parse(errors);  // Try to parse Django-style JSON errors
        console.log('parsedErrors', parsedErrors)
    } catch (e) {
        // If it fails, assume it's a simple string message
        const p = document.createElement('p');
        p.classList.add('form-error-message');
        p.textContent = errors;
        errorContainer.appendChild(p);
        return; // Don't continue processing as JSON
    }

    console.log('parsedErrors', parsedErrors);

    const passwordErrors = parsedErrors.password || [];
    const password2Errors = parsedErrors.password2 || [];

    if (passwordErrors.length > 0) {
        passwordErrors.forEach(error => {
            const p = document.createElement('p');
            p.classList.add('form-error-message');
            p.textContent = `${error.message}`;
            errorContainer.appendChild(p);
        });
    } else if (password2Errors.length > 0) {
        password2Errors.forEach(error => {
            const p = document.createElement('p');
            p.classList.add('form-error-message');
            p.textContent = `Confirm Password: ${error.message}`;
            errorContainer.appendChild(p);
        });
    }

    if (errorContainer.children.length > 0) {
        errorContainer.style.display = 'block';
    }

}



const displayFormErrors = (errors) => {
    // Clear any existing errors
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    for (const [fieldName, errorList] of Object.entries(errors)) {
        const field = document.querySelector(`#id_${fieldName}`);
        if (field) {
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('field-error');
            errorDiv.style.color = 'red';
            errorDiv.style.marginTop = '5px';
            errorDiv.innerText = errorList.join(', ');
            field.parentNode.appendChild(errorDiv)
        }
    }
}



// 2F Auth Timer
const startCodeTimer = (duration, display) => {
    let timer = duration;
    const countdown = setInterval(() => {
        const minutes = Math.floor(timer / 60)
        const seconds = timer % 60;

        display.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        if (--timer < 0) {
            clearInterval(countdown);
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
                startCodeTimer(1 * 60, timerDisplay);

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





// 2FA Tab On Input Entry
document.querySelectorAll('.code-input').forEach((input, index, inputs) => {
    input.addEventListener('input', () => {
        if (input.value.length === input.maxLength && index < inputs.length - 1) {
            inputs[index + 1].focus();
        }
    });

});

// Backspace to empty input
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

// Adjust Logo in Navbar
toggle.addEventListener('click', () => {
    sidebar.classList.toggle('close');
    navLogoText.classList.toggle('abbrev')
    if (navLogoText.classList.contains('abbrev')) {
        navLogoText.innerHTML = "TPU"
    } else {
        navLogoText.innerHTML = "The Pop Up"
    }

});

searchBtn.addEventListener('click', () => {
    sidebar.classList.remove('close');
})



mobileSearchIcon.addEventListener('click', () => {
    mobileSearchBox.classList.toggle('hide-mobile-search-box')
    navLogoText.classList.toggle('hide-logo-text')
})

const darkLighModeToggle = () => {
    modeSwitch.addEventListener('click', () => {
        body.classList.toggle('dark');

        if (body.classList.contains("dark")) {
            modeText.innerText = "Light Mode";
            localStorage.setItem('darkMode', 'enabled');
        } else {
            modeText.innerText = "Dark Mode";
            localStorage.setItem('darkMode', 'disabled'); // Save preference
        }
    })
}



mobileMoon.addEventListener('click', () => {
    body.classList.toggle('dark');
})

mobileSun.addEventListener('click', () => {
    body.classList.toggle('dark');

})


darkLighModeToggle()

// Check localStorage for saved mode preference
const savedMode = localStorage.getItem('darkMode');
if (savedMode === 'enabled') {
    body.classList.add('dark');
    modeText.innerText = "Light Mode";
}


if (!localStorage.getItem('darkMode')) {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        body.classList.add('dark');
        modeText.innerText = "Light Mode";
        localStorage.setItem('darkMode', 'enabled');
    }
}


// bid modal
document.addEventListener('DOMContentLoaded', function () {
    // Get the modal, button, and close span

    const bidButton = document.querySelectorAll('.bidButtonClass')
    if (bidButton) {
        bidButton.forEach((btn) => {
            btn.addEventListener('click', function () {
                console.log("I've been clicked the bidButton")
                const productId = this.dataset.productId;
                const modal = document.getElementById(`bidModal-${productId}`);
                console.log('productId', productId)
                console.log('modal', modal)
                if (modal) {
                    modal.style.display = 'block';
                }
            })
        })
    } else {
        console.warn('bidButton not found in the DOM.');
    }

    document.querySelectorAll('.modal.fade').forEach(modal => {
        const productId = modal.id.split('-')[1]; // Extract product ID from modal ID
        console.log('modal opened')
        console.log('productId', productId)
        // Handle close button
        const closeBtn = modal.querySelector('.closeModal');
        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                modal.style.display = 'none';
            });
        } else {
            console.warn(`Close button not found for modal-${productId}`);
        }

        // Handle outside click
        window.addEventListener('click', function (event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });



    // if user not signed in and tries to bid
    document.querySelectorAll('.loginPrompt').forEach(btn => {
        btn.addEventListener('click', () => {
            alert("You must be signed in to place a bid");
            signUpModal.style.display = 'block';
        })
    })

    // buttons for prefilled bids
    document.body.addEventListener('click', (e) => {
        if (!e.target.closest('.quick_bid')) return;
        const preBidBtn = e.target.closest('.quick_bid');
        const form = preBidBtn.closest('.bidForm');
        const input = form.querySelector('input[name="bid_amount"]');

        input.value = preBidBtn.dataset.amount;
        input.focus();
    })


    // Handle AJAX Submit
    document.querySelectorAll('.bidForm').forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const data = new FormData(form);

            console.log('data', data)

            // http://localhost:8000/auction/place-bid/
            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')

                },
                body: data
            })
                .then(async (r) => {
                    const resp = form.nextElementSibling;
                    const data = await r.json();


                    if (!r.ok) {
                        resp.style.color = "red";
                        resp.textContent = data.message || "Something went wrong.";
                        return;
                    }
                    resp.style.color = "green";
                    resp.textContent = `Bid placed! New high $${data.new_highest}, bids: ${data.bid_count}`;

                    // Update the DOM with the new highest bid and bid count
                    const productId = form.dataset.productId;

                    // Update highest bid
                    const bidDisplay = document.querySelector(`.current_bid_display[data-product-id="${productId}`)
                    if (bidDisplay) {
                        bidDisplay.innerHTML = `$${data.new_highest}`;
                    }


                    // Update bid count
                    const countDisplay = document.querySelector(`.current_bid_count[data-product-id="${productId}"], .current_bid_count_value`);
                    if (countDisplay) {
                        countDisplay.innerHTML = data.bid_count;
                    }

                    const newHighest = data.new_highest;
                    const predefinedContaner = document.querySelector(`#predefined_bids[data-product-id="${productId}"`)
                    if (predefinedContaner) {
                        const increments = [10, 20, 30];
                        const preDefButtons = predefinedContaner.querySelectorAll('.quick_bid');
                        preDefButtons.forEach((btn, index) => {
                            const increment = increments[index];

                            const updatedAmount = (Number(newHighest) + Number(increment)).toFixed(2);

                            btn.dataset.amount = updatedAmount;
                            btn.querySelector('span').textContent = `$${Number(updatedAmount).toLocaleString()}`
                        })
                    }

                    const bidHint = document.querySelector('.bid_hint');
                    bidHint.textContent = " "

                    // Optionally clear input
                    form.reset();
                })
                .catch(() => {
                    const resp = form.nextElementSibling;
                    resp.style.color = "red";
                    resp.textContent = "Unexpected error. Please try again";
                    // form.nextElementSibling.textContent = "Unexpected"
                });
        });
    });

});





// address change modal
document.addEventListener('DOMContentLoaded', function () {
    // Get the modal, button, and close span
    const addressChangeModal = document.getElementById('addressChangeModal');
    const addressChangeBtn = document.getElementById('addressChangeButton');
    const addressChangeSpan = document.querySelector('.closeAddressModal');

    // Show the modal when the button is clicked
    addressChangeBtn.addEventListener('click', function () {
        addressChangeModal.style.display = 'block';
    });

    // Close the modal when the close span is clicked
    addressChangeSpan.addEventListener('click', function () {
        addressChangeModal.style.display = 'none';
    });

    // Close the modal when clicking outside of it
    window.addEventListener('click', function (event) {
        if (event.target === addressChangeModal) {
            addressChangeModal.style.display = 'none';
        }
    });
});





// payment options dropdown
var expandButton = document.querySelector(".expandButton");
var checkoutOptionsContainer = document.querySelector('.checkout_options_container')

expandButton.addEventListener("click", function () {
    /* Toggle between adding and removing the "active" class,
    to highlight the button that controls the panel */
    this.classList.toggle("active");
    checkoutOptionsContainer.classList.toggle('show')

});


// subtotal options dropdown
var subtotalExpand = document.querySelector(".subtotalExpand");
var purchaseDetailsContainer = document.querySelector('.purchase_details_container')

subtotalExpand.addEventListener("click", function () {
    this.classList.toggle("subTotalactive");
    purchaseDetailsContainer.classList.toggle('subTotalShow')

});


// shipping button options
var shippingButtons = document.querySelectorAll(".shippingButtons")
const shippingCost = document.getElementById('shippingCost')
const orderQuantity = document.getElementById('purchaseQuantity').innerHTML
const processingFee = document.getElementById('processingFee').innerHTML
const salesTax = document.getElementById('purchaseTax').innerHTML
const purchaseSubtotal = document.getElementById('purchaseSubtotal').innerHTML


let shippingMath;
let orderTotal;
let shipping;

shippingButtons.forEach((button) => {

    shippingMath = 1499 * Number(orderQuantity)
    console.log('shippingMath', shippingMath)

    shippingCost.innerText = `$${shippingMath / 100}`
    console.log('shippingCost', shippingCost)


    button.addEventListener("click", function (e) {
        e.preventDefault();
        // Loop through all buttons and remove "active" class if present
        if (body) {
            shippingButtons.forEach((btn) => btn.classList.remove("chosen"));

            // Add "active" class to the button that was clicked
            this.classList.add("chosen");

        }

        let processFee = processingFee.replace("$", "").replace(",", "")
        let tax = salesTax.replace("$", "").replace(",", "")

        if (button.name == "standard" && orderQuantity > 0) {
            shippingMath = 1499 * Number(orderQuantity)
            shippingCost.innerText = `$${shippingMath / 100}`
            shipping = shippingCost.innerText.replace("$", "").replace(",", "")
            calculateSubtotal(processFee, shipping, tax)
        }

        if (button.name == "express" && orderQuantity > 0) {
            shippingMath = 2499 * Number(orderQuantity)
            shippingCost.innerText = `$${shippingMath / 100}`
            shipping = shippingCost.innerText.replace("$", "").replace(",", "")
            calculateSubtotal(processFee, shipping, tax)
        }

    });


});



function numberWithCommas(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}



// update primary payment button
document.addEventListener('DOMContentLoaded', function () {
    const selectedPaymentButton = document.getElementById('selectedPaymentButton');
    const checkoutOptions = document.getElementById('checkoutOptions');

    // Listen for clicks on payment buttons
    checkoutOptions.addEventListener('click', function (event) {
        const clickedButton = event.target.closest('.payment_option_buttons');

        if (clickedButton) {
            // Get the icon (either <i> or <img>) and text
            const icon = clickedButton.querySelector('i, img');
            const text = clickedButton.textContent.trim(); // Extract button text

            // Update the primary payment button
            selectedPaymentButton.innerHTML = ''; // Clear current content

            if (icon) {
                // Clone the icon and append to the button
                const newIcon = icon.cloneNode(true);
                selectedPaymentButton.appendChild(newIcon);
            }

            // Append the text
            const newText = document.createTextNode(` ${text}`);
            selectedPaymentButton.appendChild(newText);

            // close dropdown
            checkoutOptionsContainer.classList.toggle('show')
        }
    });
});

// update secondary payment button, bottom of checkout page
document.addEventListener('DOMContentLoaded', function () {
    const selectedPaymentButtonTwo = document.getElementById('selectedPaymentButtonTwo')
    const checkoutOptions = document.getElementById('checkoutOptions');

    // Listen for clicks on payment buttons
    checkoutOptions.addEventListener('click', function (event) {
        const clickedButton = event.target.closest('.payment_option_buttons');

        if (clickedButton) {
            // Get the icon (either <i> or <img>) and text
            const icon = clickedButton.querySelector('i, img');
            const text = clickedButton.textContent.trim(); // Extract button text

            // Update the primary payment button
            selectedPaymentButtonTwo.innerHTML = ''; // Clear current content

            if (icon) {
                // Clone the icon and append to the button
                const newIcon = icon.cloneNode(true);
                selectedPaymentButtonTwo.appendChild(newIcon);
            }

            // Append the text
            const newText = document.createTextNode(` ${text}`);
            selectedPaymentButtonTwo.appendChild(newText);
        }
    });
});


// get subtotal and total

const calculateSubtotal = (proccessFee, shippingCost, tax) => {

    const purchaseSubtotal = document.getElementById('purchaseSubtotal').innerHTML.replace('$', '').replace(',', '')
    const purchaseTotal = document.getElementById('purchaseTotal')

    let totalCalculation = parseFloat(purchaseSubtotal) + parseFloat(proccessFee) + parseFloat(tax) + parseFloat(shipping)
    purchaseTotal.innerHTML = `$${numberWithCommas(totalCalculation)}`

    // const purchasePrice = document.getElementById('purchasePrice').innerHTML.replace('$', '')
    // const purchaseQuantity = document.getElementById('purchaseQuantity').innerHTML
    // const processingFee = document.getElementById('processingFee').innerHTML.replace('$', '')
    // const shippingInnerHTML = shippingCost.innerHTML.replace('$', '')
    // const purchaseTax = document.getElementById('purchaseTax')

    // const merchandiseCost = Number(purchasePrice) * Number(purchaseQuantity)
    // const workingSubtotal = merchandiseCost + Number(processingFee) + Number(shippingInnerHTML)
    // const workingTaxAmount = workingSubtotal * .075
    // purchaseTax.innerHTML = "$" + String(workingTaxAmount.toFixed(2))
    // purchaseSubtotal.innerHTML = "$" + String(Number(workingTaxAmount.toFixed(2)) + workingSubtotal)
}



// Grab email for Password Reset
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = newURLSearchParams(window.location.search);
    console.log('urlParams', urlParams)

    const email = urlParams.get('email')
    console.log('email', email)

    if (email) {
        const emailInput = document.querySelector('#id_email_for_password_reset_one');
        console.log('emailInput', emailInput)
        if (emailInput) {
            emailInput.value = email;
        }
    }
})


// Password Reset
const passwordResetForm = document.getElementById('passwordResetForm');

if (passwordResetForm) {
    passwordResetForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(passwordResetForm);
        const csrfToken = getCookie('csrftoken')

        fetch(window.location.href, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Password reset successully! You can now log in');
                    window.location.href = '/'; // may want to redirect to 2fa page
                } else {
                    alert(data.error || 'Something went wrong')
                }
            })
            .catch(error => {
                console.error('Error resetting password', error);
                alert('An unexpected error occurred')
            });
    });
}



// Password Reset Confirm
const resetPasswordFormBtn = document.querySelector('.resetPasswordFormBtn');
// const resetPasswordFormBtnTwo = document.getElementById('resetPasswordFormBtn');

console.log('resetPasswordFormBtn', resetPasswordFormBtn)

// console.log('resetPasswordFormBtnTwo', resetPasswordFormBtnTwo)

const resetPasswordForm = document.getElementById('resetPasswordForm');
console.log('resetPasswordForm', resetPasswordForm)

if (resetPasswordForm) {
    resetPasswordForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(resetPasswordForm);
        console.log('formData', formData)

        const csrfToken = getCookie('csrftoken')
        console.log('csrfToken', csrfToken)

        fetch(window.location.href, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Password reset successully! You can now log in');
                    window.location.href = '/'; // may want to redirect to 2fa page
                } else {
                    alert(data.error || 'Something went wrong')
                }
            })
            .catch(error => {
                console.error('Error resetting password', error);
                alert('An unexpected error occurred')
            });
    });
}


// Shipping Address Update in Checkout Page
document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.modal_tab');
    const tabContents = document.querySelectorAll('.modal_tab_content');

    tabButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const target = button.getAttribute('data-tab');

            // Remove "active" class from all;
            tabButtons.forEach(btn => btn.classList.remove('activated'))
            tabContents.forEach(content => content.classList.remove('activated'));

            // Add active to selected
            button.classList.add('activated');
            document.getElementById(target).classList.add('activated')
        })
    })


})

