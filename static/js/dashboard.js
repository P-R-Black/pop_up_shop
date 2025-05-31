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




// chart js
// const DATA_COUNT = 7;
// const NUMBER_CFG = { count: DATA_COUNT, min: -100, max: 100 };

// const labels = Utils.months({ count: 7 });
// const data = {
//     labels: labels,
//     datasets: [
//         {
//             label: 'Fully Rounded',
//             data: Utils.numbers(NUMBER_CFG),
//             borderColor: Utils.CHART_COLORS.red,
//             backgroundColor: Utils.transparentize(Utils.CHART_COLORS.red, 0.5),
//             borderWidth: 2,
//             borderRadius: Number.MAX_VALUE,
//             borderSkipped: false,
//         },
//         {
//             label: 'Small Radius',
//             data: Utils.numbers(NUMBER_CFG),
//             borderColor: Utils.CHART_COLORS.blue,
//             backgroundColor: Utils.transparentize(Utils.CHART_COLORS.blue, 0.5),
//             borderWidth: 2,
//             borderRadius: 5,
//             borderSkipped: false,
//         }
//     ]
// };

// const config = {
//     type: 'bar',
//     data: data,
//     options: {
//         responsive: true,
//         plugins: {
//             legend: {
//                 position: 'top',
//             },
//             title: {
//                 display: true,
//                 text: 'Chart.js Bar Chart'
//             }
//         }
//     },
// };

const indChartArea = document.getElementById('sales_chart_data');

// chart js
const sales_stats = () => {
    const currData = [10, 20, 30, 40, 50, 70, 55, 45, 65, 85, 75]
    const data = {
        labels: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
        datasets: [
            {
                label: 'Daily Sales',
                data: currData,
                backgroundColor: ['rgb(203, 58, 96)'],
                borderColor: 'red',
                borderWidth: 2,
                // pointRadius: 5,
                borderRadius: Number.MAX_VALUE,
                borderSkipped: false,
            }]
    }

    const legendMargin = {
        id: 'legendMargin',
        beforeInit(chart, legend, options) {
            const fitValue = chart.legend.fit


            chart.legend.fit = function fit() {
                fitValue.bind(chart.legend)()
                return this.height += 30;
            }
        }
    };

    const config = {
        type: 'bar',
        data,
        options: {
            maintainAspectRatio: false,
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    fullWidth: true,
                    labels: {
                        // usePointStyle: true,
                        // pointStyle: 'dash',
                        color: 'rgb(203, 58, 96)',
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        color: 'rgb(203, 58, 96)',
                        font: {
                            family: 'Libre Caslon Text',
                        }
                    }
                },
                y: {
                    ticks: {
                        color: 'rgb(203, 58, 96)',
                        font: {
                            family: 'Libre Caslon Text',
                        }
                    },
                    beginAtZero: true,
                    afterTickToLabelConversion: (ctx) => {
                        newTicks = []

                        for (let i = 0; i < ctx.ticks.length; i++) {
                            let theVal = ctx.ticks[i]['value']
                            newTicks.push({ value: theVal, label: '$' + theVal })
                        }
                        ctx.ticks = newTicks

                    }
                }
            }
        },
        plugins: [legendMargin]

    };

    let chartStatus = Chart.getChart('sales_chart_data');
    if (chartStatus != undefined) {
        chartStatus.destroy()
    }
    var ctx = new Chart(indChartArea, config);
}




const salesChartTwoData = document.getElementById('sales_chart_two_data');
const yearOverYearStats = () => {
    // chart js
    const DATA_COUNT = 7;
    const NUMBER_CFG = { count: DATA_COUNT, min: -100, max: 100 };

    const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'] //Utils.months({ count: 7 });
    const data = {
        labels: labels,
        datasets: [
            {
                label: 'Last Year Sales',
                data: [5, 10, 15, 20, 25], //Utils.numbers(NUMBER_CFG),
                borderColor: 'blue', //Utils.CHART_COLORS.red,
                backgroundColor: 'lightblue', //Utils.transparentize(Utils.CHART_COLORS.red, 0.5),
                borderWidth: 2,
                borderRadius: Number.MAX_VALUE,
                borderSkipped: false,
            },
            {
                label: 'This Year Sales',
                data: [10, 20, 30, 40, 50],//Utils.numbers(NUMBER_CFG),
                borderColor: 'red', //Utils.CHART_COLORS.blue,
                backgroundColor: ['rgb(203, 58, 96)'], //Utils.transparentize(Utils.CHART_COLORS.blue, 0.5),
                borderWidth: 2,
                borderRadius: Number.MAX_VALUE,
                borderSkipped: false,
            }
        ]
    };

    const config = {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    fullWidth: true,
                    labels: {
                        // usePointStyle: true,
                        // pointStyle: 'dash',
                        color: 'rgb(203, 58, 96)',
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        color: 'rgb(203, 58, 96)',
                        font: {
                            family: 'Libre Caslon Text',
                        }
                    }
                },
                y: {
                    ticks: {
                        color: 'rgb(203, 58, 96)',
                        font: {
                            family: 'Libre Caslon Text',
                        }
                    },
                    beginAtZero: true,
                    afterTickToLabelConversion: (ctx) => {
                        newTicks = []

                        for (let i = 0; i < ctx.ticks.length; i++) {
                            let theVal = ctx.ticks[i]['value']
                            newTicks.push({ value: theVal, label: '$' + theVal })
                        }
                        ctx.ticks = newTicks

                    }
                }
            }
        },
    };

    let chartStatus = Chart.getChart('sales_chart_two_data');
    if (chartStatus != undefined) {
        chartStatus.destroy()
    }
    var ctx = new Chart(salesChartTwoData, config);
}


window.onload = function () {

    if (window.innerWidth <= 600) {
        Chart.defaults.font.size = 10;
    } else if (window.innerWidth >= 601 && window.innerWidth <= 1024) {
        Chart.defaults.font.size = 16;
    } else {
        Chart.defaults.font.size = 22;
    }
    sales_stats()
    yearOverYearStats()
}
