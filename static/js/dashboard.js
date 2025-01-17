// Dashboard modal
document.addEventListener('DOMContentLoaded', function () {
    // Get the edit, button, and close span
    const dashboardEditSizeModal = document.getElementById('sizeEditModal');
    const dashboardSizeEditBtn = document.getElementById('dashboardSizeEditBtn');
    const closeSizeEditModal = document.querySelector('.closeSizeEditModal');



    if (dashboardSizeEditBtn) {
        // Show the modal when the button is clicked
        dashboardSizeEditBtn.addEventListener('click', function () {
            console.log('dashboardSizeEditBtn called')
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

    // // Close the modal when clicking outside of it
    // if (modal) {
    //     window.addEventListener('click', function (event) {
    //         if (event.target === modal) {
    //             modal.style.display = 'none';
    //         }
    //     });
    // } else {
    //     console.warn('bidModal not found in the DOM.');
    // }
});