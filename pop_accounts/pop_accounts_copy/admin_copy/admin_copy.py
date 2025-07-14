ADMIN_NAVIGATION_COPY = [
    {"label":"Account Sizes","url": "account_sizes"}, 
    {"label":"En Route", "url":"enroute"},
    {"label":"Inventory", "url":"inventory_admin"},
    {"label":"Most Interested","url": "most_interested"},
    {"label":"On Notice", "url": "most_on_notice"}, 
    {"label":"Sales", "url": "sales_admin"}, 
    {"label":"Shipments", "url": "shipments"},
    {"label":"Total Accounts","url": "total_accounts"},
    {"label":"Total Open Bids","url": "total_open_bids"}, 
    {"label":"Update Shipping", "url": "update_shipping"},   
]

ADMIN_SHIPPING_UPDATE = {
    "page_title": "Update Shipping Info", 
    "order_no_title_box": "Orders Awaiting Shipment", 
    "order_no_title_box_two": "Orders Pending Delivery"
    }
ADMIN_SHIPING_OKAY_PENDING = {"page_title": "Pending Okay To Ship"}

ADMIN_SHIPMENTS = {"page_title": "Shipments", "shipment_status": [
    {"label": "All Shipments", "class": "button_medium shipment_status_button active_shipment", "id": "shipments", "data": "ship-tab"},
    {"label": "Pending Delivery", "class": "button_medium shipment_status_button", "id": "pending_deliv", "data": "pending-tab"},
    {"label": "Delivered", "class": "button_medium shipment_status_button", "id": "delivered", "data": "deliv-tab"}
    ],
    "order_no_title_box_shipment_title": "All Shipments",
    "order_no_title_box_pending_title": "Pending Delivery",
    "order_no_title_box_delivered_title": "Delivered",
    }



