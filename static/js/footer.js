// help center buying options dropdown
var buyingBoxExpand = document.getElementById("help_center_buying");
var sellingBoxExpand = document.getElementById("help_center_selling");
var accountBoxExpand = document.getElementById("help_center_accounts");

var shippingBoxExpand = document.getElementById('help_center_shipping')
var paymentOptBoxExpand = document.getElementById('help_center_payments')
var feesBoxExpand = document.getElementById('help_center_fees')

var helpCenterDisplayContainer = document.querySelector('.help_center_display_container');
var helpCenterDisplayContainerBottom = document.querySelector('.help_center_display_container_bottom')

var helpCenterDetailsContainerBuy = document.querySelector('.help_center_details_container_buy');
var helpCenterDetailsContainerSell = document.querySelector('.help_center_details_container_sell');
var helpCenterDetailsContainerAccount = document.querySelector('.help_center_details_container_account');

var helpCenterDetailsContainerShipping = document.querySelector('.help_center_details_container_shipping');
var helpCenterDetailsContainerPayment = document.querySelector('.help_center_details_container_payment');
var helpCenterDetailsContainerFee = document.querySelector('.help_center_details_container_fee');


if (buyingBoxExpand) {
    buyingBoxExpand.addEventListener(("click"), () => {
        if (helpCenterDisplayContainer.classList.contains('hide')) {
            helpCenterDisplayContainer.classList.add('show')
            helpCenterDisplayContainer.classList.remove('hide')

            helpCenterDetailsContainerBuy.classList.add('show')
            helpCenterDetailsContainerBuy.classList.remove('hide')
        } else if (helpCenterDisplayContainer.classList.contains('show') && helpCenterDetailsContainerSell.classList.contains('show') || helpCenterDetailsContainerAccount.classList.contains('show')) {

            helpCenterDetailsContainerSell.classList.remove('show')
            helpCenterDetailsContainerSell.classList.add('hide')

            helpCenterDetailsContainerAccount.classList.remove('show')
            helpCenterDetailsContainerAccount.classList.add('hide')

            helpCenterDetailsContainerBuy.classList.add('show')
            helpCenterDetailsContainerBuy.classList.remove('hide')

        } else {
            if (helpCenterDisplayContainer.classList.contains('show') && helpCenterDetailsContainerBuy.classList.contains('show')) {
                helpCenterDisplayContainer.classList.remove('show')
                helpCenterDisplayContainer.classList.add('hide')
                helpCenterDetailsContainerBuy.classList.remove('show')
                helpCenterDetailsContainerBuy.classList.add('hide')

            }

        }

    });
}


sellingBoxExpand.addEventListener(("click"), () => {
    if (helpCenterDisplayContainer.classList.contains('hide')) {
        helpCenterDisplayContainer.classList.add('show')
        helpCenterDisplayContainer.classList.remove('hide')

        helpCenterDetailsContainerSell.classList.add('show')
        helpCenterDetailsContainerSell.classList.remove('hide')
    } else if (helpCenterDisplayContainer.classList.contains('show') && helpCenterDetailsContainerBuy.classList.contains('show') || helpCenterDetailsContainerAccount.classList.contains('show')) {
        helpCenterDetailsContainerBuy.classList.remove('show')
        helpCenterDetailsContainerBuy.classList.add('hide')
        helpCenterDetailsContainerAccount.classList.remove('show')
        helpCenterDetailsContainerAccount.classList.add('hide')

        helpCenterDetailsContainerSell.classList.add('show')
        helpCenterDetailsContainerSell.classList.remove('hide')
    } else {
        if (helpCenterDisplayContainer.classList.contains('show') && helpCenterDetailsContainerSell.classList.contains('show')) {
            helpCenterDisplayContainer.classList.remove('show')
            helpCenterDisplayContainer.classList.add('hide')
            helpCenterDetailsContainerSell.classList.remove('show')
            helpCenterDetailsContainerSell.classList.add('hide')

        }
    }

});

accountBoxExpand.addEventListener(("click"), () => {
    if (helpCenterDisplayContainer.classList.contains('hide')) {
        helpCenterDisplayContainer.classList.add('show')
        helpCenterDisplayContainer.classList.remove('hide')

        helpCenterDetailsContainerAccount.classList.add('show')
        helpCenterDetailsContainerAccount.classList.remove('hide')
    } else if (helpCenterDisplayContainer.classList.contains('show') && helpCenterDetailsContainerBuy.classList.contains('show') || helpCenterDetailsContainerSell.classList.contains('show')) {
        helpCenterDetailsContainerBuy.classList.remove('show')
        helpCenterDetailsContainerBuy.classList.add('hide')
        helpCenterDetailsContainerSell.classList.remove('show')
        helpCenterDetailsContainerSell.classList.add('hide')

        helpCenterDetailsContainerAccount.classList.add('show')
        helpCenterDetailsContainerAccount.classList.remove('hide')
    } else {
        if (helpCenterDisplayContainer.classList.contains('show') && helpCenterDetailsContainerAccount.classList.contains('show')) {
            helpCenterDisplayContainer.classList.remove('show')
            helpCenterDisplayContainer.classList.add('hide')
            helpCenterDetailsContainerAccount.classList.remove('show')
            helpCenterDetailsContainerAccount.classList.add('hide')

        }
    }
});


shippingBoxExpand.addEventListener(("click"), () => {
    console.log('shippingBoxExpand button!')
    if (helpCenterDisplayContainerBottom.classList.contains('hide')) {
        helpCenterDisplayContainerBottom.classList.add('show')
        helpCenterDisplayContainerBottom.classList.remove('hide')

        helpCenterDetailsContainerShipping.classList.add('show')
        helpCenterDetailsContainerShipping.classList.remove('hide')
    } else if (helpCenterDisplayContainerBottom.classList.contains('show') && helpCenterDetailsContainerPayment.classList.contains('show') || helpCenterDetailsContainerFee.classList.contains('show')) {

        helpCenterDetailsContainerPayment.classList.remove('show')
        helpCenterDetailsContainerPayment.classList.add('hide')

        helpCenterDetailsContainerFee.classList.remove('show')
        helpCenterDetailsContainerFee.classList.add('hide')

        helpCenterDetailsContainerShipping.classList.add('show')
        helpCenterDetailsContainerShipping.classList.remove('hide')

    } else {
        if (helpCenterDisplayContainerBottom.classList.contains('show') && helpCenterDetailsContainerShipping.classList.contains('show')) {
            helpCenterDisplayContainerBottom.classList.remove('show')
            helpCenterDisplayContainerBottom.classList.add('hide')
            helpCenterDetailsContainerShipping.classList.remove('show')
            helpCenterDetailsContainerShipping.classList.add('hide')
        }
    }
});


paymentOptBoxExpand.addEventListener(("click"), () => {
    if (helpCenterDisplayContainerBottom.classList.contains('hide')) {
        helpCenterDisplayContainerBottom.classList.add('show')
        helpCenterDisplayContainerBottom.classList.remove('hide')

        helpCenterDetailsContainerPayment.classList.add('show')
        helpCenterDetailsContainerPayment.classList.remove('hide')
    } else if (helpCenterDisplayContainerBottom.classList.contains('show') && helpCenterDetailsContainerShipping.classList.contains('show') || helpCenterDetailsContainerFee.classList.contains('show')) {

        helpCenterDetailsContainerShipping.classList.remove('show')
        helpCenterDetailsContainerShipping.classList.add('hide')

        helpCenterDetailsContainerFee.classList.remove('show')
        helpCenterDetailsContainerFee.classList.add('hide')

        helpCenterDetailsContainerPayment.classList.add('show')
        helpCenterDetailsContainerPayment.classList.remove('hide')

    } else {
        if (helpCenterDisplayContainerBottom.classList.contains('show') && helpCenterDetailsContainerPayment.classList.contains('show')) {
            helpCenterDisplayContainerBottom.classList.remove('show')
            helpCenterDisplayContainerBottom.classList.add('hide')
            helpCenterDetailsContainerPayment.classList.remove('show')
            helpCenterDetailsContainerPayment.classList.add('hide')
        }
    }
});


feesBoxExpand.addEventListener(("click"), () => {
    if (helpCenterDisplayContainerBottom.classList.contains('hide')) {
        helpCenterDisplayContainerBottom.classList.add('show')
        helpCenterDisplayContainerBottom.classList.remove('hide')

        helpCenterDetailsContainerFee.classList.add('show')
        helpCenterDetailsContainerFee.classList.remove('hide')
    } else if (helpCenterDisplayContainerBottom.classList.contains('show') && helpCenterDetailsContainerShipping.classList.contains('show') || helpCenterDetailsContainerPayment.classList.contains('show')) {

        helpCenterDetailsContainerShipping.classList.remove('show')
        helpCenterDetailsContainerShipping.classList.add('hide')

        helpCenterDetailsContainerPayment.classList.remove('show')
        helpCenterDetailsContainerPayment.classList.add('hide')

        helpCenterDetailsContainerFee.classList.add('show')
        helpCenterDetailsContainerFee.classList.remove('hide')

    } else {
        if (helpCenterDisplayContainerBottom.classList.contains('show') && helpCenterDetailsContainerFee.classList.contains('show')) {
            helpCenterDisplayContainerBottom.classList.remove('show')
            helpCenterDisplayContainerBottom.classList.add('hide')
            helpCenterDetailsContainerFee.classList.remove('show')
            helpCenterDetailsContainerFee.classList.add('hide')

        }

    }

});