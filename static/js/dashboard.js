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
    const dashboardlocationEditModal = document.getElementById('locationEdittModal');
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
            if (event.target === dashboardlocationEdittModal) {
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
    const dashboardPaymentEditModal = document.getElementById('paymentEdittModal');
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