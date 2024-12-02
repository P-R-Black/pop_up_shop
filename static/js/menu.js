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



document.addEventListener('DOMContentLoaded', function () {
    // Get the modal, button, and close span
    const modal = document.getElementById('bidModal');
    const btn = document.getElementById('bidButton');
    const span = document.querySelector('.closeModal');
    console.log('span', span)

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