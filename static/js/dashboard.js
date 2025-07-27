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

                console.log('edit address modal opening!')

                accountAddressEditModal.style.display = 'block';

                const addressId = this.getAttribute('data-address-id')
                console.log('addressId', addressId);

                fetch(`/pop_accounts/get-address/${addressId}/`)
                    .then(response => response.json())
                    .then(data => {

                        console.log('data', data)
                        // Populate the modal form fields with response data;
                        const streeAddressPrefix = document.querySelectorAll('.personal_info_input_prefix')
                        const streeAddressFirstName = document.querySelectorAll('.personal_info_input_first_name')
                        const streeAddressMiddleName = document.querySelectorAll('.personal_info_input_middle_name')
                        const streeAddressLastName = document.querySelectorAll('.personal_info_input_last_name')
                        const streeAddressSuffix = document.querySelectorAll('.personal_info_input_suffix')
                        const streetAddressLineOne = document.querySelectorAll('.personal_info_street_address_one_input')
                        const streetAddressLineTwo = document.querySelectorAll('.personal_info_street_address_two_input')
                        const streetAddressSte = document.querySelectorAll('.personal_info_apt_inputs');
                        const streetAddressCityTown = document.querySelectorAll('.personal_info_address_city_input');
                        const streetAddressState = document.querySelectorAll('.personal_info_address_state');
                        const streetAddressZipCode = document.querySelectorAll('.personal_info_address_zip_input');
                        const streetAddressDelivInstruct = document.querySelectorAll('.delivery_instruct_text');
                        const streetAddressHiddenInput = document.querySelectorAll('#address-id')  // hidden input

                        streeAddressPrefix.forEach((addyOne) => {
                            addyOne.value = data.prefix;
                        })

                        streeAddressFirstName.forEach((addyOne) => {
                            addyOne.value = data.first_name;
                        })
                        streeAddressMiddleName.forEach((addyOne) => {
                            addyOne.value = data.middle_name;
                        })

                        streeAddressLastName.forEach((addyOne) => {
                            addyOne.value = data.last_name;
                        })

                        streeAddressSuffix.forEach((addyOne) => {
                            addyOne.value = data.suffix;
                        })
                        streetAddressLineOne.forEach((addyOne) => {
                            addyOne.value = data.address_line;
                        })
                        streetAddressLineTwo.forEach((addyOne) => {
                            addyOne.value = data.address_line2;
                        })
                        streetAddressSte.forEach((addyOne) => {
                            addyOne.value = data.apartment_suite_number
                        })
                        streetAddressCityTown.forEach((addyOne) => {
                            addyOne.value = data.town_city

                        })

                        streetAddressState.forEach((addyOne) => {
                            addyOne.value = data.state

                        })
                        streetAddressZipCode.forEach((addyOne) => {
                            addyOne.value = data.postcode

                        })
                        streetAddressDelivInstruct.forEach((addyOne) => {
                            addyOne.value = data.delivery_instructions

                        })

                        streetAddressHiddenInput.forEach((addyOne) => {
                            addyOne.value = addressId

                        })


                    })
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


// Remove Address in Personal Info Page
document.addEventListener('DOMContentLoaded', () => {

    const removeButtons = document.querySelectorAll('.accountDataAddressRemoveBtn');

    removeButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();


            console.log('remove clicked!')

            const addressId = this.getAttribute('data-address-id');
            console.log('addressId', addressId)


            const confirmed = confirm("Are you sure you want to remove this address?");
            if (!confirmed) return;

            fetch(`/pop_accounts/delete-address/${addressId}/`, {
                method: 'POST',  // or 'DELETE' if your backend supports it
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})  // optional
            })
                .then(response => {
                    if (response.ok) {
                        // Remove the entire container
                        this.closest('.dashboard_databox_small').remove();
                    } else {
                        alert("Failed to remove address.");
                    }
                });
        });
    });

    // Function to get CSRF token from cookie
    function getCSRFToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.slice(name.length + 1));
            }
        }
        return '';
    }
});


// Set Address as Default Address
document.addEventListener('DOMContentLoaded', () => {
    const defaultButtons = document.querySelectorAll('.setDefaultAddressBtn');

    defaultButtons.forEach(button => {
        button.addEventListener('click', function () {
            // e.preventDefault();

            console.log('defaultButtons called!')

            const addressId = this.getAttribute('data-address-id');
            console.log('addressId', addressId);

            fetch(`/pop_accounts/set-default-address/${addressId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload()
                    } else {
                        alert('Failed to set default address.')
                    }
                })
        })
    })
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






const salesDataSets = {
    day: {
        labels: pastTwentyDaySalesJson.labels,
        data: pastTwentyDaySalesJson.data,
        label: 'Daily Sales'
    },
    month: {
        labels: pastTwelveMonthsSalesJson.labels,
        data: pastTwelveMonthsSalesJson.data,
        label: 'Monthly Sales'
    },
    year: {
        labels: pastFiveYearsSalesJson.labels,
        data: pastFiveYearsSalesJson.data,
        label: 'Yearly Sales'
    }
};

const comparisonDataSets = {
    day: {
        labels: dayOverDaySalesCompJson.labels,
        datasets: [
            {
                label: "This Year",
                data: dayOverDaySalesCompJson.current_year,
                borderColor: 'rgba(76, 175, 80, 0.1)',
                backgroundColor: "rgb(203, 58, 96)",
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                borderRadius: Number.MAX_VALUE,
            },
            {
                label: "Last Year",
                data: dayOverDaySalesCompJson.previous_year,
                borderColor: "rgba(244, 67, 54, 0.1)",
                backgroundColor: "rgba(240, 160, 12, 1)",
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                borderRadius: Number.MAX_VALUE,
            }
        ]
    },
    month: {
        labels: monthOverMonthCompJson.labels,
        datasets: [
            {
                label: "This Year",
                data: monthOverMonthCompJson.current_year,
                borderColor: "rgba(33, 150, 243, 0.1)",
                backgroundColor: "rgb(203, 58, 96)",
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                borderRadius: Number.MAX_VALUE,
            },
            {
                label: "Last Year",
                data: monthOverMonthCompJson.previous_year,
                borderColor: "rgba(33, 150, 243, 0.1)",
                backgroundColor: "rgba(240, 160, 12, 1)",
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                borderRadius: Number.MAX_VALUE,
            }
        ]
    },
    year: {
        labels: yearOverYearCompJson.labels,
        datasets: [
            {
                label: "This 5 Years",
                data: yearOverYearCompJson.current_year,
                borderColor: "rgba(243, 7, 7, 0.1)",
                backgroundColor: "rgb(203, 58, 96)",
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                borderRadius: Number.MAX_VALUE,
            },
            {
                label: "Last 5 Years",
                data: yearOverYearCompJson.current_previous_year,
                borderColor: "rgba(103, 58, 183, 0.1)",
                backgroundColor: "rgba(240, 160, 12, 1)",
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                borderRadius: Number.MAX_VALUE,
            }
        ]
    }
};


const salesCtx = document.getElementById('sales_chart_data').getContext('2d');
const comparisonCtx = document.getElementById('sales_chart_two_data').getContext('2d');

let salesChart = new Chart(salesCtx, {
    type: 'bar',
    data: {
        labels: salesDataSets.day.labels,
        datasets: [{
            label: salesDataSets.day.label,
            data: salesDataSets.day.data,
            borderColor: 'rgba(103, 58, 183, 0.1)',
            backgroundColor: 'rgb(203, 58, 96)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            borderRadius: Number.MAX_VALUE,
        }]
    },
    options: {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
            legend: {
                display: true,
                labels: {
                    color: 'rgb(203, 58, 96)'
                }
            },
        },
        scales: {
            x: {
                ticks: {
                    color: 'rgb(203, 58, 96)',
                    font: { family: 'Libre Carlson Text' }
                }
            },
            y: {
                beginAtZero: true,
                ticks: {
                    color: 'rgb(203, 58, 96)',
                    font: { family: 'Libre Carlson Text' },
                    callback: function (value) {
                        return `$${value}`
                    }
                }
            }
        }
    }
});

let comparisonChart = new Chart(comparisonCtx, {
    type: 'bar',
    data: {
        labels: comparisonDataSets.day.labels,
        datasets: comparisonDataSets.day.datasets
    },
    options: {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
            legend: {
                display: true,
                labels: {
                    color: 'rgb(203, 58, 96)'
                }
            },
        },
        scales: {
            x: {
                ticks: {
                    color: 'rgb(203, 58, 96)',
                    font: { family: 'Libre Carlson Text' }
                }
            },
            y: {
                beginAtZero: true,
                ticks: {
                    color: 'rgb(203, 58, 96)',
                    font: { family: 'Libre Carlson Text' },
                    callback: function (value) {
                        return `$${value}`
                    }
                }
            }
        }
    }
});


document.querySelectorAll('#sales_filter a').forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault();
        const view = this.dataset.view;

        // Update sales chart
        const salesData = salesDataSets[view];
        salesChart.data.labels = salesData.labels;
        salesChart.data.datasets[0].data = salesData.data;
        salesChart.data.datasets[0].label = salesData.label;
        salesChart.update();

        // Update comparison chart
        const comparisonData = comparisonDataSets[view];
        comparisonChart.data.labels = comparisonData.labels;
        comparisonChart.data.datasets = comparisonData.datasets;
        comparisonChart.update();
    });
});