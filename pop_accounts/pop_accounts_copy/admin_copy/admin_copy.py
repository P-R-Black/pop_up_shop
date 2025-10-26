# ADMIN_NAVIGATION_COPY = [
#     {"label":"Account Sizes","url": "account_sizes"}, 
#     {"label": "Add Products", "url": "add_products"},
#     {"label":"En Route", "url":"enroute"},
#     {"label":"Inventory", "url":"inventory_admin"},
#     {"label":"Most Interested","url": "most_interested"},
#     {"label":"On Notice", "url": "most_on_notice"}, 
#     {"label":"Sales", "url": "sales_admin"}, 
#     {"label":"Shipments", "url": "shipments"},
#     {"label":"Total Accounts","url": "total_accounts"},
#     {"label":"Total Open Bids","url": "total_open_bids"}, 
#     {"label":"Update Product", "url": "update_product"},
#     {"label":"Update Shipping", "url": "update_shipping"},   
# ]

ADMIN_DASHBOARD_COPY = {"page_title": "Dashboard"}

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


ADMIN_PRODUCTS_PAGE = {
    'page_title': 'Add Products', 'section_title_one': "Add New Product Type, Category, Brand", 
    "section_title_product": "Add Pop Up Product", "section_title_image": "Add Images",
    "section_title_pricing": "Pricing Data", "section_title_buy_now" :"Buy Now Creation",
    "section_title_auction":"Auction Creation", "section_title_additional":"Additional Auction Data",
    "section_title_additional_product": "Additional Product Data"
    }


ADMIN_PRODUCT_UPDATE = {
    "page_title": "Update Product Info", 
    "order_no_title_box": "Orders Awaiting Shipment", 
    "order_no_title_box_two": "Orders Pending Delivery",
    "product_status": [
    {"label": "All Products", "class": "button_medium product_status_button active_product", "id": "all_products",      "data": "prod-tab"},
    {"label": "Coming Soon",  "class": "button_medium product_status_button",                "id": "prod_coming_soon",  "data": "coming-tab"},
    {"label": "In Inventory", "class": "button_medium product_status_button",                "id": "prod_in_inventory", "data": "inventory-tab"}
    ],
    "product_title_box_all_prods_title": "All Products",
    "product_title_box_coming_soon_title": "Coming Soon",
    "product_title_box_in_inventory_title": "In Inventory",
    }


MOST_ON_NOTICE_COPY = {
    "page_title": "Most On Notice", 
    "page_item_list": [
        {"header": "Accounts on Notice"},
        {"header": "Year"},
        {"header": "Item"},
        {"header": "Size"}
    ]

}


MOST_INTERESTED_COPY = {
    "page_title": "Most Interested", 
    "page_item_list": [
        {"header": "Accounts Interested"},
        {"header": "Year"},
        {"header": "Item"},
        {"header": "Size"}
    ]

}