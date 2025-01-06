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

    console.log('sun clicked')

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




