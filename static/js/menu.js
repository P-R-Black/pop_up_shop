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


const inviteFriendModal = document.getElementById('inviteFriendModal');
const inviteFriendModalBtn = document.querySelectorAll('.inviteFriendBtn');
const closeInviteModal = document.querySelector('.closeInviteModal');





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



document.addEventListener('DOMContentLoaded', function () {

    darkLighModeToggle()

    // Invite Friend Modal
    if (inviteFriendModalBtn) {
        inviteFriendModalBtn.forEach((inv) => {
            inv.addEventListener('click', () => {
                inviteFriendModal.style.display = 'block';
            })
        })
    } else {
        console.warn('bidButton not found in the DOM.');
    }
    // Close Invite Friend Modal
    if (closeInviteModal) {
        // Close the modal when the close span is clicked
        closeInviteModal.addEventListener('click', function () {
            inviteFriendModal.style.display = 'none';
        });
    } else {
        console.warn('closeInviteModal span not found in the DOM.');
    }
    // Close Invite Friend Modal If Outside of Modal Clicked
    if (inviteFriendModal) {
        window.addEventListener('click', function (event) {
            if (event.target === inviteFriendModal) {
                inviteFriendModal.style.display = 'none';
            }
        });
    } else {
        console.warn('inviteFriendModal not found in the DOM.');
    }


    // Opens Register Modal When Email Invite Clicks on Link
    const params = new URLSearchParams(window.location.search);
    if (params.get("show_auth_modal") === "true") {
        signUpModal.style.display = 'block';
    }


    // Shrinks Side Navigation Bar
    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('close');

        navLogoText.classList.add('fade-out'); // Start fade-out

        setTimeout(() => {
            if (sidebar.classList.contains('close')) {
                navLogoText.innerText = 'TPU';
                navLogoText.style.fontSize = '32px';
            } else {
                navLogoText.innerText = 'The Pop Up';
                navLogoText.style.fontSize = '48px';
            }

            navLogoText.classList.remove('fade-out');
            navLogoText.classList.add('fade-in');

            // Remove the fade-in class after animation completes
            setTimeout(() => {
                navLogoText.classList.remove('fade-in');
            }, 300); // Match this to your CSS transition time
        }, 150); // Wait for fade-out before changing text
    });

    searchBtn.addEventListener('click', () => {
        sidebar.classList.remove('close');
    })



    mobileSearchIcon.addEventListener('click', () => {
        mobileSearchBox.classList.toggle('hide-mobile-search-box')
        navLogoText.classList.toggle('hide-logo-text')
    })


    // Bid Modal
    // Get the modal, button, and close span

    const bidButton = document.querySelectorAll('.bidButtonClass')
    if (bidButton) {
        bidButton.forEach((btn) => {
            btn.addEventListener('click', function () {
                console.log("I've been clicked the bidButton")
                const productId = this.dataset.productId;
                const modal = document.getElementById(`bidModal-${productId}`);
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

    // Billing Address Update on Checkout Page
    const tabButtons = document.querySelectorAll('.billing_address_button');
    const tabContents = document.querySelectorAll('.billing_address_content');

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
    });



    // Shipments in Admin Dashboard
    const shipTabButtons = document.querySelectorAll('.shipment_status_button');
    const shipTabContents = document.querySelectorAll('.all_shipments_section');

    shipTabButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const target = button.getAttribute('data-tab');

            // Remove "active" class from all;
            shipTabButtons.forEach(btn => btn.classList.remove('active_shipment'))
            shipTabContents.forEach(content => content.classList.remove('active_shipment'));

            // Add active to selected
            button.classList.add('active_shipment');
            document.getElementById(target).classList.add('active_shipment')
        })
    });


    // Products in Update Product Info
    const prodTabButtons = document.querySelectorAll('.product_status_button');
    const prodTabContents = document.querySelectorAll('.all_products_section');

    prodTabButtons.forEach(prodButton => {
        prodButton.addEventListener('click', (e) => {
            e.preventDefault();
            const target = prodButton.getAttribute('data-tab');

            prodTabButtons.forEach(btn => btn.classList.remove('active_product'));
            prodTabContents.forEach(content => content.classList.remove('active_product'));

            // Add active to selected
            prodButton.classList.add('active_product');
            document.getElementById(target).classList.add('active_product')
        })
    });



    // Grab email for Password Reset
    window.addEventListener('DOMContentLoaded', () => {
        const urlParams = newURLSearchParams(window.location.search);
        const email = urlParams.get('email')

        if (email) {
            const emailInput = document.querySelector('#id_email_for_password_reset_one');
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
    };



    // Password Reset Confirm
    const resetPasswordFormBtn = document.querySelector('.resetPasswordFormBtn');

    const resetPasswordForm = document.getElementById('resetPasswordForm');

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
    };

    // Shipping Address Update in Checkout Page
    const shippingTabButtons = document.querySelectorAll('.modal_tab');
    const shippingTabContents = document.querySelectorAll('.modal_tab_content');

    shippingTabButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const target = button.getAttribute('data-tab');

            // Remove "active" class from all;
            shippingTabButtons.forEach(btn => btn.classList.remove('activated'))
            shippingTabContents.forEach(content => content.classList.remove('activated'));

            // Add active to selected
            button.classList.add('activated');
            document.getElementById(target).classList.add('activated')
        })
    });


    // Nav Dashboard Display and Hide Links
    // var expandDashLink = document.querySelector(".dashboard_expand");
    // var dashboardLinksContainer = document.querySelector('.dashboard_nav_container')

    // payment options dropdown
    // expandDashLink.addEventListener("click", function () {
    // this.classList.toggle("active");
    // dashboardLinksContainer.classList.toggle('show')

    // });


    // expandInnerButton = document.querySelectorAll('.inner_dashboard_expand');

    // // Nav Dashboard Inner Links Show and Hide
    // expandInnerButton.forEach(btn => {
    //     btn.addEventListener('click', function () {
    //         console.log('inner clicked!')
    //         console.log('expandInnerButton', expandInnerButton)

    //         const group = this.closest('.dashboard-group');    // safe container
    //         console.log('group', group)

    //         const container = group?.querySelector('.inner_dashboard_container');
    //         console.log('container', container)

    //         if (!container) return;
    //         this.classList.toggle('active');
    //         container.classList.toggle('show');

    //         // accessibility nicety
    //         const expanded = this.classList.contains('active');
    //         this.setAttribute('aria-expanded', expanded);
    //         container.setAttribute('aria-hidden', !expanded);
    //     });
    // });


    // Main dashboard toggle
    const dashboardExpand = document.querySelector('.dashboard_expand');
    const dashboardSubmenu = document.getElementById('dashboard-submenu');


    // Also add specific click event to the expand icon
    dashboardExpand.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('clicked!')
        dashboardSubmenu.classList.toggle('show');
        dashboardExpand.classList.toggle('expanded');
    });

    // Category toggles
    const categoryHeaders = document.querySelectorAll('.category-header');

    categoryHeaders.forEach(header => {
        header.addEventListener('click', function (e) {
            e.preventDefault();

            const category = this.dataset.category;
            const submenu = document.getElementById(category + '-submenu');
            const expandIcon = this.querySelector('.category-expand');

            // Toggle current submenu
            submenu.classList.toggle('show');
            expandIcon.classList.toggle('expanded');
        });
    });






})




function displayFormErrorsTwo(errors) {
    console.log('errors', errors);

    const errorContainer = document.querySelector('.registration_form_errors');
    errorContainer.innerHTML = ''; // Clear previous errors
    errorContainer.style.display = 'block';

    let parsedErrors = {};

    try {
        parsedErrors = JSON.parse(errors);  // Try to parse Django-style JSON errors
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





// address change modal
document.addEventListener('DOMContentLoaded', function () {
    // Get the modal, button, and close span
    const addressChangeModal = document.getElementById('addressChangeModal');
    const addressChangeBtn = document.getElementById('addressChangeButton');
    const addressChangeSpan = document.querySelector('.closeAddressModal');

    const billingAddressChangeModal = document.getElementById('billingAddressChangeModal')
    const billingAddressChangeSpan = document.querySelector('.closeBillingAddressModal')
    const billingAddressChangeBtn = document.getElementById('billingAddressChangeButton');

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


    // Billing Address
    // Show the modal when the button is clicked
    billingAddressChangeBtn.addEventListener('click', function () {
        billingAddressChangeModal.style.display = 'block';
    });

    // Close the modal when the close span is clicked
    billingAddressChangeSpan.addEventListener('click', function () {
        billingAddressChangeModal.style.display = 'none';
    });

    // Close the modal when clicking outside of it
    window.addEventListener('click', function (event) {
        if (event.target === billingAddressChangeModal) {
            billingAddressChangeModal.style.display = 'none';
        }
    });


    document.getElementById('billingAddressChangeButton').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('billingAddressChangeModal').style.display = 'block';
    })

    document.getElementById('confirmBillingAddress').addEventListener('click', () => {
        const selected = document.querySelector('input[name="billing_address_choice"]:checked');
        if (selected) {
            const addressId = selected.value;
            fetch("{% url 'payment:set_billing_address' %}", {
                method: "POST",
                headers: {
                    "X-CSRFToken": "{{ csrf_token }}",
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ address_id: addressId })
            }).then(res => {
                if (res.ok) this.location.reload();
            })
        }
    })
});
