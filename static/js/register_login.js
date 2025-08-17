// Variables For Signup/Register Modal Home
const signUpTitleOptionsContainer = document.querySelector('.sign_up_title_options_container');
const emailSignUpButton = document.querySelector('.emailSignUpButton');

// Variables for Register/Login by Email
const emailVerificationContainer = document.querySelector('.email_verification_container');
const emailInput = document.getElementById('id_email_check');
const emailSubmitButton = document.querySelector('.emailSubmitButton');

// Variables for Register/Login by Google
// const googleSignUpButton = document.querySelector()

// Variables for Register/Login by Facebook
// const facebookSignUpButton = document.querySelector()


// Variable for Email Registration
const signUpEmailContainer = document.querySelector('.sign_up_email_container');


// Variables for container to enter password and sign-in
const emailLoginContainer = document.querySelector('.email_login_container');
const loginSubmitButton = document.querySelector('.loginSubmitButton');
const signUpOptionsFormPasswordInput = document.querySelector('.sign_up_options_form_password'); // class inherted from custom form


// Variables for container to enter 6-digit code
const signUpEmailConfirmContainer = document.querySelector('.sign_up_email_confirm_container');
const confirmSubmitBtn = document.querySelector('.confirm_submit_button');
const confirmInputs = document.querySelectorAll('.confirmation_input input');



// From Sign in Modal Home
if (emailSignUpButton) {
    emailSignUpButton.addEventListener('click', () => {
        console.log('email clicked')
        moveForwardSignIn('hide_container', 'show_container', 'hide_container', 'show_email_verification_container', signUpTitleOptionsContainer, emailVerificationContainer)
    })
}

// if (googleSignUpButton) {
//     googleSignUpButton.addEventListener('click', () => {
//         console.log('googleSignUpButton clicked')
//         moveForwardSignIn()
//     })
// }

// if (facebookSignUpButton) {
//     facebookSignUpButton.addEventListener('click', () => {
//         console.log('facebookSignUpButton clicked')
//         moveForwardSignIn()
//     })
// }



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
        const emailProvidedSigninPopup = document.querySelectorAll('.email_provided_signin_popup')

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
                if (data.status === false) {
                    // move forward to password login container
                    moveForwardSignIn('shift_left', 'show_container', 'hide_email_login_container', 'show_email_login_container', emailVerificationContainer, emailLoginContainer)
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
                console.log('data from loginSubmitButton is', data)
                if (data['authenticated'] === true) {
                    // const moveForwardSignIn( addThisHideClass, removeThisShowClass, removeNextHideClass, addNextShowClass, containerToHide, containerToShow)
                    moveForwardSignIn('hide_email_login_container_to_left', 'show_email_login_container', 'hide_sign_up_email_confirm_container', 'show_sign_up_email_confirm_container', emailLoginContainer, signUpEmailConfirmContainer)

                    setTimeout(() => {
                        const fiveMinutes = 5 * 60;
                        startCodeTimer(fiveMinutes, timerDisplay)
                    }, 100)


                } else if (data['authenticated'] === false) {
                    console.error('Unexpected response:', data);
                    console.error('Unexpected response2:', data.message);
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






const moveForwardSignIn = (
    addThisHideClass,
    removeThisShowClass,
    removeNextHideClass,
    addNextShowClass,
    containerToHide,
    containerToShow

) => {
    console.log('moving forward')
    containerToHide.classList.remove(removeThisShowClass)
    containerToHide.classList.add(addThisHideClass)

    containerToShow.classList.remove(removeNextHideClass)
    containerToShow.classList.add(addNextShowClass)
}


const moveBackwardSignIn = (
    removeThisClass,
    addThisClass,
    removeNextClass,
    addNextClass,
    containerToHide,
    containerToShow
) => {

    console.log('moving backward')
    containerToHide.classList.remove(removeThisClass)
    containerToHide.classList.add(addThisClass)
    containerToShow.classList.remove(removeNextClass)
    containerToShow.classList.add(addNextClass)
}


const moveBackwardSignInButton = (
    removeThisClass,
    addThisClass,
    removeNextClass,
    addNextClass,
    nameOfContainerToHide,
    nameOfContainerToShow
) => {
    console.log('moveBackwardSignInButton moving backward')
    const containerToHide = document.querySelector(nameOfContainerToHide)
    const containerToShow = document.querySelector(nameOfContainerToShow)

    containerToHide.classList.remove(removeThisClass)
    containerToHide.classList.add(addThisClass)
    containerToShow.classList.remove(removeNextClass)
    containerToShow.classList.add(addNextClass)
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







// /*  ====== Sign Up Modal ===== */
/* Modal background */
// .sign_up_modal {
//     /* Hidden by default */
//     display: none;

//     /* Enable scroll if needed */
//     position: fixed;
//     z-index: 1000;
//     left: 20%;
//     top: 0;

//     width: 75%;
//     height: 90%;
//     overflow: auto;

//     /* Black background with opacity */
//     background-color: rgba(0, 0, 0, 0.4);

// }

// /* Modal content */
// .sign_up_modal_content {
//     background-color: #fff;
//     /* margin: 15% auto; */
//     /* Center it */
//     padding: 1rem 1rem;
//     border: 1px solid #888;
//     width: 85%;
//     /* Adjust width */
//     box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
//     border-radius: 5px;

//     border: 2px solid var(--text-color);

//     display: flex;
//     flex-direction: column;
//     gap: 1rem;
//     height: 90%;
//     margin: 2.5% auto;
// }



/* ===== sign_up_pic_form_container ===== */

// .sign_up_pic_form_container {
//     display: flex;

//     overflow: hidden;
//     width: 100%;
//     position: relative;

// }


// .sign_up_image_container {
//     background-color: white;
//     display: flex;
//     justify-content: flex-start;
//     width: 50%;
//     z-index: 1;

// }


// .img_sign_up {
//     transform: rotate(-50deg);
//     height: 58%;
//     margin-left: -4rem;
//     margin-top: 4.75rem;
// }

// .interntal_sign_up_container {
//     display: flex;
//     overflow: hidden;
//     width: 100%;
//     position: relative;

// }

/* ===== end sign_up_pic_form_container ===== */

// /* ==== sign_up_title_options_container ==== */

// .sign_up_title_options_container,
// .email_verification_container,
// .sign_up_email_container,
// .email_login_container,
// .sign_up_email_confirm_container,
// .forgot_password_container,
// .forgot_password_email_check_container {
//     position: absolute;
//     width: 50%;
//     top: 0;
//     transition: transform 0.5s ease-in-out;
// }

// .sign_up_title_options_container {
//     right: 0%;
//     transform: translateX(0%);
//     width: 100%;

//     display: flex;
//     flex-direction: column;
//     justify-content: space-between;
//     height: 100%;
// }


// .sign_up_title_options_container.hide_container {
//     transform: translateX(-200%);
// }



// .sign_up_modal_title {
//     display: flex;
//     flex-direction: column;
//     align-items: center;
// }

// .sign_up_modal_title h3 {
//     font-size: clamp(1.25rem, 1.75rem, 3vw);
//     margin-bottom: 1rem;
//     text-align: center;
// }

// .sign_up_modal_title p {
//     text-align: center;
//     margin-bottom: 1rem;
// }

// .sign_up_options_container {
//     align-items: center;
//     display: flex;
//     flex-direction: column;
//     justify-content: space-around;
//     height: 40%;
// }

// .sign_up_options_form_container {
//     align-items: center;
//     display: flex;
//     flex-direction: column;
//     justify-content: space-around;
//     height: 60%;
// }



// .sign_up_option_buttons {
//     align-items: center;
//     background-color: transparent;
//     border: 2px solid var(--text-color);
//     border-radius: 5px;
//     box-sizing: border-box;
//     color: black;
//     cursor: pointer;
//     display: inline-flex;
//     justify-content: space-around;
//     height: 2.5rem;
//     /* max-height: 3.5rem; */
//     padding: 0px;
//     position: relative;
//     width: 90%;
// }


// .sign_up_option_buttons i,
// .sign_up_option_buttons img {
//     width: 3rem;
// }

// .sign_up_option_buttons i {
//     font-size: 1.35rem;
// }

// .sign_up_option_buttons p {
//     font-size: clamp(.90rem, 1rem, 6vw);
//     font-weight: 600;
//     width: 15rem;
// }

// .sign_up_modal_policy {
//     margin-top: 2rem;
// }

// .sign_up_modal_policy p {
//     font-size: clamp(.60rem, .80rem, 6vw);
//     text-align: center;
// }


// /* ===== email_verification_container ====*/

// .email_verification_container {
//     left: 100%;
//     transform: translateX(0%);
//     width: 100%;

//     display: flex;
//     flex-direction: column;
//     justify-content: space-between;

//     height: 100%;
// }

// .email_verification_container.show_container {
//     transform: translateX(-100%);

// }


// .email_verification_container.shift_left {
//     transform: translateX(-200%);
// }



// .sign_up_modal_title {
//     display: flex;
//     flex-direction: column;
//     align-items: center;
// }


// .sign_up_modal_title p {
//     text-align: center;
//     margin-bottom: 1rem;
//     width: 90%;
// }

// .email_sign_up_modal_title {
//     display: flex;
//     flex-direction: column;
//     align-items: center;
// }

// .email_sign_up_modal_title p {
//     text-align: center;
//     width: 80%;
// }

// .email_sign_up_modal_container {
//     align-items: center;
//     display: flex;
//     justify-content: center;
//     margin-bottom: 1rem;
// }



// .email_sign_up_modal_container h3 {
//     font-size: clamp(1.25rem, 1.75rem, 3vw);
// }


// .email_sign_up_modal_container i {
//     font-size: 2.10rem;
//     cursor: pointer;
//     margin-bottom: .30rem;
//     text-align: left;


// }


// .sign_up_options_form {
//     display: flex;
//     flex-direction: column;
//     margin-top: 1rem;
// }

// .registration_options_form {
//     display: flex;
//     flex-direction: column;
//     margin-top: 1rem;

// }


// .password_reest_sign_up_options_form {
//     display: flex;
//     flex-direction: column;
//     margin-top: 1rem;
// }


// form.sign_up_options_form input,
// form.registration_options_form input,
// form.password_reset_sign_up_options_form input {
//     border: 2px solid var(--text-color);
//     border-radius: 5px;
//     color: var(--text-color);
//     font-size: 1rem;
//     height: 2rem;
//     padding-left: .5rem;
//     width: clamp(18rem, 20rem, 5vw);
//     margin-bottom: 1rem;
// }


// #id_email {
//     width: 100%;
//     height: 2rem;

// }


// /* ===== end of email_verification_container ===== */


// /* ===== start sign_up_email_container / Register Screen ===== */
// .sign_up_email_container {
//     left: 200%;
//     transform: translateX(0%);
//     width: 100%;

//     align-items: center;
//     display: flex;
//     flex-direction: column;
//     justify-content: space-between;
//     height: 100%;
// }


// .sign_up_email_container.show_container {
//     transform: translateX(-200%);

// }

// .sign_up_email_container.shift_left_again {
//     transform: translateX(-300%);
// }


// .registration_form_errors {
//     border: 2px solid green;
//     height: auto;
//     width: 100%;
// }

// /* ===== end sign_up_email_container / Register Screen ===== */




// /* ===== start email_login_container | displayed if email on file ===== */

// .email_login_container {
//     left: 200%;
//     transform: translateX(0%);
//     width: 100%;

//     align-items: center;
//     display: flex;
//     flex-direction: column;
//     justify-content: space-between;
//     height: 100%;
// }


// .email_login_container.show_email_login_container {
//     transform: translateX(-200%);

// }

// .email_login_container.hide_email_login_container_to_left {
//     transform: translateX(-300%);
// }



// p.email_provided_signin_popup {
//     color: var(--text-color);
//     font-size: clamp(1rem, 1.50rem, 2.5vw);
//     margin-bottom: 1rem;
//     text-align: center;

// }

// /* ===== end email_login_container ===== */



// /* ===== sign_up_email_confirm_container ===== */

// .sign_up_email_confirm_container {
//     left: 200%;
//     transform: translateX(0%);
//     width: 100%;

//     align-items: center;
//     display: flex;
//     flex-direction: column;
//     height: 100%;
//     justify-content: space-between;
// }


// .sign_up_email_confirm_container.show_sign_up_email_confirm_container {
//     transform: translateX(-200%);

// }


// /* .sign_up_email_confirm_container.shift_left_again {
//     transform: translateX(-300%);
// } */



// .confirmation_input_container_text {
//     align-items: center;
//     display: flex;
//     flex-direction: column;
// }


// .confirmation_input_container_text p:nth-child(1) {
//     font-size: 1.25rem;
//     text-align: center;
//     margin-bottom: .5rem;
//     width: 80%;
// }

// .confirmation_input_container_text p:nth-child(2) {
//     font-size: 1.25rem;
//     font-weight: bold;
//     margin-bottom: .75rem;
//     text-align: center;
//     width: 80%;
// }

// .confirmation_input_container_text p:nth-child(3) {
//     color: var(--text-color);
//     font-size: 1.5rem;
//     font-weight: 600;
//     margin-bottom: .50rem;
//     text-align: center;
// }


// .comfirmation_input_container form {
//     align-items: center;
//     display: flex;
//     flex-direction: column;

//     gap: 1rem;
// }


// .resend_request_container {
//     display: flex;
//     flex-direction: column;
//     margin-top: 1.25rem;
//     text-align: center;
// }

// #resend_status_message {
//     margin-top: .5rem;
// }

// .inner_resend_request_container {
//     align-items: center;
//     display: flex;
//     justify-content: center;
//     gap: .5rem;
// }

// .confirmation_input {
//     display: flex;
//     justify-content: center;
//     gap: .5rem
// }

// .confirmation_input input {
//     border: 2px solid var(--text-color);
//     border-radius: 5px;
//     color: var(--text-color);
//     font-size: 1.25rem;
//     height: 3rem;
//     text-align: center;
//     width: 2rem;
// }

// /* ===== end of sign_up_email_confirm_container ===== */

// /* ===== start of forgot_password_container ===== */
// .forgot_password_container {
//     left: 200%;
//     transform: translateX(0%);
//     width: 100%;

//     align-items: center;
//     display: flex;
//     flex-direction: column;
//     justify-content: space-between;
//     height: 100%;
// }


// .forgot_password_container.show_forgot_password_container {
//     transform: translateX(-200%);


// }



// .forgot_password_container.hide_forgot_password_container {
//     transform: translateX(-300%);
// }


// .forgot_password_options_container {
//     align-items: center;
//     display: flex;
//     flex-direction: column;
//     justify-content: space-around;
//     height: 100%;
// }


// .spinner {
//     border: 4px solid #f3f3f3;
//     /* Light grey */
//     border-top: 4px solid #555;
//     /* Black */
//     border-radius: 50%;
//     width: 30px;
//     height: 30px;
//     animation: spin 0.8s linear infinite;
//     margin: auto;
// }

// @keyframes spin {
//     0% {
//         transform: rotate(0deg);
//     }

//     100% {
//         transform: rotate(360deg);
//     }
// }


// /* ===== end of forgot_password_container ===== */



// /* ===== start of forgot_password_email_check_container ===== */
// .forgot_password_email_check_container {
//     left: 200%;
//     transform: translateX(0%);
//     width: 100%;

//     align-items: center;
//     display: flex;
//     flex-direction: column;
//     justify-content: space-between;
//     height: 100%;
// }


// .forgot_password_email_check_container.show_forgot_password_email_check_container {
//     transform: translateX(-200%);
// }


/* ===== end of forgot_password_email_check_container ===== */


/* ==================================== End of Sign Up Modal =================================== */
