const body = document.querySelector('body')
const sidebar = body.querySelector('.sidebar')
const toggle = body.querySelector('.toggle')
const searchBtn = body.querySelector('.search-box')
const modeSwitch = body.querySelector('.toggle-switch')
const modeText = body.querySelector('.mode-text')
const navLogoText = body.querySelector('.logo-text')


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

modeSwitch.addEventListener('click', () => {
    body.classList.toggle('dark');

    if (body.classList.contains("dark")) {
        modeText.innerText = "Light Mode"
    } else {
        modeText.innerText = "Dark Mode"
    }
})


// bid modal
document.addEventListener('DOMContentLoaded', function () {
    // Get the modal, button, and close span
    const modal = document.getElementById('bidModal');
    const btn = document.getElementById('bidButton');
    const span = document.querySelector('.closeModal');

    // Show the modal when the button is clicked
    btn.addEventListener('click', function () {
        modal.style.display = 'block';
    });

    // Close the modal when the close span is clicked
    span.addEventListener('click', function () {
        modal.style.display = 'none';
    });

    // Close the modal when clicking outside of it
    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
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




var expandButton = document.querySelector(".expandButton");
var checkoutOptionsContainer = document.querySelector('.checkout_options_container')
console.log('expandButton', expandButton)
console.log('checkoutOptionsContainer', checkoutOptionsContainer)

expandButton.addEventListener("click", function () {
    console.log('button clicked')
    /* Toggle between adding and removing the "active" class,
    to highlight the button that controls the panel */
    this.classList.toggle("active");
    checkoutOptionsContainer.classList.toggle('show')

    /* Toggle between hiding and showing the active panel */
    // var panel = this.nextElementSibling;
    // if (panel.style.display === "block") {
    //     panel.style.display = "none";
    // } else {
    //     panel.style.display = "block";
    // }
});