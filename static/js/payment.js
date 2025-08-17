window.addEventListener('DOMContentLoaded', async () => {

    // payment options dropdown variables
    var expandButton = document.querySelector(".expandButton");
    var checkoutOptionsContainer = document.querySelector('.checkout_options_container')

    // subtotal options dropdown variables
    var subtotalExpand = document.querySelector(".subtotalExpand");
    var purchaseDetailsContainer = document.querySelector('.purchase_details_container')

    // shipping button options variables
    var shippingButtons = document.querySelectorAll(".shippingButtons")
    const shippingCost = document.getElementById('shippingCost')
    const processingFee = document.getElementById('processingFee').innerHTML
    const salesTax = document.getElementById('purchaseTax').innerHTML
    let orderQuantity;

    if (document.getElementById('purchaseQuantity')) {
        orderQuantity = document.getElementById('purchaseQuantity').innerHTML
    }

    // Message Div
    const messagesDiv = document.getElementById('payment-messages');

    // const purchaseSubtotal = document.getElementById('purchaseSubtotal').innerHTML
    let shippingMath;
    let orderTotal;
    let shipping;


    // Container for Making Payment
    const purchaseDetailConfirmPay = document.querySelector('.purchase_details_confirm_pay');

    // update primary payment button, bottom of checkout page variables
    const selectedPaymentButton = document.getElementById('selectedPaymentButton');

    // update secondary payment button, bottom of checkout page variables
    const checkoutOptions = document.getElementById('checkoutOptions');

    // Stripe Button
    var stripe = Stripe(STRIPE_PUBLISHABLE_KEY);
    const creditCardForm = document.getElementById('card-payment-form')
    creditCardForm.style.display = 'none'

    // const confirmCardPayment = document.getElementById('confirm-card-payment')

    // payment options dropdown
    expandButton.addEventListener("click", function () {
        /* Toggle between adding and removing the "active" class,
        to highlight the button that controls the panel */
        this.classList.toggle("active");
        checkoutOptionsContainer.classList.toggle('show')

    });



    // update primary payment button
    const payBtnIcon = document.querySelectorAll('.payBtnIcon');
    const payBtnText = document.querySelectorAll('.payBtnText');
    const hiddenInput = document.getElementById('selectedPaymentMethod');



    // Listen for clicks on payment buttons
    checkoutOptions.addEventListener('click', function (event) {
        const clickedButton = event.target.closest('.payment_option_buttons');

        if (clickedButton) {
            // Get the icon (either <i> or <img>) and text
            const icons = clickedButton.querySelectorAll('i, img, .payBtnIcon img');
            const text = clickedButton.textContent.trim(); // Extract button text
            const method = clickedButton.dataset.method;
            console.log('the method is', method)

            // Update the primary payment button
            selectedPaymentButton.innerHTML = ''; // Clear current content
            let newIcon;


            if (icons) {
                icons.forEach((icon) => {
                    newIcon = icon.cloneNode(true);
                    selectedPaymentButton.appendChild(newIcon);
                })
            }


            // if (icons && payBtnIcon) {
            //     // Clone the icon and append to the button
            //     const newIcon = icons.cloneNode(true);
            //     selectedPaymentButton.appendChild(newIcon);
            // }

            // if (payBtnText) {
            //     payBtnText.textContent = `${text}`
            // }
            hiddenInput.value = method

            // Append the text
            const newText = document.createTextNode(` ${text}`);
            selectedPaymentButton.appendChild(newText);


            if (method === "apple_pay") {
                buttonUnMount()
                creditCardForm.style.display = 'none'
                makePaymentButton(method, purchaseDetailConfirmPay, 'payment_option_buttons_two', 'apple-pay-button', newIcon, newText)
                console.log('call apple_pay stuff')
            }

            if (method == "google_pay") {
                buttonUnMount()
                creditCardForm.style.display = 'none'
                makePaymentButton(method, purchaseDetailConfirmPay, 'payment_option_buttons_two', 'google-pay-button', newIcon, newText)
                console.log('call google_pay stuff')
            }

            if (method == "paypal") {
                buttonUnMount()
                creditCardForm.style.display = 'none'
                makePaymentButton(method, purchaseDetailConfirmPay, 'payment_option_buttons_two', 'paypal-button-container', newIcon, newText)
                console.log('call paypal stuff')
            }

            if (method == "venmo") {
                buttonUnMount()
                creditCardForm.style.display = 'none'
                makePaymentButton(method, purchaseDetailConfirmPay, 'payment_option_buttons_two', 'venmo-button-container', newIcon, newText)
                console.log('call venmo stuff')
            }

            if (method == "credit_card") {
                buttonUnMount()
                creditCardForm.style.display = 'block'
                makePaymentButton(method, purchaseDetailConfirmPay, 'payment_option_buttons_two', 'confirm-card-payment', newIcon, newText)
                console.log('credit_card stuff')
            }

            if (method == "stable_coin") {
                buttonUnMount()
                creditCardForm.style.display = 'none'
                makePaymentButton(method, purchaseDetailConfirmPay, 'payment_option_buttons_two', 'stable-coin-payment', newIcon, newText)
                console.log('stable_coin stuff')
            }

        };

        // close dropdown
        checkoutOptionsContainer.classList.toggle('show')

    });



    // subtotal order details dropdown
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
            let taxRate = document.getElementById('taxRate').innerHTML;

            if (button.name == "standard" && orderQuantity > 0) {
                shippingMath = 1499 * Number(orderQuantity)
                shippingCost.innerText = `$${shippingMath / 100}`
                shipping = shippingCost.innerText.replace("$", "").replace(",", "")
                calculateSubtotal(processFee, shipping, taxRate)
            }

            if (button.name == "express" && orderQuantity > 0) {
                shippingMath = 2499 * Number(orderQuantity)
                shippingCost.innerText = `$${shippingMath / 100}`
                shipping = shippingCost.innerText.replace("$", "").replace(",", "")
                calculateSubtotal(processFee, shipping, taxRate)
            }
            buttonUnMount()
        });
    });



    // get subtotal and total
    const calculateSubtotal = (proccessFee, shippingCost, taxRate) => {

        const purchaseSubtotal = document.getElementById('purchaseSubtotal').innerHTML.replace('$', '').replace(',', '')
        let tax = parseFloat(taxRate) * parseFloat(purchaseSubtotal);
        const purchaseTotal = document.getElementById('purchaseTotal')
        let totalCalculation = parseFloat(purchaseSubtotal) + parseFloat(proccessFee) + parseFloat(tax) + parseFloat(shippingCost)
        let purchaseTotalCalc = totalCalculation.toFixed(2)

        console.log('purchaseTotalCalc', purchaseTotalCalc)
        purchaseTotal.innerHTML = `$${parseFloat(purchaseTotalCalc).toLocaleString()}`

    }


    const cleanText = el => el ? el.innerHTML.trim().replace(/&nbsp;/g, '') : '';


    const getShippingAddressInfo = () => {
        let shippingOjbect = {}

        let shippingCustName, shippingPrefix, shippingSuffix, shippingMiddleName, shippingAddressLine2, shippingPhoneNumber

        if (document.querySelector('.shipping_to_name')) {
            shippingCustName = document.querySelector('.shipping_to_name');
        }

        if (document.querySelector('.shipping_name_prefix')) {
            shippingPrefix = document.querySelector('.shipping_name_prefix');
        }

        if (document.querySelector('.shipping_to_middle_name')) {
            shippingMiddleName = document.querySelector('.shipping_to_middle_name');
        }
        if (document.querySelector('.shipping_to_suffix')) {
            shippingSuffix = document.querySelector('.shipping_to_suffix');
        }

        if (document.getElementById('shippingAddressLine2')) {
            shippingAddressLine2 = document.getElementById('shippingAddressLine2');
        }

        if (document.querySelector('.shipping_phone_number')) {
            shippingPhoneNumber = document.querySelector('.shipping_phone_number')
        }

        var shippingFirstName = document.querySelector('.shipping_to_first_name');
        var shippingLastName = document.querySelector('.shipping_to_last_name');
        var shippingAddressLine = document.getElementById('addressLine')
        var shippingAptSte = document.getElementById('aptSuite')
        var shippingCity = document.getElementById('shipping_town_city')
        var shippingState = document.getElementById('shipping_state')
        var shippingPostCode = document.getElementById('shipping_postcode')
        var shippingAddressId = document.getElementById('shippingAddressData').value

        shippingOjbect = {
            'shippingPrefix': cleanText(shippingPrefix),
            'shippingCustName': cleanText(shippingCustName),
            'shippingFirstName': cleanText(shippingFirstName),
            'shippingMiddleName': cleanText(shippingMiddleName),
            'shippingLastName': cleanText(shippingLastName),
            'shippingSuffix': cleanText(shippingSuffix),
            'shippingAddressLine': cleanText(shippingAddressLine),
            'shippingAddressLine2': cleanText(shippingAddressLine2),
            'shippingAptSte': cleanText(shippingAptSte),
            'shippingCity': cleanText(shippingCity),
            'shippingState': cleanText(shippingState),
            'shippingPostCode': cleanText(shippingPostCode),
            'shippingPhoneNumber': cleanText(shippingPhoneNumber) || shippingPhoneNumber.value || shippingPhoneNumber.textContent || '',
            'shippingAddressId': shippingAddressId
        }


        return shippingOjbect;

    }


    const getBillingAddressInfo = () => {
        let billingObject = {}

        let billingPrefix, billingSuffix, billingMiddleName, billingAddressLine2, billingPhoneNumber

        if (document.querySelector('.billing_to_name')) {
            billingCustName = document.querySelector('.billing_to_name');
        }

        if (document.querySelector('.billing_name_prefix')) {
            billingPrefix = document.querySelector('.billing_name_prefix');
        }

        if (document.querySelector('.billing_to_middle_name')) {
            billingMiddleName = document.querySelector('.billing_to_middle_name');
        }
        if (document.querySelector('.billing_to_suffix')) {
            billingSuffix = document.querySelector('.billing_to_suffix');
        }

        if (document.getElementById('billingAddressLine2')) {
            billingAddressLine2 = document.getElementById('billingAddressLine2');
        }

        if (document.querySelector('.billing_phone_number')) {
            billingPhoneNumber = document.querySelector('.billing_phone_number');
        }

        var billingCustName = USER;
        var billingFirstName = document.querySelector('.billing_to_first_name');
        var billingLastName = document.querySelector('.billing_to_last_name');
        var billingAddressLine = document.getElementById('billingAddressLine');
        var billingAptSte = document.getElementById('billingAptSuite');
        var billingCity = document.getElementById('billing_town_city');
        var billingState = document.getElementById('billing_state');
        var billingPostCode = document.getElementById('billing_postcode');

        var billingAddressId = document.getElementById('billingAddressData').value


        billingObject = {
            'billingPrefix': cleanText(billingPrefix),
            'billingCustName': billingCustName,
            'billingFirstName': cleanText(billingFirstName),
            'billingMiddleName': cleanText(billingMiddleName),
            'billingLastName': cleanText(billingLastName),
            'billingSuffix': cleanText(billingSuffix),
            'billingAddressLine': cleanText(billingAddressLine),
            'billingAddressLine2': cleanText(billingAddressLine2),
            'billingAptSte': cleanText(billingAptSte),
            'billingCity': cleanText(billingCity),
            'billingState': cleanText(billingState),
            'billingPostCode': cleanText(billingPostCode),
            'billingPhoneNumber': cleanText(billingPhoneNumber) || billingPhoneNumber.value || billingPhoneNumber.textContent || '',
            'billingAddressId': billingAddressId,
            'billingEmail': USER_EMAIL
        }


        return billingObject;

    }

    const getFinalAmount = () => {
        const cleanAmount = purchaseTotal.innerHTML.replace('$', '').replace(',', '')
        amount = (parseFloat(cleanAmount) * 100).toFixed(2).toString().split('.')
        console.log('inside getFinalAmount', amount)
        return Number(amount[0])
    }

    const createOrderPayLoad = (userId, payment_data_id, clientSecret, total_paid, shippingObject, billingObject, couponId, discount, paymentMethod) => {
        // userId: str, stripeId: str, total_paid: int, shippingObject: dict, billingObject: dict, couponId: str, discount: int

        const orderPayLoad = {
            payment_data_id: payment_data_id,
            order_key: clientSecret,
            user_id: userId, // get from context or session
            total_paid: total_paid / 100,
            full_name: billingObject.billingCustName,
            email: billingObject.billingEmail,
            address1: billingObject.billingAddressLine,
            address2: billingObject.billingAddressLine2,
            postal_code: billingObject.billingPostCode,
            apartment_suite_number: billingObject.billingAptSte,
            city: billingObject.billingCity,
            state: billingObject.billingState,
            phone: billingObject.billingPhoneNumber,
            shippingAddressId: shippingObject.shippingAddressId,
            billingAddressId: billingObject.billingAddressId,
            coupon_id: couponId,
            discount: discount,
            payment_method: paymentMethod
        }

        return orderPayLoad;
    }


    const makePaymentButton = (paymentOption, parent, className, idName, newIcon, newText) => {
        let paymentButton = document.createElement('button')

        if (paymentOption === 'paypal' || paymentOption === 'google_pay' || paymentOption === 'apple_pay') {
            document.getElementById(idName).style.display = 'block';
            if (paymentOption == 'paypal') {
                payPalPayProcess()
            }
            if (paymentOption === 'google_pay') {
                stripeGooglePayProcess()
            }
            if (paymentOption === 'apple_pay') {
                stripeApplePayProcess(paymentButton)

            }
        }


        if (paymentOption == 'venmo') {
            paymentButton.id = idName;
            paymentButton.classList.add(className)

            const icon = newIcon.cloneNode(true)
            paymentButton.appendChild(icon)

            const text = newText.cloneNode(true);
            paymentButton.appendChild(text)

            parent.appendChild(paymentButton)
            venmoPayProcess(paymentButton)
        }

        if (paymentOption == 'credit_card') {
            paymentButton.id = idName;
            paymentButton.classList.add(className)

            const icon = newIcon.cloneNode(true)
            paymentButton.appendChild(icon)

            const text = newText.cloneNode(true);
            paymentButton.appendChild(text)

            parent.appendChild(paymentButton)
            let windowCard = createCreditCardElement(stripe)
            stripePaymentProcessCreditCard(paymentButton, windowCard)

        }

        if (paymentOption === 'stable_coin') {

            paymentButton.id = idName;
            paymentButton.classList.add(className)

            const icon = newIcon.cloneNode(true)
            paymentButton.appendChild(icon)

            const text = newText.cloneNode(true);
            paymentButton.appendChild(text)

            parent.appendChild(paymentButton)
            initiateCryptoPayment(paymentButton)
            // nowPaymentsProcess()



        }


    }







    //////////////////////////////////////////////////////////////
    ///////////////////// PAYPAL PAYMENTS ////////////////////////
    //////////////////////////////////////////////////////////////

    const payPalPayProcess = () => {
        let amount = getFinalAmount();
        console.log('amount Paypal', amount)
        let billingObject = getBillingAddressInfo();
        let shippingObject = getShippingAddressInfo();
        let userId = document.getElementById('userData').value

        paypal.Buttons({
            createOrder: function (data, actions) {
                // Get the amount dynamically from your app if needed

                return actions.order.create({
                    purchase_units: [{
                        amount: {
                            value: (amount / 100).toFixed(2) // Must be a string, e.g., "19.99"
                        },
                        payee: {
                            email_address: billingObject.billingEmail,
                        },
                    }]
                });
            },


            onApprove: function (data, actions) {
                return actions.order.capture().then(function (details) {

                    // ✅ Now send order info to your backend to create the order
                    let orderPayLoad = createOrderPayLoad(userId, data.orderID, data.payerID, amount, shippingObject, billingObject, "", 0, 'paypal')

                    fetch('/orders/create-after-payment/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify(orderPayLoad)
                    })
                        .then(res => res.json())
                        .then(data => {
                            if (data.success) {
                                window.location.replace('/payment/placed-order/');
                            } else {
                                alert('Order creation failed after PayPal payment.');
                            }
                        });
                });
            },
            onError: function (err) {
                console.error('PayPal error', err);
                alert('Something went wrong with PayPal payment.');
            }
        }).render('#paypal-button-container');
    }

    //////////////////////////////////////////////////////////////
    //////////////////// END Of PAYPAL PAYMENTS //////////////////
    //////////////////////////////////////////////////////////////



    //////////////////////////////////////////////////////////////
    /////////////////////// VENMO PAYMENTS ///////////////////////
    //////////////////////////////////////////////////////////////

    /// Initiate Venmo Payment Process
    const venmoPayProcess = (paymentButton) => {
        console.log('venmoPayProcess has been called')
        let venmoInstance = null;
        let isInitialized = false;
        let isProcessing = false;

        initializeVenmoPayment()

        paymentButton.addEventListener('click', () => {
            if (!isInitialized) {
                showMessage('Initializing Venmo, please wait...', 'loading');
                return;
            }

            if (isProcessing) {
                showMessage('Payment already in progress...', 'payment pending');
                return;
            }

            handleVenmoPayment();

        });

        async function initializeVenmoPayment() {

            if (isInitialized) {
                showMessage('Venmo already initialize');
                return;
            }

            try {
                // Create Braintree client
                const clientInstance = await braintree.client.create({
                    authorization: CLIENT_TOKEN
                });

                // Check if Venmo is available
                venmoInstance = await braintree.venmo.create({
                    client: clientInstance,
                    allowNewBrowserTab: false // Keeps the payment flow in the same tab
                });


                if (!venmoInstance.isBrowserSupported()) {
                    showMessage('Venmo is not supported on this device. Please use a mobile device with the Venmo app installed.', 'error');
                    return;
                }

                isInitialized = true;

                // Update button text to show it's ready
                const buttonText = paymentButton.querySelector('.button-text');
                if (buttonText) {
                    buttonText.textContent = 'Pay with Venmo';
                }


                // Create Venmo button
                // handleVenmoPayment(venmoInstance)

            } catch (error) {
                console.error('Error initializing Venmo:', error);
                showMessage('Error initializing Venmo payment. Please try again.', 'error');
                paymentButton.disabled = true;
            }
        }


        let billingObject = getBillingAddressInfo();
        let shippingObject = getShippingAddressInfo();
        let userId = document.getElementById('userData').value


        async function handleVenmoPayment() {
            if (!venmoInstance || !isInitialized) {
                console.error('Venmo not initialized');
                showMessage('Venmo not read. Please refresh the page', 'error');
                return
            }

            if (isProcessing) {
                console.log('Payment already in progress');
                return;
            }

            isProcessing = true;

            try {
                showMessage('Redirecting to Venmo...', 'loading');

                paymentButton.disabled = true;

                // Tokenize with Venmo
                const payload = await venmoInstance.tokenize();


                // Get amount
                const amount = getFinalAmount();
                console.log('amount Venmo', amount)

                // create paymentPayload to get a transaction id for venmoe
                let paymentPayload = {
                    payment_method_nonce: payload.nonce,
                    amount: amount,
                    user_id: userId,
                    shipping_address_id: shippingObject.shippingAddressId,
                    billing_address_id: billingObject.billingAddressId
                }

                // First Process the payment
                const paymentResponse = await fetch('/payment/process-venmo/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify(paymentPayload)
                })

                const paymentResult = await paymentResponse.json();

                let orderPayLoad = createOrderPayLoad(userId, paymentResult.transaction_id, paymentResult.transaction_id, amount, shippingObject, billingObject, "", 0, 'venmo');


                // Send to Django backend
                const response = await fetch('/orders/create-after-payment/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify(orderPayLoad)
                });


                const result = await response.json();

                console.log('result', result)

                if (result.success) {
                    showMessage(`Payment successful! Transaction ID: ${result.transaction_id || 'N/A'}`, 'success');
                    setTimeout(() => {
                        window.location.href = '/payment/placed-order/';
                    }, 1500);
                } else {
                    showMessage(`Payment failed: ${result.error || 'Unknown error'}`, 'error');
                    paymentButton.disabled = false;
                    isProcessing = false;
                }

            } catch (error) {
                console.error('Venmo payment error:', error);

                // Re-enable buttons on error
                paymentButton.disabled = false;
                isProcessing = false;

                if (error.code === 'VENMO_CANCELED') {
                    showMessage('Payment was canceled.', error);
                } else if (error.code === 'VENMO_APP_CANCELED') {
                    showMessage('Payment was canceled in the Venmo app.', error);
                } else {
                    showMessage('Payment failed. Please try again.', error);
                }
            }
        }

    }


    //////////////////////////////////////////////////////////////
    //////////////////// END OF VENMO PAYMENTS ///////////////////
    //////////////////////////////////////////////////////////////




    //////////////////////////////////////////////////////////////
    ///////////// STRIPE CREDIT CARD PAYMENTS ////////////////////
    //////////////////////////////////////////////////////////////


    // MOUNTS STRIPE PAYMENT ELEMENT FOR CREDIT CARDS
    const createCreditCardElement = (stripe) => {
        // Mount Stripe card element only once
        if (!window.cardElementMounted) {
            const elements = stripe.elements();
            const style = {
                base: {

                    color: "#CB3A60",
                    lineHeight: '2.4',
                    fontSize: '12px',
                    border: '2px solid red',
                    fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
                    '::placeholder': {
                        color: '#cb3a60',
                    },
                },
                invalid: {
                    color: '#ff1744',
                    iconColor: '#ff1744'
                }
            };
            window.card = elements.create('card', { style: style });
            card.mount("#card-element");

            card.on('change', function (event) {
                const displayError = document.getElementById('card-errors');
                if (event.error) {
                    displayError.textContent = event.error.message;
                    $('#card-errors').addClass('alert alert-info')
                } else {
                    displayError.textContent = '';
                    $('#card-errors').removeClass('alert alert-info')
                }
            });
            window.cardElementMounted = true;
            return window.card
        }

        console.log('Stripe pay elements created')

    }

    /// PROCESS CREDIT CARD PAYMENT
    const stripePaymentProcessCreditCard = (paymentButton, windowCard) => {

        if (paymentButton) {
            paymentButton.addEventListener('click', async (e) => {

                const cleanAmount = purchaseTotal.innerHTML.replace('$', '').replace(',', '')
                console.log('cleanAmount', cleanAmount)

                let amount = getFinalAmount();
                console.log('amount stripe credi card', amount)


                const { clientSecret } = await fetch('create-payment-intent/', {
                    method: "POST",
                    headers: { "Content-Type": "application/json", 'X-CSRFToken': getCsrfToken() },
                    body: JSON.stringify({ amount: amount }),
                }).then(res => res.json());

                let billingObject = getBillingAddressInfo();
                let shippingObject = getShippingAddressInfo();
                let userId = document.getElementById('userData').value


                try {

                    // Call to confirm pay
                    const result = await stripe.confirmCardPayment(clientSecret, {
                        payment_method: {
                            card: windowCard,
                            billing_details: {
                                address: {
                                    line1: billingObject.billingAddressLine,
                                    line2: billingObject.billingAddressLine2,
                                    city: billingObject.billingCity,
                                    state: billingObject.billingState,
                                    postal_code: billingObject.billingPostCode

                                },
                                name: billingObject.billingCustName,
                                email: billingObject.billingEmail
                            }
                        }
                    });

                    let orderPayLoad = createOrderPayLoad(userId, result.paymentIntent.id, clientSecret, amount, shippingObject, billingObject, "", 0, 'stripe')

                    if (result.error) {
                        console.log('Payment Failed:', result.error.message);
                        alert(result.error.message)
                    } else if (result.paymentIntent && result.paymentIntent.status == 'succeeded') {
                        fetch('/orders/create-after-payment/', {
                            method: "POST",
                            headers: { 'Content-Type': 'application/json', },
                            body: JSON.stringify(orderPayLoad)
                        })
                            .then(res => res.json())
                            .then(data => {
                                if (data.success) {
                                    window.location.replace('/payment/placed-order/');
                                } else {
                                    alert('Order creation failed.')
                                }
                            });
                    }
                } catch (err) {
                    console.error('Unexpected error', err)
                    alert("An unexpected error occured. Please refresh and try again")
                }

            })
        }

    }
    //////////////////////////////////////////////////////////////
    ////////////// END OF STRIPE CREDIT CARD PAYMENTS ////////////
    //////////////////////////////////////////////////////////////



    //////////////////////////////////////////////////////////////
    ///////////// STRIPE GOOGLE PAY PAYMENTS ////////////////////
    //////////////////////////////////////////////////////////////


    const stripeGooglePayProcess = () => {
        console.log('googlePayProcess has been called')

        initializeGooglePayPayment()


        async function initializeGooglePayPayment() {

            try {
                const buttonContainer = document.getElementById('google-pay-button');
                if (!buttonContainer) {
                    console.error('Google Pay Button Container Not Found.');
                    showMessage('Google Pay Button Container Not Found.', 'error');
                    return;
                }
                showMessage('Checking Google Pay Availability...', 'info');

                // prevent multiple initializations;
                if (window.applePayButtonMounted) {
                    showMessage('Google Pay is Ready', 'success');
                    return;
                }

                const elements = stripe.elements();
                const amount = getFinalAmount();
                console.log('amount google pay', amount)

                const paymentRequest = stripe.paymentRequest({
                    country: 'US',
                    currency: 'usd',
                    total: {
                        label: 'The Pop Up',
                        amount: amount
                    },
                    requestPayerName: true,
                    requestPaymerEmail: true

                });

                // Check Google Pay Availability
                const canMakePayment = await paymentRequest.canMakePayment();

                if (!canMakePayment) {
                    showMessage('Google Pay is Not Available on This Device or Browser', 'error');
                    document.getElementById('google-pay-button').style.display = 'none';
                }

                // Google Pay is available, create and mount buttons;
                const prButton = elements.create('paymentRequestButton', {
                    paymentRequest,
                    style: {
                        paymentRequestButton: {
                            type: 'default',
                            theme: 'dark',
                            height: '45px'
                        },
                    },
                })

                // Mount the button
                if (prButton) {
                    prButton.mount("#google-pay-button")
                    showMessage("Google Pay is Ready", 'success')
                }

                // Set up payment event handler
                paymentRequest.on('paymentmethod', handleGooglePayPayment);


            } catch (error) {
                console.log('Google Pay initialization error ', error);
                showMessage('Failed to initialize Google Pay: ' + error.message, 'error');
                document.getElementById('google-pay-button').style.display = 'none';
            }
        };

        const handleGooglePayPayment = async (ev) => {
            try {
                showMessage('Processing Google Pay Payment...', 'info');
                const amount = getFinalAmount();

                // create payment intent
                const { clientSecret } = await fetch('create-payment-intent/', {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ amount: amount }),
                }).then(res => res.json());

                console.log('clientSecret', clientSecret)

                // Confirm the payment
                const { error, paymentIntent } = await stripe.confirmCardPayment(
                    clientSecret,
                    { payment_method: ev.paymentMethod.id },
                    { handleActions: false }
                );

                if (error) {
                    ev.complete('fail')
                    console.error('Google Pay Payment Error:', error.message);
                    showMessage('Payment Failed ' + error.message, 'error');
                    return;
                }
                ev.complete('success');
                showMessage('Payment Successful! Creating Your Order...', 'success');

                // Finalize the payment (Manage 3D Secure if Necessary)
                const confirmed = await stripe.confirmCardPayment(clientSecret);
                console.log('confirmed', confirmed)

                if (confirmed.paymentIntent.status !== 'succeeded') {
                    showMessage('Payment Confirmation Failed', 'error');
                    return;
                }

                await createOrderAfterGooglePayment(confirmed.paymentIntent.id, amount, clientSecret);



            } catch (error) {
                ev.complete('fail');
                console.error("Google Pay Processing Error", error);
                showMessage('Payment Processing Failed: ' + error.message, 'error');

            }
        }

        const createOrderAfterGooglePayment = async (paymentIntentId, amount, clientSecret) => {
            try {
                const billingObject = getBillingAddressInfo();
                const shippingObject = getShippingAddressInfo();
                const userId = document.getElementById('userData').value;

                const orderPayLoad = createOrderPayLoad(userId, paymentIntentId, clientSecret, amount, shippingObject, billingObject, "", 0, 'google_pay');

                const response = await fetch('/orders/create-after-payment/', {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken()
                    },
                    body: JSON.stringify(orderPayLoad)
                });


                const data = await response.json();

                console.log('Order creation response for Google Pay:', data);

                if (data.success) {
                    showMessage('Order created successfully! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.replace('/payment/placed-order/');
                    }, 1000);
                } else {
                    showMessage('Order creation failed after successful payment', 'error');
                }

            } catch (error) {
                console.error('Order creation error:', error);
                showMessage('Failed to create order: ' + error.message, 'error');

            }
        }

    }

    //////////////////////////////////////////////////////////////
    ////////////// END OF STRIPE GOOGLE PAY PAYMENTS /////////////
    //////////////////////////////////////////////////////////////


    //////////////////////////////////////////////////////////////
    /////////////// STRIPE APPLE PAY PAYMENTS ////////////////////
    //////////////////////////////////////////////////////////////

    /// * * *  APPLE PAY CODE, WORKS BUT THERE ARE OTHER REQUIREMENTS * * * ///
    /// NEED APPLE PAY DOMAIN AND OTHER THINGS TO IMPLEMENT APPLE PAY * * * ///


    const stripeApplePayProcess = (paymentButton) => {
        console.log('appleyPayProces has been called')


        initializeApplePayPayment()

        paymentButton.addEventListener('click', () => {
            if (!isInitialized) {
                console.log('Apple Pay not yet initialized, please wait...');
                showMessage('Initializing Apple Pay, please wait...', 'loading');
                return;
            }

            if (isProcessing) {
                console.log('Payment already in progress');
                showMessage('Payment already in progress', 'payment pending');
                return;
            }

            handleApplePayPayment();
        });

        async function initializeApplePayPayment() {
            console.log('inializeApplePayPayment has been called')

            try {
                showMessage('Checking Apple Pay availability...', 'info');

                // Check if DOM element exists
                const buttonContainer = document.getElementById('apple-pay-button');
                if (!buttonContainer) {
                    console.error('Apple Pay Button Container Not Found.');
                    showMessage('Apple Pay Button Container Not Found.', 'error');
                    return;
                }

                // prevent multiple intializations;
                if (window.applePayButtonMounted) {
                    showMessage('Apple Pay is Ready', 'success');
                    return;
                }

                const elements = stripe.elements()
                const amount = getFinalAmount()
                console.log('amount apple pay', amount)

                const paymentRequest = stripe.paymentRequest({
                    country: 'US',
                    currency: 'usd',
                    total: {
                        label: 'The Pop Up',
                        amount: amount
                    },
                    requestPayerName: true,
                    requestPaymerEmail: true
                });

                const canMakePayment = await paymentRequest.canMakePayment();

                if (!canMakePayment) {
                    showMessage('Apple Pay is Not Available on This Device or Browser', 'error');
                    document.getElementById('apple-pay-button').style.display = 'none';
                }

                // Apple Pay is available, create and mount button;

                const prButton = elements.create('paymentRequestButton', {
                    paymentRequest,
                    style: {
                        paymentRequestButton: {
                            type: 'default',
                            theme: 'dark',
                            height: '45px'
                        },
                    },
                });


                // Mount the button
                if (prButton) {
                    prButton.mount("#apple-pay-button")
                    showMessage("Apple Pay is ready", 'success')
                }



                // Set up payment event handler
                paymentRequest.on('paymentmethod', handleApplePayPayment);


            } catch (error) {
                console.log('Apple Pay initialization error ', error);
                showMessage('Failed to initialize Apple Pay: ' + error.message, 'error');
                document.getElementById('apple-pay-button').style.display = 'none';

            }
        };

        const handleApplePayPayment = async (ev) => {
            try {
                showMessage('Processing Apple Pay Payment...', 'info');

                const amount = getFinalAmount();
                // create payment intent
                const { clientSecret } = await fetch('create-payment-intent/', {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ amount: amount }),
                }).then(res => res.json());

                // Confirm the Payment
                const { error, paymentIntent } = await stripe.confirmCardPayment(
                    clientSecret,
                    { payment_method: ev.paymentMethod.id },
                    { handleActions: false }
                );

                if (error) {
                    ev.complete('fail')
                    console.error('Apple Pay Payment Error:', error.message);
                    showMessage('Payment Failed ' + error.message, 'error');
                    return;
                }
                ev.complete('success');
                showMessage('Payment Successful! Creating Your Order...', 'success');

                const confirmed = await stripe.confirmCardPayment(clientSecret);

                if (confirmed.paymentIntent.status !== 'succeeded') {
                    showMessage('Payment Confirmation Failed', 'error');
                    return;
                }

                await createOrderAfterApplePayment(confirmed.paymentIntent.id, amount);

            } catch (error) {
                ev.complete('fail');
                console.error("Apple Pay Processing Error", error);
                showMessage('Payment Processing Failed: ' + error.message, 'error');

            }
        };

        const createOrderAfterApplePayment = async (paymentIntentId, amount) => {
            try {
                const billingObject = getBillingAddressInfo();
                const shippingObject = getShippingAddressInfo();
                const userId = document.getElementById('userData').value;

                const orderPayLoad = createOrderPayLoad(userId, paymentIntentId, clientSecret, amount, shippingObject, billingObject, "", 0, 'apple_pay');

                const response = await fetch('/orders/create-after-payment/', {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken()
                    },
                    body: JSON.stringify(orderPayLoad)
                });

                const data = await response.json();
                console.log('Order creation response for Apple Pay:', data);

                if (data.success) {
                    showMessage('Order created successfully! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.replace('/payment/placed-order/');
                    }, 1000);
                } else {
                    showMessage('Order creation failed after successful payment', 'error');
                }

            } catch (error) {
                console.error('Order creation error:', error);
                showMessage('Failed to create order: ' + error.message, 'error');

            }
        }
    }


    //////////////////////////////////////////////////////////////
    //////////////// END OF STRIPE APPLE PAY PAYMENTS ////////////
    //////////////////////////////////////////////////////////////



    //////////////////////////////////////////////////////////////
    //////////////// NOWPAYMENTS STABLECOIN PAYMENTS ////////////
    //////////////////////////////////////////////////////////////

    const initiateCryptoPayment = (paymentButton) => {
        paymentButton.addEventListener('click', () => {
            nowPaymentsProcess()
        })

    }
    const nowPaymentsProcess = () => {
        console.log('nowPaymentsProcess called')

        let amount = getFinalAmount()
        let billingObject = getBillingAddressInfo();
        let shippingObject = getShippingAddressInfo();
        let userId = document.getElementById('userData').value;

        // show loading state
        showPaymentLoading();

        const paymentData = {
            price_amount: (amount / 100).toFixed(2),
            price_currency: 'USD',
            pay_currency: '', // Will be selected by the user (DAI or USDC)
            order_id: generateOrderId(), // Generate unique order ID,
            order_description: `Order for ${userId}`,
            success_url: window.location.origin + '/payment/success',
            cancel_url: window.location.origin + '/checkout/',
            billing_address: billingObject.billingAddressLine,
            shipping_address: shippingObject.shippingAddressLine,
            user_id: userId
        }

        // Call Django backend to create NowPayment payment
        fetch('create-nowpayments/', {
            method: 'POST',
            headers: {
                'content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(paymentData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show currency selection modal
                    showCurrencySelectionModal(data.payment_data, paymentData);
                } else {
                    throw new Error(data.error || 'Payment creation failed');
                }
            })
            .catch(error => {
                console.error('NowPayments error:', error);
                hidePaymentLoading();
                showPaymentError('Failed to intialize crypto payment, please try and again.');
            })
    };

    const showCurrencySelectionModal = (paymentData, originalData) => {
        console.log('showCurrencySelectionModal called')

        const modal = document.createElement('div');
        modal.className = 'crypto-currency-modal';
        modal.innerHTML = `
            <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Select Cryptocurrency</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Choose your preferred stablecoin for payment:</p>
                    <div class="currency-options">
                        <button class="currency-option" data-currency="dai">
                            <img src="/static/img/dia-logo.png" alt="DAI" class="currency-logo">
                            <span>DAI</span>
                        </button>
                        <button class="currency-option" data-currency="usdc">
                            <img src="/static/img/usdc-logo.png" alt="USDC" class="currency-logo">
                            <span>USDC</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;

        document.body.appendChild(modal);

        // Handle currency selection
        modal.querySelectorAll('.currency-option').forEach(button => {
            button.addEventListener('click', (e) => {
                const selectedCurrency = e.currentTarget.dataset.currency;
                modal.remove();
                initiateNowPayment(selectedCurrency, originalData);
            });
        });

        // Handle Modal Close
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
            hidePaymentLoading();
        });
    };

    // Initiate Payment with Selected Currency
    const initiateNowPayment = (currency, paymentData) => {
        console.log('initiateNowPayment called')

        paymentData.pay_currency = currency.toUpperCase();
        console.log('paymentData.pay_currency', paymentData.pay_currency)

        fetch('finalize-nowpayments/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(paymentData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show payment details modal
                    showPaymentDetailsModal(data.payment_info);
                } else {
                    throw new Error(data.error || 'Payment finalization failed');
                }
            })
            .catch(error => {
                console.error('Payment finalization error', error);
                hidePaymentLoading();
                showPaymentError('Failed to finalize crypto payment. Please try again');
            });
    };

    // Show payment details and QR code
    const showPaymentDetailsModal = (paymentInfo) => {
        console.log('showPaymentDetailsModal called')

        const modal = document.createElement('div');
        modal.className = 'payment-details-modal';
        modal.innerHTML = `
        <div class="modal-overlay">
            <div class="modal-content payment-modal">
                <div class="modal-header">
                    <h3>Complete Your ${paymentInfo.pay_currency} Payment</h3>
                    <div class="payment-status" id="paymentStatus">
                        <span class="status-pending">⏳ Waiting for payment...</span>
                    </div>
                </div>
                <div class="modal-body">
                    <div class="payment-info">
                        <div class="payment-amount">
                            <h4>${paymentInfo.pay_amount} ${paymentInfo.pay_currency}</h4>
                            <p>≈ $${paymentInfo.price_amount} USD</p>
                        </div>
                        
                        <div class="payment-address">
                            <label>Send to this address:</label>
                            <div class="address-container">
                                <input type="text" value="${paymentInfo.pay_address}" readonly class="payment-address-input">
                                <button class="copy-btn" onclick="copyToClipboard('${paymentInfo.pay_address}')">Copy</button>
                            </div>
                        </div>

                        <div class="qr-code-container">
                            <div id="qrcode"></div>
                        </div>

                        <div class="payment-timer">
                            <p>Time remaining: <span id="countdown">${paymentInfo.time_limit || '15:00'}</span></p>
                        </div>

                        <div class="payment-instructions">
                            <h5>Instructions:</h5>
                            <ol>
                                <li>Copy the address above or scan the QR code</li>
                                <li>Send exactly <strong>${paymentInfo.pay_amount} ${paymentInfo.pay_currency}</strong></li>
                                <li>Wait for confirmation (usually 1-3 minutes)</li>
                            </ol>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" id="cancelPaymentBtn">Cancel Payment</button>
                    <button class="btn-primary"  id="checkPaymentStatusBtn">Check Status</button>
                </div>
            </div>
        </div>
        `;
        document.body.appendChild(modal);
        hidePaymentLoading();

        // Attach Event Handler
        document.getElementById('cancelPaymentBtn').addEventListener('click', () => {
            cancelPayment(paymentInfo.payment_id)
        })

        document.getElementById('checkPaymentStatusBtn').addEventListener('click', () => {
            checkPaymentStatus(paymentInfo.payment_id)
        })

        // Generate QR Code
        generateQRCode(paymentInfo.pay_address, paymentInfo.pay_amount, paymentInfo.pay_currency);

        // Start payment monitoring
        startPaymentMonitoring(paymentInfo.payment_id);

        // Start countdown timer
        if (paymentInfo.time_limit) {
            startCountdownTimer(paymentInfo.time_limit);
        }
    };


    // Generate QR Code for payment
    const generateQRCode = (address, amount, currency) => {
        console.log('generateQRCode called')
        // Using qrcode.js library (this needs to be included)
        const qrData = `${currency.toLowerCase()}:${address}?amount=${amount}`;
        const qr = qrcode(0, 'M');
        qr.addData(qrData);
        qr.make();
        document.getElementById('qrcode').innerHTML = qr.createImgTag(4)
    };

    // Monitor Payment Status
    const startPaymentMonitoring = (paymentId) => {
        console.log('startPaymentMonitoring called')
        const checkInterval = setInterval(() => {
            fetch(`check-nowpayments-status/${paymentId}/`, {
                method: "GET",
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            })
                .then(response => response.json())
                .then(data => {
                    console.log('data', data)
                    updatePaymentStatus(data.status, data.payment_info);

                    if (data.status === 'finished' || data.status === 'confirmed') {
                        clearInterval(checkInterval);
                        handlePaymentSuccess(data.payment_info);
                    } else if (data.status === 'failed' || data.status === 'expired') {
                        clearInterval(checkInterval);
                        handlePaymentFailure(data.payment_info);

                    }

                })
                .catch(error => {
                    console.error('Status check error', error);
                });
        }, 10000); // check every 10 seconds

        // Store internal ID for cleanup
        window.paymentCheckInterval = checkInterval;
    };

    // Update payment status display
    const updatePaymentStatus = (status, paymentInfo) => {
        console.log('updatePaymentStatus called')
        const statusElement = document.getElementById('paymentStatus');
        if (!statusElement) return;

        const statusMap = {
            'waiting': '⏳ Waiting for payment...',
            'confirming': '🔄 Confirming transaction...',
            'confirmed': '✅ Payment confirmed!',
            'finished': '✅ Payment completed!',
            'failed': '❌ Payment failed',
            'expired': '⏰ Payment expired'
        };

        statusElement.innerHTML = `<span class="status-${status}">${statusMap[status] || status}</span>`;
    }

    // Handle Successful Payment
    const handlePaymentSuccess = (paymentInfo) => {
        console.log('handlePaymentSuccess called')
        // Create order in your system
        let userId = document.getElementById('userData').value;
        let amount = getFinalAmount();
        let billingObject = getBillingAddressInfo();
        let shippingObject = getShippingAddressInfo();

        let orderPayLoad = createOrderPayLoad(userId, paymentInfo.payment_id, paymentInfo.payment_id, amount, shippingObject, billingObject, "", 0, 'now_payment');

        fetch('/orders/create-after-payment/', {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify(orderPayLoad)
        })
            .then(response => response.json)
            .then(data => {
                if (data.success) {
                    // Clean up and redirect
                    document.querySelector('.payment-details-modal').remove()
                    window.location.replace('/payment/placed-order/');
                } else {
                    shwoPaymentError('Order creation failed after successful payment')
                }
            });
    };

    // Handle Payment Failure
    const handlePaymentFailure = (paymentInfo) => {
        console.log('handlePaymentFailure called')
        showPaymentError("Payment failed or expired. Please try again");
        document.querySelector(".payment-details-modal").remove();
    };

    // Utility function
    const copyToClipboard = (text) => {
        console.log('copyToClipboard called')

        navigator.clipboard.writeText(text).then(() => {
            // Show copied feedback
            const copyBtn = event.target;
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied';
            setTimeout(() => {
                copyBtn.textContent = originalText;
            }, 2000);
        })
    }

    const cancelPayment = (paymentId) => {
        console.log('cancelPayment called')

        // Clear countdown timer
        if (countdownTimer) {
            clearInterval(countdownTimer);
            countdownTimer = null;
        }

        // Remove the modal
        const modal = document.querySelector('.payment-details-modal');
        if (modal) {
            modal.remove();
        }

        if (confirm("Are you sure you want to cancel this payment?")) {
            // Clean up
            if (window.paymentCheckInterval) {
                clearInterval(window.paymentCheckInterval)
            }
            document.querySelector(".payment-details-modal").remove();
        }
    }

    const checkPaymentStatus = (paymentId) => {
        console.log('checkPaymentStatus called')

        // Manual status check
        fetch(`check-nowpayments-status/${paymentId}/`, {
            method: "GET",
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
            .then(response => response.json)
            .then(data => {
                updatePaymentStatus(data.status, data.payment_info);
                if (data.status === 'finished' || data.status === 'confirmed') {
                    handlePaymentSuccess(data.payment_info);
                }
            });
    };

    let countdownTimer = null;

    const startCountdownTimer = (timeLimit) => {
        console.log('startCountdownTimer called', timeLimit)

        // Clear any existing timer first
        if (countdownTimer) {
            clearInterval(countdownTimer)
        }

        const [minutes, seconds] = timeLimit.split(':').map(Number);
        let totalSeconds = minutes * 60 + seconds;

        countdownTimer = setInterval(() => {
            // Check if the countdown element still exists
            const countdownElement = document.getElementById('countdown');
            if (!countdownElement) {
                clearInterval(countdownElement);
                countdownTimer = null;
                return;
            }

            const mins = Math.floor(totalSeconds / 60);
            const secs = totalSeconds % 60;
            countdownElement.textContent = document.getElementById('countdown').textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

            // document.getElementById('countdown').textContent = `${mins.toString().padStart(2, 0)}:${secs.toString().padStart(2, 0)}`;

            if (totalSeconds <= 0) {
                clearInterval(countdownTimer);
                countdownTimer = null;
                handlePaymentFailure({ reason: 'expired' });
            }
            totalSeconds--;
        }, 1000)
    }

    const generateOrderId = () => {
        console.log('generateOrderId called')
        return 'ORDER_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9)
    }

    const showPaymentLoading = () => {
        console.log('showPaymentLoading called')
        // Add loading state to payment button
        const paymentContainer = document.querySelector(".purchase_details_confirm_pay");
        paymentContainer.innerHTML += `<div class="payment-loading">Processing Payment...</div>`;
    };

    const hidePaymentLoading = () => {
        console.log('hidePaymentLoading called')
        const loadingElement = document.querySelector('.payment-loading');
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    const showPaymentError = (message) => {
        console.log('showPaymentError called')
        const errorDiv = document.createElement('div');
        errorDiv.className = 'payment-error';
        errorDiv.textContent = message;
        document.querySelector('.purchase_details_confirm_pay').appendChild(errorDiv);

        setTimeout(() => {
            errorDiv.remove();
        }, 5000)
    }

    // Add event listener for stablecoin payment option
    /// Modify your existing payment option selection logic
    document.addEventListener('DOMContentLoaded', function () {

        let stablecoinButton;
        if (document.getElementById('stable-coin-payment')) {
            stablecoinButton = document.getElementById('stable-coin-payment');
        }
        console.log('stableCoinButton', stablecoinButton)
        // stablecoinButton.style.display = 'block'

        if (stablecoinButton) {
            console.log('yes stableCoinbutton')
            stablecoinButton.addEventListener('click', function () {
                console.log('stable_coin button clicked for payment!')
                // Your existing logic to update the selected payment method
                document.getElementById('selectedPaymentMethod').value = 'stable_coin';
                document.getElementById('selectedPaymentButton').innerHTML = `
                        <span class="payBtnIcon">
                            <img src="{% static 'img/stableCoins.png' %}" class='stable-coin-logo' />
                        </span>
                `;

                // Set up the final payment button for stablecoins
                setupStablecoinPayment();
            })
        }
    })



    const setupStablecoinPayment = () => {
        console.log('setupStablecoinPayment called')
        // Create the final payment button for stablecoins
        const confirmPayDiv = document.querySelector('.purchase_details_confirm_pay');

        // Remove existing payment buttons
        const existingButtons = confirmPayDiv.querySelectorAll('.payment_option_buttons_two');
        existingButtons.forEach(btn => btn.remove());

        // Add stablecoin payment button
        const stablecoinPayButton = document.createElement('button');
        stablecoinPayButton.className = 'payment_option_buttons_two';
        stablecoinPayButton.innerHTML = `
            <span class="payBtnIcon">
                <img src="{% static 'img/stableCoins.png' %}" class='stable-coin-logo' />
            </span>
        <span class="payBtnText">Pay with Crypto</span>
    `;

        stablecoinPayButton.addEventListener('click', nowPaymentsProcess);
        confirmPayDiv.appendChild(stablecoinPayButton);
    };



    //////////////////////////////////////////////////////////////
    //////////// END OF NOWPAYMENTS STABLECOIN PAYMENTS //////////
    //////////////////////////////////////////////////////////////





    /*
     * buttonUnMount()
     * Returns: N/A
     * Function: Removes/resets the payment button.
     * When somthing in checkout changes that effects the total price,
     * the payment button needs to be unmounted, so that the total price
     * can be recalculated.
     */
    const buttonUnMount = () => {
        const stripeIds = ['google-pay-button', 'apple-pay-button', 'confirm-card-payment',
            'paypal-button-container', 'venmo-button-container']

        for (let i = 0; i < stripeIds.length; i++) {
            const currentId = stripeIds[i];
            let elementToUnMount = document.getElementById(currentId);

            if (elementToUnMount) {
                // For Venmo Specifically
                if (currentId === 'venmo-button-container') {

                    // Save Parement Element
                    const parentElement = elementToUnMount.parentNode;

                    // Delete the element (wether div or button)
                    elementToUnMount.remove();

                    // Recreate the original div
                    const newDiv = document.createElement('div');
                    newDiv.id = 'venmo-button-container';
                    newDiv.style.display = 'none';

                    // Put the div back in the DOM
                    parentElement.appendChild(newDiv);

                } else {
                    // For the other elements
                    elementToUnMount.innerHTML = '';
                    elementToUnMount.style.display = 'none';
                }
            }
        }

        if (messagesDiv) {
            messagesDiv.innerHTML = "";
        }

        if (subtotalExpand && purchaseDetailsContainer) {
            const isOpen = subtotalExpand.classList.contains('subTotalactive') &&
                purchaseDetailsContainer.classList.contains('subTotalShow');

            if (isOpen) {
                subtotalExpand.classList.remove('subTotalactive');
                purchaseDetailsContainer.classList.remove('subTotalShow');
            }
        }

        // Réinitialiser tous les flags
        window.applePayButtonMounted = false;
        window.googlePayButtonMounted = false;
        window.venmoButtonMounted = false;
    }


    function showMessage(message, type) {
        console.log('showMessage called', message)
        messagesDiv.innerHTML = `<div class="${type}">${message}</div>`;

        // Clear loading messages after 3 seconds
        if (type === 'loading') {
            setTimeout(() => {
                if (messagesDiv.querySelector('.loading')) {
                    messagesDiv.innerHTML = '';
                }
            }, 3000);
        }
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

});


