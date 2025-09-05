// Sign-in / Registration modal flow
// registred user, email sign-in | - sign-in option (google, facebook, email) -> enter email -> enter password -> enter 6-digit code from email

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
const facebookSignUpButton = document.querySelector('.facebookSignUpButton');
const socialVerificationContainer = document.querySelector('.social_registration_container')


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
// const moveForwardSignIn( addThisHideClass, removeThisShowClass, removeNextHideClass, addNextShowClass, containerToHide, containerToShow)
// moveForwardSignIn('hide_container', 'show_container', 'hide_container', 'show_social_registration_container', signUpTitleOptionsContainer, socialVerificationContainer) //socialVerificationContainer
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


function openPopUp(socialUrl) {
    console.log('openPopUp called!')
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

    // let loginProcessing = false;
    // let checkCount = 0;

    pollLoginStatus(socialPopup)

}


function pollLoginStatus(socialPopup) {
    let loginProcessing = false;
    let checkCount = 0;

    console.log('pollLoginStatus called ')

    const checkLoginStatus = setInterval(async () => {
        checkCount++;

        console.log('checkLoginStatus called')

        try {
            const response = await fetch('/pop_accounts/social-login-complete/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            console.log('response', response)

            if (response.ok) {
                const userData = await response.json();
                console.log('userData', userData)

                console.log(`${checkCount}: ${userData}`)

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
                console.log(`Response not OK:`, response.status);
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



// Create PopUp for Facebook Login
document.addEventListener("DOMContentLoaded", () => {

    const fbBtn = document.getElementById("facebookSignUpButton");
    const fbUrl = document.getElementById("facebookLoginUrl").value;

    const googleBtn = document.getElementById("googleSignUpButton");
    const googleUrl = document.getElementById("googleLoginUrl").value;


    if (!fbBtn || !fbUrl || !googleBtn || !googleUrl) return;


    fbBtn.addEventListener("click", (e) => {
        e.preventDefault();

        openPopUp(fbUrl)

        // const width = 550, height = 600;
        // const left = (screen.width - width) / 2;
        // const top = (screen.height - height) / 2;

        // const facebookPopup = window.open(
        //     fbUrl,
        //     "fbLoginPopup",
        //     `width=${width},height=${height}, top=${top}, left=${left}`
        // );

        // if (!facebookPopup) {
        //     return;
        // }

        // let loginProcessing = false;
        // let checkCount = 0;

        // Poll for authentication status
        // const checkLoginStatus = setInterval(async () => {
        //     checkCount++;

        //     try {
        //         const response = await fetch('/pop_accounts/social-login-complete/', {
        //             headers: {
        //                 'X-Requested-With': 'XMLHttpRequest'
        //             }
        //         });

        //         if (response.ok) {
        //             const userData = await response.json();

        //             if (userData.authenticated && !loginProcessing) {
        //                 loginProcessing = true;
        //                 clearInterval(checkLoginStatus);

        //                 updateNavigationWithUserData(userData);

        //                 // Close popup
        //                 setTimeout(() => {
        //                     try {
        //                         facebookPopup.close();
        //                     } catch (error) {
        //                         console.error(error);
        //                     }
        //                 }, 1500);
        //                 return;
        //             }
        //         } else {
        //             console.log(`Response not OK:`, response.status);
        //         }
        //     } catch (error) {
        //         console.log(`Fetch error:`, error.message);
        //     }

        //     // Stop checking after 10 minutes
        //     if (checkCount > 1200) {
        //         console.log('Authentication checking timeout after 10 minutes');
        //         clearInterval(checkLoginStatus);
        //     }
        // }, 500);
    });



    googleBtn.addEventListener('click', (e) => {
        e.preventDefault()
        console.log('ggogle Button Clicked')
        openPopUp(googleUrl)

    })

    const sModal = document.getElementById('signUpModal')


    // poll for popup close
    // const checkPopup = setInterval(() => {
    //     if (sModal) {
    //         clearInterval(checkPopup);
    //         console.log('sModal is', sModal)
    //         sModal.style.display = "none";
    //         window.location.reload()
    //     }
    // if (popup.closed) {
    //     clearInterval(checkPopup);
    //     console.log('Facebook login popup closed');
    //     // window.location.reload();
    //     updateNavigationAfterLogin();
    // }
    // }, 500);

})





// document.addEventListener('DOMContentLoaded', () => {
//     const googleBtn = document.getElementById("googleSignUpButton");
//     const googleUrl = document.getElementById("googleLoginUrl").value;

//     if (!googleBtn || !googleUrl) return;

//     googleBtn.addEventListener('click', (e) => {
//         e.preventDefault()
//         console.log('google clicked')
//         console.log('googleUrl', googleUrl)

//         const width = 550, height = 600;
//         const left = (screen.width - width) / 2;
//         const top = (screen.height - height) / 2;

//         const googlePopup = window.open(
//             googleUrl,
//             "googleLoginPopup",
//             `width=${width},height=${height}, top=${top}, left=${left}`
//         );

//         if (!googlePopup) {
//             return;
//         }

//         let loginProcessing = false;
//         let checkCount = 0;

//     })
// })




function updateNavigationWithUserData(userData) {
    console.log('Updating navigation with user data:', userData);

    // Update greeting
    const greetingsBox = document.getElementById("greetings_box_name");
    const greetingsContainer = document.getElementById("greetings_container");
    if (greetingsBox && greetingsContainer) {
        greetingsBox.textContent = `Hello ${userData.firstName}`;
        greetingsContainer.style.display = "block";
        console.log('Greeting updated to:', `Hello ${userData.firstName}`);
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
                    <a href="/accounts/dashboard-admin/">
                        <i class='bx bxs-user-detail icon'></i>
                        <span class="text nav-text">Dashboard</span>
                    </a>
                </li>
            `;
            console.log('Adding admin dashboard link');
        } else {
            dashboardLink = `
                <li class="nav-link">
                    <a href="/accounts/dashboard/">
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
                <form id="logout_form" action="/" method="POST">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                    <li class="nav-link">
                        <button type="submit" onclick="performLogout()">
                            <i class='bx bx-log-out icon'></i>
                            <span class="text nav-text">Log out</span>
                        </button>
                    </li>
                </form>
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
    const signUpModal = document.getElementById('signUpModal');
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



// async function updateNavigationAfterLogin(userData) {
//     console.log('updateNavigationAfterLogin called!', userData)

//     // Update greeting
//     const greetingsBox = document.getElementById("greetings_box_name");
//     console.log('greetingsBox', greetingsBox)

//     const greetingsContainer = document.getElementById("greetings_container");
//     console.log('greetingsContainer', greetingsContainer)

//     if (greetingsBox && greetingsContainer) {
//         greetingsBox.textContent = `Hello ${userData.firstName}`;
//         greetingsContainer.style.display = "block";
//     }

//     // Remove login/signup buttons
//     const loginBtn = document.getElementById("login_button");
//     const signupBtn = document.getElementById("signup_button");

//     if (loginBtn) {
//         loginBtn.remove();
//     }
//     if (signupBtn) {
//         signupBtn.remove();
//     }

//     // Add logout button
//     const menuLinks = document.getElementById("menu-links");
//     console.log('menuLinks', menuLinks)

//     if (menuLinks && !document.getElementById("logout_form")) {
//         const logoutForm = `
//                 <form id="logout_form" action="/" method="POST">
//                         <input type="hidden" name="csrfmiddlewaretoken">
//                         <li class="nav-link">
//                             <button type="submit" onclick="{performLogout()}">
//                                 <i class='bx bx-log-out icon'></i>
//                                 <span class="text nav-text">Log out</span>
//                             </button>
//                         </li>
//                     </form>`;

//         menuLinks.insertAdjacentHTML("beforeend", logoutForm);
//     }

//     // Close any login modals
//     if (typeof closeLoginModal === "function") {
//         closeLoginModal()
//     }
//     console.log('Navigation update complete');
// }

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




async function performLogout() {
    console.log('performLogout called')
    try {
        const csrfToken = getCSRFToken();

        if (!csrfToken) {
            window.location.href = '/';
            return;
        }

        const response = await fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
            },
            body: `csrfmiddlewaretoken=${encodeURIComponent(csrfToken)}`,
            credentials: 'same-origin'
        });

        // Always redirect, don't wait for response parsing
        window.location.href = '/';

    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/';
    }
}



