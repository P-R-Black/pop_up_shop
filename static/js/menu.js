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

const timerDisplay = document.querySelector('#code-timer');


// 2f auth confirmation
const confirmSubmitBtn = document.querySelector('.confirm_submit_button');
const confirmInputs = document.querySelectorAll('.confirmation_input input');

// sign-up moddal
document.addEventListener('DOMContentLoaded', function () {
    // Get the modal, button, and close span


    if (signUpModalBtn) {
        signUpModalBtn.forEach((sub) => {
            sub.addEventListener('click', () => {
                signUpModal.style.display = 'block';
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
});


// sign up email modal 
document.addEventListener('DOMContentLoaded', function () {
    const backChevron = document.getElementById('backChevron');
    const signUpTitleOptionsContainer = document.querySelector('.sign_up_title_options_container');
    const emailVerificationContainer = document.querySelector('.email_verification_container');
    const emailSignUpButton = document.querySelector('.emailSignUpButton');

    const signUpEmailContainer = document.querySelector('.sign_up_email_container');
    const emailSubmitButton = document.querySelector('.emailSubmitButton');

    const emailLoginContainer = document.querySelector('.email_login_container');

    const confirmContainerBackChevron = document.getElementById('confirmContainerBackChevron');

    const confirmContainerBackChevronTwo = document.getElementById('confirmContainerBackChevronTwo');
    const confirmContainerBackChevronThree = document.getElementById('confirmContainerBackChevronThree');

    const confirmContainerBackChevronSix = document.getElementById('confirmContainerBackChevronSix');
    const signUpEmailConfirmContainer = document.querySelector('.sign_up_email_confirm_container');
    const passwordSubmitButton = document.querySelector('.passwordSubmitButton');
    const loginSubmitButton = document.querySelector('.loginSubmitButton');
    const modal = document.querySelector('.sign_up_modal');



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
                        console.log(" formData.get('email')", formData.get('email'))
                        emailVerificationContainer.classList.remove('show_container');
                        emailVerificationContainer.classList.add('shift_left');
                        emailLoginContainer.classList.remove('hide_email_login_container');
                        emailLoginContainer.classList.add('show_email_login_container');

                        emailProvidedSigninPopup.forEach((epp) => epp.innerHTML = formData.get('email'));
                    } else if (data.status === true) {
                        const email = formData.get('email');
                        sessionStorage.setItem('auth_email', email);
                        // Go to registration container
                        console.log(" formData.get('email') 2", formData.get('email'))
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
                header: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data['authenticated'] === true) {
                        emailLoginContainer.classList.remove('show_email_login_container');
                        emailLoginContainer.classList.add('hide_email_login_container_to_left');
                        signUpEmailConfirmContainer.classList.remove('hide_ign_up_email_confirm_container')
                        signUpEmailConfirmContainer.classList.add('show_sign_up_email_confirm_container')

                        setTimeout(() => {
                            const fiveMinutes = 5 * 60;
                            startCodeTimer(fiveMinutes, timerDisplay)
                        }, 100)


                    } else {
                        console.error('Unexpected response:', data);
                    }
                })
                .catch(error => {
                    console.error('Error subitting password', error)
                })
        })
    }

    if (confirmContainerBackChevronSix) {
        confirmContainerBackChevronSix.addEventListener('click', () => {
            console.log('backbutton six clicked!')
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

            const code = Array.from(confirmInputs).map(input => input.value).join('');

            fetch('/pop_accounts/auth/verify-code/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ code })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.verified) {

                        if (signUpModal) {
                            signUpModal.style.display = 'none';
                        }

                    } else {
                        alert(data.error || 'Invalid code.')
                    }
                })
                .catch(err => {
                    console.error('Two-Factor Authentication verification failed', err);
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

})


// Submit Registration Form
const registrationSubmitButton = document.querySelector('.registrationSubmitButton');

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
                if (data.success) {
                    // Show success UI or redirect
                    console.log('User registered!');
                } else if (data.errors) {
                    displayFormErrors(data.errors);
                }
            })
            .catch(error => {
                console.error('Error submitting registration form:', error);
            });
    });
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
    const modal = document.getElementById('bidModal');
    const btn = document.getElementById('bidButton');
    const span = document.querySelector('.closeModal');

    if (btn) {
        // Show the modal when the button is clicked
        btn.addEventListener('click', function () {
            modal.style.display = 'block';
        });
    } else {
        console.warn('bidButton not found in the DOM.');
    }


    const bidButton = document.querySelectorAll('.bidButtonClass')
    bidButton.forEach((bidBtn) => {
        bidBtn.addEventListener('click', function () {
            if (bidBtn) {
                // Show the modal when the button is clicked
                bidBtn.addEventListener('click', function () {
                    modal.style.display = 'block';
                });
            } else {
                console.warn('bidButton not found in the DOM.');
            }
        })
    })



    if (span) {
        // Close the modal when the close span is clicked
        span.addEventListener('click', function () {
            modal.style.display = 'none';
        });
    } else {
        console.warn('closeModal span not found in the DOM.');
    }

    // Close the modal when clicking outside of it
    if (modal) {
        window.addEventListener('click', function (event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    } else {
        console.warn('bidModal not found in the DOM.');
    }
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
var shippingButtons = document.querySelectorAll(".button_long_option")
const shippingCost = document.getElementById('shippingCost')

shippingButtons.forEach((button) => {
    button.addEventListener("click", function () {
        // Loop through all buttons and remove "active" class if present
        if (body) {
            shippingButtons.forEach((btn) => btn.classList.remove("chosen"));

            // Add "active" class to the button that was clicked
            this.classList.add("chosen");

        }
        console.log('button.innerHTML', button.innerHTML)
        if (button.innerHTML == "Standard Shipping") {
            shippingCost.innerText = "$14.99"
        }

        if (button.innerHTML == "Express Shipping") {
            shippingCost.innerText = "$29.99"
        }
        calculateSubtotal()

    });
});


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

const calculateSubtotal = () => {
    const purchaseSubtotal = document.getElementById('purchaseSubtotal')
    const purchasePrice = document.getElementById('purchasePrice').innerHTML.replace('$', '')
    const purchaseQuantity = document.getElementById('purchaseQuantity').innerHTML
    const processingFee = document.getElementById('processingFee').innerHTML.replace('$', '')
    const shippingInnerHTML = shippingCost.innerHTML.replace('$', '')
    const purchaseTax = document.getElementById('purchaseTax')

    const merchandiseCost = Number(purchasePrice) * Number(purchaseQuantity)
    const workingSubtotal = merchandiseCost + Number(processingFee) + Number(shippingInnerHTML)
    const workingTaxAmount = workingSubtotal * .075
    purchaseTax.innerHTML = "$" + String(workingTaxAmount.toFixed(2))
    purchaseSubtotal.innerHTML = "$" + String(Number(workingTaxAmount.toFixed(2)) + workingSubtotal)
}




