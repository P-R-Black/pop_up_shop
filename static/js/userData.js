
document.addEventListener("DOMContentLoaded", () => {

    addItemsToUserLists(
        notifyMeButton = document.querySelectorAll('.notify-me-button'),
        '/pop_accounts/mark-on-notice/',
        'On Notice',
        emoji = '❤️'
    )

    addItemsToUserLists(
        notifyMeButton = document.querySelectorAll('.interested_btn'),
        '/pop_accounts/mark-interested/',
        'Interested',
        emoji = '❤️'
    )

    uncheckListedSavedItems(
        checkboxInput = document.querySelectorAll(".on_notice_checkbox"),
        "/pop_accounts/mark-on-notice/",
        "product-two",
        "notice-product"
    )

    uncheckListedSavedItems(
        checkboxInput = document.querySelectorAll(".interested_checkbox"),
        "/pop_accounts/mark-interested/",
        "product",
        "int-product"
    )

})



function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(trimmed.split('=')[1]);
                break;
            }
        }
    }
    return cookieValue;
}

function getCookieTwo(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


// Adds Items to lists like Interested-In or On-Notice and Updates UI
const addItemsToUserLists = (addToListBtn, fetchUrl, label, emoji = '❤️') => {
    addToListBtn.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();

            const productId = this.dataset.productId;
            const isInterested = this.dataset.interested == "true";

            fetch(fetchUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({ product_id: productId })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "added") {
                        this.textContent = `${label} ${emoji}`;
                        this.dataset.interested = "true";
                    } else if (data.status === "removed") {
                        this.textContent = `${label}`;
                        this.dataset.interested = "false";
                    } else {
                        alert(data.message || "Something went wrong.")
                    }
                })
                .catch(err => {
                    console.log('Request failed', err);
                    alert("Network error occurred");
                })
        })
    })
}


// Removes Items from lists like Interested-In or On-Notice on Dashboard and on Interested-In & On-Notice Pages
const uncheckListedSavedItems = (checkboxInput, fetchUrl, getIdElementItemOne, getIdElementItemTwo) => {

    checkboxInput.forEach((checkbox) => {
        checkbox.addEventListener('change', (event) => {
            event.preventDefault();

            const productId = event.target.dataset.productId;
            const action = event.target.checked ? "add" : "remove";


            fetch(fetchUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookieTwo("csrftoken"),
                },
                body: JSON.stringify({ product_id: productId, action })
            })
                .then((response) => {
                    if (!response.ok) throw new Error("Request failed");
                    return response.json();
                })
                .then((data) => {
                    if ((data.status === "success" || data.status == "removed") && action === "remove") {
                        // Try removing either item in dashboard box  or on dedicated interested/On Notice page 
                        const item = document.getElementById(`${getIdElementItemOne}-${productId}`) ||
                            document.getElementById(`${getIdElementItemTwo}-${productId}`);
                        if (item) {
                            item.style.transition = "opacity 0.3s ease";
                            item.style.opacity = 0;
                            setTimeout(() => item.remove(), 300)
                        }
                    }
                })
                .catch((error) => console.error("Error updating interest:", error));
        })
    })

}
