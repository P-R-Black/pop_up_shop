



// var stripe = Stripe(STRIPE_PUBLIC_KEY);

// var elem = document.getElementById('selectedPaymentButtonTwo')
// clientsecret = elem.getAttribute('data-secret')

// console.log('clientsecret', clientsecret)

// var elements = stripe.elements();
// var style = {
//     base: {
//         color: "#000",
//         lineHeight: '2.4',
//         fontSize: '16px'

//     }
// };
// var card = elements.create('card', { style: style })
// card.mount("#card-element")

// var card = elements.create('card', { style: style });
// card.mount("#card-element")

// card.on('change', function (event) {

//     var displayError = document.getElementById('card-errors')
//     if (event.error) {
//         displayError.textContent = event.error.message;
//         $('#card-errors').addClass('alert alert-info');

//     } else {
//         displayError.textContent = '';
//         $('#card-errors').removeClass('alert alert-info');
//     }
// })

// var form = document.getElementById('payment-form');
// form.addEventListener('submit', function (ev) {
//     ev.preventDefault();

//     var custName = document.getElementById('custName').value;
//     var custAdd = document.getElementById('custAdd').value;
//     var custAdd2 = document.getElementById('custAdd2').value;
//     var postCode = document.getElementById('postCode').value;

// $.ajax({
//     type: "POST",
//     url: 'http://127.0.0.1:8000/orders/add/',
//     data: {
//         order_key: clientsecret,
//         csrfmiddlewaretoken: CSRF_TOKEN,
//         action: "post",
//     },
//     success: function (json) {
//         console.log(json.success)

//         stripe.confirmCardPayment(clientsecret, {
//             payment_method: {
//                 card: card,
//                 billing_details: {
//                     address: {
//                         line1: custAdd,
//                         line2: custAdd2
//                     },
//                     name: custName
//                 },
//             }
//         }).then(function (result) {
//             if (result.error) {
//                 console.log('payment error')
//                 console.log(result.error.message);
//             } else {
//                 if (result.paymentIntent.status === 'succeeded') {
//                     console.log('payment processed')
//                     // There's a risk of the customer closing the window before callback
//                     // execution. Set up a webhook or plugin to listen for the
//                     // payment_intent.succeeded event that handles any business critical
//                     // post-payment actions.
//                     window.location.replace("http://127.0.0.1:8000/payment/placedorder/");
//                 }
//             }
//         });

//     },
//     error: function (xhr, errmsg, err) { },
// });
// })


window.addEventListener('DOMContentLoaded', () => {
    // payment options dropdown variables
    var expandButton = document.querySelector(".expandButton");
    var checkoutOptionsContainer = document.querySelector('.checkout_options_container')

    // subtotal options dropdown variables
    var subtotalExpand = document.querySelector(".subtotalExpand");
    var purchaseDetailsContainer = document.querySelector('.purchase_details_container')

    // shipping button options variables
    var shippingButtons = document.querySelectorAll(".shippingButtons")
    const shippingCost = document.getElementById('shippingCost')
    const orderQuantity = document.getElementById('purchaseQuantity').innerHTML
    const processingFee = document.getElementById('processingFee').innerHTML
    const salesTax = document.getElementById('purchaseTax').innerHTML
    const purchaseSubtotal = document.getElementById('purchaseSubtotal').innerHTML
    let shippingMath;
    let orderTotal;
    let shipping;


    // update primary payment button, bottom of checkout page variables
    const selectedPaymentButton = document.getElementById('selectedPaymentButton');

    // update secondary payment button, bottom of checkout page variables
    const selectedPaymentButtonTwo = document.getElementById('selectedPaymentButtonTwo')
    const checkoutOptions = document.getElementById('checkoutOptions');


    // payment options dropdown
    expandButton.addEventListener("click", function () {
        /* Toggle between adding and removing the "active" class,
        to highlight the button that controls the panel */
        this.classList.toggle("active");
        checkoutOptionsContainer.classList.toggle('show')

    });



    // update primary payment button
    const payBtnIcon = document.querySelectorAll('payBtnIcon');
    console.log('payBtnIcon', payBtnIcon)

    const payBtnText = document.querySelectorAll('payBtnText');
    console.log('payBtnText', payBtnText)

    const hiddenInput = document.getElementById('selectedPaymentMethod');

    // Listen for clicks on payment buttons
    checkoutOptions.addEventListener('click', function (event) {
        const clickedButton = event.target.closest('.payment_option_buttons');

        if (clickedButton) {
            // Get the icon (either <i> or <img>) and text
            const icon = clickedButton.querySelector('i, img');
            const text = clickedButton.textContent.trim(); // Extract button text
            const method = clickedButton.dataset.method;
            console.log('the method is', method)

            // Update the primary payment button
            selectedPaymentButton.innerHTML = ''; // Clear current content

            if (icon && payBtnIcon) {
                // Clone the icon and append to the button

                const newIcon = icon.cloneNode(true);
                selectedPaymentButton.appendChild(newIcon);

                // payBtnIcon.innerHTML = ''; // clear old icon
                // console.log('old payBtnIcon.innerHTML', payBtnIcon.innerHTML)
                // payBtnIcon.appendChild(icon.cloneNode(true)); // clone new
                // console.log('new payBtnIcon.innerHTML', payBtnIcon.innerHTML)
            }

            if (payBtnText) {
                payBtnText.textContent = `${text}`
            }
            hiddenInput.value = method

            // Append the text
            const newText = document.createTextNode(` ${text}`);
            selectedPaymentButton.appendChild(newText);

            // close dropdown
            checkoutOptionsContainer.classList.toggle('show')
        }
    });


    // update secondary payment button, bottom of checkout page

    // Listen for clicks on payment buttons
    checkoutOptions.addEventListener('click', function (event) {
        const clickedButton = event.target.closest('.payment_option_buttons');

        if (clickedButton) {
            // Get the icon (either <i> or <img>) and text
            const icon = clickedButton.querySelector('i, img');
            console.log('icon', icon)

            const text = clickedButton.textContent.trim(); // Extract button text
            console.log('text', text)

            // Update the primary payment button
            selectedPaymentButtonTwo.innerHTML = ''; // Clear current content

            if (icon && payBtnIcon) {
                // Clone the icon and append to the button
                const newIcon = icon.cloneNode(true);
                selectedPaymentButtonTwo.appendChild(newIcon);

            }


            // Append the text
            const newText = document.createTextNode(` ${text}`);
            selectedPaymentButtonTwo.appendChild(newText);
        }
    });


    // subtotal options dropdown
    subtotalExpand.addEventListener("click", function () {
        this.classList.toggle("subTotalactive");
        purchaseDetailsContainer.classList.toggle('subTotalShow')

    });


    // shipping button options
    shippingButtons.forEach((button) => {
        shippingMath = 1499 * Number(orderQuantity)
        shippingCost.innerText = `$${shippingMath / 100}`

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

    // get subtotal and total
    const calculateSubtotal = (proccessFee, shippingCost, tax) => {

        const purchaseSubtotal = document.getElementById('purchaseSubtotal').innerHTML.replace('$', '').replace(',', '')
        const purchaseTotal = document.getElementById('purchaseTotal')

        let totalCalculation = parseFloat(purchaseSubtotal) + parseFloat(proccessFee) + parseFloat(tax) + parseFloat(shippingCost)
        purchaseTotal.innerHTML = `$${numberWithCommas(totalCalculation)}`

    }


    ////////////////// IN THE WORKS //////////////////
    var stripe = Stripe(STRIPE_PUBLIC_KEY);
    console.log('stripe', stripe)
    console.log('STRIPE_PUBLIC_KEY', STRIPE_PUBLIC_KEY)


    const clientsecret = selectedPaymentButtonTwo.getAttribute('data-secret');
    console.log('clientsecret', clientsecret)

    selectedPaymentButtonTwo.addEventListener('click', (e) => {
        e.preventDefault()
        console.log('selectedPaymentButtonTwo button clicked')

        if (!selectedMethod) {
            alert('Please choose a payment method.')
            return;
        }

        const selectedMethod = hiddenInput.value;
        console.log('Selected Payment Method:', selectedMethod);

        let custName, prefix, suffix, middleName, addressLine2

        if (document.querySelector('.shipping_to_name')) {
            custName = document.querySelector('.shipping_to_name');
        }

        if (document.querySelector('.shipping_name_prefix')) {
            prefix = document.querySelector('.shipping_name_prefix');
        }

        if (document.querySelector('.shipping_to_middle_name')) {
            middleName = document.querySelector('.shipping_to_middle_name');
        }
        if (document.querySelector('.shipping_to_suffix')) {
            suffix = document.querySelector('.shipping_to_suffix');
        }

        if (document.getElementById('addressLine2')) {
            addressLine2 = document.getElementById('addressLine2');
        }

        var firstName = document.querySelector('.shipping_to_first_name');
        var lastName = document.querySelector('.shipping_to_last_name');
        var addressLine = document.getElementById('addressLine')
        var aptSte = document.getElementById('aptSuite')
        var city = document.getElementById('shipping_town_city')
        var state = document.getElementById('shipping_state')
        var zip = document.getElementById('shipping_postcode')

        const cleanText = el => el ? el.innerHTML.trim().replace(/&nbsp;/g, '') : '';

        console.log('prefix:', cleanText(prefix));
        console.log('custName', cleanText(custName));
        console.log('firstName', cleanText(firstName));
        console.log('middleName', cleanText(middleName));
        console.log('lastName', cleanText(lastName));
        console.log('suffix', cleanText(suffix));

        console.log('addressLine', cleanText(addressLine))
        console.log('addressLine2', cleanText(addressLine2))
        console.log('aptSte', cleanText(aptSte))

        console.log('city', cleanText(city));
        console.log('state', cleanText(state));
        console.log('zip', cleanText(zip));


        // Stripe Info
        var elements = stripe.elements();
        console.log('elements', elements)

        var style = {
            base: {
                color: "#000",
                lineHeight: '2.4',
                fontSize: '16px',
                border: '2px solid red',
            }
        };

        var card = elements.create("card", { style: style });
        console.log('card', card);

        card.mount("#card-element");
        card.on('change', function (event) {
            var displayError = document.getElementById('card-errors')
            if (event.error) {
                displayError.textContent = event.error.message;
                $('#card-errors').addClass('alert alert-info');
            } else {
                displayError.textContent = '';
                $('#card-errors').removeClass('alert alert-info');
            }
        });



        switch (selectedMethod) {
            case 'apple_pay':
            case 'google_pay':
            case 'credit_card':
                // call stripe
                makeStripeCall(clientsecret)
                break;
            case 'paypal':
                // Redirect to PayPal flow
                console.log('paypal')
                break;
            case 'venmo':
                // Venmo flow
                console.log('venmo')
                break;
            case 'stable_coin':
                // Venmo flow
                console.log('stable_coin')
                break;
            default: alert("Please choose a valid payment option.");
        }
    })

})





const makeStripeCall = (clientsecret) => {
    console.log('stripe has been called', clientsecret)


    $.ajax({
        type: "POST",
        url: '/orders/add/',
        data: {
            order_key: clientsecret,
            csrfmiddlewaretoken: CSRF_TOKEN,
            action: "post",
        },
        success: function (json) {
            console.log('json.success', json.success)

            stripe.confirmCardPayment(clientsecret, {
                payment_method: {
                    card: card,
                    billing_details: {
                        address: {
                            line1: addressLine.innerHTML.trim().replace('&nbsp;', ''),
                            line2: addressLine ? addressLine : ""
                        },
                        name: custName.innerHTML.trim().replace('&nbsp;', '')
                    },
                }
            }).then(function (result) {
                if (result.error) {
                    console.log('payment error')
                    console.log(result.error.message);
                } else {
                    if (result.paymentIntent.status === 'succeeded') {
                        console.log('payment processed')
                        // There's a risk of the customer closing the window before callback
                        // execution. Set up a webhook or plugin to listen for the
                        // payment_intent.succeeded event that handles any business critical
                        // post-payment actions.
                        window.location.replace("http://127.0.0.1:8000/payment/placedorder/");
                    }
                }
            });

        },
        error: function (xhr, errmsg, err) { },
    });

}




