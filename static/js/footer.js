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


// Refactored and accessible JavaScript
    // class HelpCenterAccordion {
    //     constructor() {
    //         this.topButtons = ['help_center_buying', 'help_center_selling', 'help_center_accounts'];
    //         this.bottomButtons = ['help_center_shipping', 'help_center_payments', 'help_center_fees'];
    //         this.topPanels = ['buying_display', 'selling_display', 'my_account_display'];
    //         this.bottomPanels = ['shipping_display', 'payment_opt_display', 'fees_display'];
            
    //         this.init();
    //     }

    //     init() {
    //         // Top buttons
    //         this.topButtons.forEach((buttonId) => {
    //             const button = document.getElementById(buttonId);
    //             if (button) {
    //                 button.addEventListener('click', () => this.toggleTopSection(buttonId));
    //                 button.addEventListener('keydown', (e) => this.handleKeyboard(e, buttonId));
    //             }
    //         });

    //         // Bottom buttons
    //         this.bottomButtons.forEach((buttonId) => {
    //             const button = document.getElementById(buttonId);
    //             if (button) {
    //                 button.addEventListener('click', () => this.toggleBottomSection(buttonId));
    //                 button.addEventListener('keydown', (e) => this.handleKeyboard(e, buttonId));
    //             }
    //         });
    //     }

    //     toggleTopSection(buttonId) {
    //         const button = document.getElementById(buttonId);
    //         const panelId = buttonId.replace('help_center_', '') + '_display';
    //         const panel = document.getElementById(panelId);
    //         const container = document.querySelector('.help_center_display_container');

    //         const isExpanded = button.getAttribute('aria-expanded') === 'true';

    //         if (isExpanded) {
    //             // Close
    //             this.closePanel(panel, button, container);
    //         } else {
    //             // Close other panels and open this one
    //             this.topPanels.forEach(panelId => {
    //                 const p = document.getElementById(panelId);
    //                 const btn = document.getElementById('help_center_' + panelId.replace('_display', ''));
    //                 if (p && p.classList.contains('show')) {
    //                     this.closePanel(p, btn, container);
    //                 }
    //             });
    //             this.openPanel(panel, button, container);
    //         }
    //     }

    //     toggleBottomSection(buttonId) {
    //         const button = document.getElementById(buttonId);
    //         let panelId = buttonId.replace('help_center_', '') + '_display';
            
    //         // Handle special mapping
    //         if (buttonId === 'help_center_payments') {
    //             panelId = 'payment_opt_display';
    //         }
            
    //         const panel = document.getElementById(panelId);
    //         const container = document.querySelector('.help_center_display_container_bottom');

    //         const isExpanded = button.getAttribute('aria-expanded') === 'true';

    //         if (isExpanded) {
    //             // Close
    //             this.closePanel(panel, button, container);
    //         } else {
    //             // Close other panels and open this one
    //             this.bottomPanels.forEach(panelId => {
    //                 const p = document.getElementById(panelId);
    //                 const btnId = 'help_center_' + (panelId === 'payment_opt_display' ? 'payments' : panelId.replace('_display', ''));
    //                 const btn = document.getElementById(btnId);
    //                 if (p && p.classList.contains('show')) {
    //                     this.closePanel(p, btn, container);
    //                 }
    //             });
    //             this.openPanel(panel, button, container);
    //         }
    //     }

    //     openPanel(panel, button, container) {
    //         if (container.classList.contains('hide')) {
    //             container.classList.remove('hide');
    //             container.classList.add('show');
    //         }
    //         panel.classList.remove('hide');
    //         panel.classList.add('show');
    //         button.setAttribute('aria-expanded', 'true');
            
    //         // Focus first link in panel for keyboard users
    //         const firstLink = panel.querySelector('a');
    //         if (firstLink) {
    //             firstLink.removeAttribute('tabindex');
    //             firstLink.focus();
    //         }
    //     }

    //     closePanel(panel, button, container) {
    //         panel.classList.remove('show');
    //         panel.classList.add('hide');
    //         button.setAttribute('aria-expanded', 'false');
            
    //         // Hide container if no panels are showing
    //         const anyVisible = container.querySelector('.show');
    //         if (!anyVisible) {
    //             container.classList.add('hide');
    //             container.classList.remove('show');
    //         }
            
    //         // Return focus to button
    //         button.focus();
    //     }

    //     handleKeyboard(e, buttonId) {
    //         // Space and Enter should toggle
    //         if (e.key === ' ' || e.key === 'Enter') {
    //             e.preventDefault();
    //             document.getElementById(buttonId).click();
    //         }
    //     }
    // }

    // // Initialize on DOM ready
    // document.addEventListener('DOMContentLoaded', () => {
    //     new HelpCenterAccordion();
    // });