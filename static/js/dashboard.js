// Dashboard Size Edit modal
document.addEventListener('DOMContentLoaded', function () {
    // Get the edit, button, and close span
    const dashboardEditSizeModal = document.getElementById('sizeEditModal');
    const dashboardSizeEditBtn = document.getElementById('dashboardSizeEditBtn');
    const closeSizeEditModal = document.querySelector('.closeSizeEditModal');



    if (dashboardSizeEditBtn) {
        // Show the modal when the button is clicked
        dashboardSizeEditBtn.addEventListener('click', function () {
            dashboardEditSizeModal.style.display = 'block';
        });
    } else {
        console.warn('bidButton not found in the DOM.');
    }


    // const bidButton = document.querySelectorAll('.bidButtonClass')
    // bidButton.forEach((bidBtn) => {
    //     bidBtn.addEventListener('click', function () {
    //         if (bidBtn) {
    //             // Show the modal when the button is clicked
    //             bidBtn.addEventListener('click', function () {
    //                 modal.style.display = 'block';
    //             });
    //         } else {
    //             console.warn('bidButton not found in the DOM.');
    //         }
    //     })
    // })



    if (closeSizeEditModal) {
        // Close the modal when the close span is clicked
        closeSizeEditModal.addEventListener('click', function () {
            dashboardEditSizeModal.style.display = 'none';
        });
    } else {
        console.warn('closeModal span not found in the DOM.');
    }

    // Close the modal when clicking outside of it
    if (dashboardEditSizeModal) {
        window.addEventListener('click', function (event) {
            if (event.target === dashboardEditSizeModal) {
                dashboardEditSizeModal.style.display = 'none';
            }
        });
    } else {
        console.warn('bidModal not found in the DOM.');
    }
});



// Location Edit Modal
document.addEventListener('DOMContentLoaded', function () {
    // Get edit button and close span
    const dashboardlocationEditModal = document.getElementById('locationEditModal');
    const dashboardLocationEditBtn = document.getElementById('dashboardLocationEditBtn');
    const closeLocationEditModal = document.querySelector('.closeLocationEditModal');

    if (dashboardLocationEditBtn) {
        // Show the modal when the button is clicked
        dashboardLocationEditBtn.addEventListener('click', function () {
            dashboardlocationEditModal.style.display = 'block';
        });
    } else {
        console.warn('bidButton not found in the DOM.');
    }


    if (closeLocationEditModal) {
        // Close the modal when the close span is clicked
        closeLocationEditModal.addEventListener('click', function () {
            dashboardlocationEditModal.style.display = 'none';
        });
    } else {
        console.warn('closeModal span not found in the DOM.');
    }

    // Close the modal when clicking outside of it
    if (dashboardlocationEditModal) {
        window.addEventListener('click', function (event) {
            if (event.target === dashboardlocationEditModal) {
                dashboardlocationEditModal.style.display = 'none';
            }
        });
    } else {
        console.warn('bidModal not found in the DOM.');
    }

})

// Payment Edit Modal
document.addEventListener('DOMContentLoaded', function () {
    // Get edit button and close span
    const dashboardPaymentEditModal = document.getElementById('paymentEditModal');
    const dashboardPaymentEditBtn = document.getElementById('dashboardPaymentEditBtn');
    const closePaymentEditModal = document.querySelector('.closePaymentEditModal');

    if (dashboardPaymentEditBtn) {
        // Show the modal when the button is clicked
        dashboardPaymentEditBtn.addEventListener('click', function () {
            dashboardPaymentEditModal.style.display = 'block';
        });
    } else {
        console.warn('bidButton not found in the DOM.');
    }


    if (closePaymentEditModal) {
        // Close the modal when the close span is clicked
        closePaymentEditModal.addEventListener('click', function () {
            dashboardPaymentEditModal.style.display = 'none';
        });
    } else {
        console.warn('closeModal span not found in the DOM.');
    }

    // Close the modal when clicking outside of it
    if (dashboardPaymentEditModal) {
        window.addEventListener('click', function (event) {
            if (event.target === dashboardPaymentEditModal) {
                dashboardPaymentEditModal.style.display = 'none';
            }
        });
    } else {
        console.warn('bidModal not found in the DOM.');
    }


})


// Dashboard Account Data Address Edit Modal
document.addEventListener('DOMContentLoaded', function (e) {
    e.preventDefault();
    // Get edit button and close span
    const accountAddressEditModal = document.getElementById('accountAddressEditModal');
    const accountDataAddressEditBtn = document.querySelectorAll('.accountDataAddressEditBtn');
    const closeAccountAddressEditModal = document.querySelector('.closeAccountAddressEditModal');

    if (accountDataAddressEditBtn) {
        accountDataAddressEditBtn.forEach((adae) => {
            // Show the modal when the button is clicked
            adae.addEventListener('click', function (e) {
                e.preventDefault();
                accountAddressEditModal.style.display = 'block';
            });
        })

    } else {
        console.warn('bidButton not found in the DOM.');
    }


    if (closeAccountAddressEditModal) {
        // Close the modal when the close span is clicked
        closeAccountAddressEditModal.addEventListener('click', function () {
            accountAddressEditModal.style.display = 'none';
        });
    } else {
        console.warn('closeModal span not found in the DOM.');
    }

    // Close the modal when clicking outside of it
    if (accountAddressEditModal) {
        window.addEventListener('click', function (event) {
            if (event.target === accountAddressEditModal) {
                accountAddressEditModal.style.display = 'none';
            }
        });
    } else {
        console.warn('bidModal not found in the DOM.');
    }


})



// Dashboard Account Data Payment Edit Modal
document.addEventListener('DOMContentLoaded', function (e) {
    e.preventDefault();
    // Get edit button and close span
    const accountPaymentEditModal = document.getElementById('accountPaymentEditModal');
    const accountDataPaymentEditBtn = document.querySelectorAll('.accountDataPaymentEditBtn');
    const closeAccountPaymentEditModal = document.querySelector('.closeAccountPaymentEditModal');

    if (accountDataPaymentEditBtn) {
        accountDataPaymentEditBtn.forEach((adpe) => {
            // Show the modal when the button is clicked
            adpe.addEventListener('click', function (e) {
                e.preventDefault();
                console.log('payment edit clicked')
                accountPaymentEditModal.style.display = 'block';
            });
        })

    } else {
        console.warn('bidButton not found in the DOM.');
    }


    if (closeAccountPaymentEditModal) {
        // Close the modal when the close span is clicked
        closeAccountPaymentEditModal.addEventListener('click', function () {
            accountPaymentEditModal.style.display = 'none';
        });
    } else {
        console.warn('closeModal span not found in the DOM.');
    }

    // Close the modal when clicking outside of it
    if (accountPaymentEditModal) {
        window.addEventListener('click', function (event) {
            if (event.target === accountPaymentEditModal) {
                accountPaymentEditModal.style.display = 'none';
            }
        });
    } else {
        console.warn('bidModal not found in the DOM.');
    }


})


// Open bids bid modal
document.addEventListener('DOMContentLoaded', function () {
    // Get the modal, button, and close span

    const openBidsBidModal = document.querySelector('.openBidsBidModal');
    const opeBidsBidButton = document.querySelectorAll('.opeBidsBidButton');
    const openBidCloseModal = document.querySelector('.openBidCloseModal');

    console.log('openBidsBidModal', openBidsBidModal)

    if (opeBidsBidButton) {
        opeBidsBidButton.forEach((obbb) => {
            obbb.addEventListener('click', function () {
                console.log('a button has been clicked!')
                openBidsBidModal.style.display = 'block'
            });
        })
    } else {
        console.warn('open bids bidButton not found in the DOM')
    }


    if (openBidCloseModal) {
        // Close the modal when the close span is clicked
        openBidCloseModal.addEventListener('click', function () {
            openBidsBidModal.style.display = 'none';
        });
    } else {
        console.warn('closeModal span not found in the DOM.');
    }

    // Close the modal when clicking outside of it
    if (openBidsBidModal) {
        window.addEventListener('click', function (event) {
            if (event.target === openBidsBidModal) {
                openBidsBidModal.style.display = 'none';
            }
        });
    } else {
        console.warn('bidModal not found in the DOM.');
    }
});