from django.urls import reverse

ABOUT_US_COPY = {"page_title": "About The Pop Up", "paragraph_title": "Connecting buyers with authentic products", 
            "paragraph": "The Pop Up’s focus is authenticity and we exist to bring authentic products to buyers."}

HOW_IT_WORKS_COPY = {
    "page_title": "How it Works",
    "instructions": [{
        "instruction_level" : "Basic", "instruction": [
            {"instruct": "Find a product you like"},
            {"instruct": "Place a bid before auction close or buy now"},
            {"instruct": "If winning bid placed or item purchased now, item shipped to you"}]
    },
    {
        "instruction_level" : "Advanced", "instruction": [
            {"instruct": "We track upcoming releases from different manufacturers", "label":"Future Releases", "url": "future_releases"},
            {"instruct": "We secure products based on community interest", "label":"Coming Soon", "url": "coming_soon"},
            {"instruct": "Get notice of product availabilty by pressing \"Notify Me\" on the \"Coming Soon'\" page"},
             {"instruct": "Receive email notice when auction opens for product"},
            {"instruct": "Place a bid on product before auction close or buy product now"},
            {"instruct": "If winning bid placed or item purchased now, item shipped to you"}
            
            ]
    }]
}

VERIFICATION_COPY = {
    "page_title": "Verification",
    "sections": [{
        "section_title": "We Got Receipts", "section_paragraph":[
            {"paragraph": "We only secure product from the manufacturers and trusted retailers, and we’ve got the receipts to prove it. If you’re going to pay top dollar for your favorite kicks or clothing item, we want to make sure you receive an authentic product."}
        ]
    },
    {
        "section_title": "The Fight Against Counterfeits", "section_paragraph":[
            {"paragraph": "There was a time when counterfeits were easy to spot. "
            "Uneven stitching on a Gucci bag, an incorrect logo on a Louis Vuitton item, a "
            "Rolex with a second hand that ticks, or a non-symmetrical Jumpman were all tell tale "
            "signs of counterfeit goods. However, counterfeiters and counterfeits have gotten better, "
            "making it difficult for even the best professionals to spot the difference between real and "
            "counterfeit."}, {"paragraph":"We attempt to limit our communities exposure to counterfeits by only purchasing "
            "roduct directly from the manufacturers and/or trusted retailers."}
        ]
    },
    
    ]
}


CONTACT_US_COPY = {
    "page_title": "Contact Us",
    "section_paragraph": "Your concerns are important to us, and we’ll get back to you within 24 hours of receiving your message. "
}

HELP_CENTER_COPY = {
    "page_title": "Help Center",
    "help_center_options_top": [
        {"option": "Buying", "id": "help_center_buying"},
        {"option": "Selling", "id": "help_center_selling"},
        {"option": "My Account", "id": "help_center_accounts"},
        ],
    "buying_options": [
        {"buying_option_title": "Know More About Buying", 
         "buying_option": [
            {"label": "Auction Bid vs Buy Now", "url": "buying-help"},
            {"label": "Retracting a Bid", "url": "buying-help"},
            {"label": "Who Am I Buying From", "url": "buying-help"},
         ]}],
    "selling_options": [
        {"selling_option_title": "Know More About Selling", 
         "selling_option": [
            {"label": "Who is Doing the Selling", "url": "selling-help"},
            {"label": "Can I Sell on The Pop Up", "url": "selling-help"},
         ]}],
    "account_options": [
        {"account_option_title": "Understanding My Account", 
         "account_option": [
            {"label": "Update My Account Information", "url": "account-help"},
            {"label": "Reset My Password", "url": "account-help"},
            {"label": "Delete My Account", "url": "account-help"},
         ]}],
    "help_center_options_bottom": [
        {"option": "Shipping and Tracking", "id": "help_center_shipping"},
        {"option": "Payment Options", "id": "help_center_payments"},
        {"option": "Fees", "id": "help_center_fees"},
        ],
    "ship_track_options": [
        {"ship_track_option_title": "Know More About Shipping and Tracking", 
         "ship_track_option": [
            {"label": "General Shipping", "url": "shipping-help"},
            {"label": "Track Shipping", "url": "shipping-help"},
            {"label": "International Shipping", "url": "shipping-help"},
            {"label": "Update My Shipping Address", "url": "shipping-help"},
         ]}],
    "payment_options": [
        {"payment_option_title": "Know More Payment Options", 
         "payment_option": [
            {"label": "What are the Payment Options", "url": "payment-help"},
            {"label": "Does The Pop Up Accept Cryptocurrency as Payment", "url": "payment-help"},
            {"label": "Payment Processing", "url": "payment-help"},
         ]}],
    "fee_options": [
        {"fee_option_title": "Understanding Fees", 
         "fee_option": [
            {"label": "Processing Fee", "url": "fees-help"},
         ]}]
}

HELP_CENTER_PAGE_BUYING = {
    "page_title": "Buying",
    "side_link_links": [
        {"label": "Auction Bid vs Buy Now", "url": "#bidvbuy"},
        {"label": "Retracting a Bid", "url": "#retractBid"},
        {"label": "Who Am I Buying From", "url": "#mainSeller"},
    ],
    "sections": [
        {"section_title": "Auction Bid vs Buy Now",  "id": "bidvbuy",
        "section_paragraph": [
            {"paragraph": "To win the opportunity to purchase a product that is in an open auction, you must have the best offer at the time of the auction's close. Placing a bid in an auction is as simple as finding the product you wish to bid on, pressing the \"Bid\" button, and entering a monetary amount that is higher than the current highest bid. If a higher bid is placed on the product, we notify you. If you hold the winning bid at the close of the auction we will notify you."},
            {"paragraph": "Some products can be purchased without placing a bid, by pressing the \"Buy Now\" button. The \"Buy Now\" button will direct the user to the checkout page, where they can buy the product without making a bid in the auction. Once the purchasers payment has been accepted, the auction for the product will end and the product will be shipped to the purchaser."},
            {"paragraph": "To win a product through auction, you may need to track the product until the auction closes. Also, while the auction is open, you may need to place several bids in order to secure the product. By buying now, you can bypass the need for bidding and waiting for the auction to close. "}
         ]
         },

        {"section_title": "Retracting a Bid",  "id": "retractBid",
        "section_paragraph": [
            {"paragraph_title":"I Need to Cancel My Bid", "paragraph": "To cancel a bid, go to your dashboard, go to the \"Open Bids\" section of the dashboard and press the \"Adjust Bid\" button. In the pop-up window, select \"Cancel Bid\"."},
            {"paragraph_title":"I Need to Edit My Bid", "paragraph": "In the case you've entered a higher bid or lower bid than you meant to, you can adjust your bid. One way to adjust your bid is to go to your dashboard, go to the \"Open Bids\" section of the dashboard and press the \"Adjust Bid\" button. In the pop-up window enter the correct amount you want to bid in the \"Enter your bid\" field."},
            {"paragraph": "Another way to edit your bid is by going to the \"Auction\" page and finding the product you've bid on, select the \"Make Bid\" button, and enter the correct bid in the \"Enter your bid\" field. "}
         ]
         },
        
        {"section_title": "Who Am I Buying From",  "id": "mainSeller",
        "section_paragraph": [
            {"paragraph": "All products are being sold by \"The Pop Up.\" We want to ensure that everything sold is authentic, and the best weay to do that is by controlling what gets bought and sold. We only secure product from manufacturers and trusted retailers, and we keep the receipts to prove it. We believe that if you’re going to pay top dollar for your favorite pair kicks or clothing item, it shoud be the authentic product."},
         ]
         },
    ]
}

HELP_CENTER_PAGE_SELLING = {
    "page_title": "Selling",
    "side_link_links": [
        {"label": "Who is Doing the Selling", "url": "#primarySeller"},
        {"label": "Can I Sell on The Pop Up", "url": "#canISell"},
    ],
    "sections": [
        {"section_title": "Who is Doing the Selling",  "id": "primarySeller",
        "section_paragraph": [
            {"paragraph": "All products are being sold by \"The Pop Up.\" We want to ensure that everything sold is authentic, and the best weay to do that is by controlling what gets bought and sold. We only secure product from manufacturers and trusted retailers, and we keep the receipts to prove it. We believe that if you’re going to pay top dollar for your favorite pair kicks or clothing item, it shoud be the authentic product."},
         ]
         },

        {"section_title": "Can I Sell on The Pop Up",  "id": "canISell",
        "section_paragraph": [
            {"paragraph": "At this time we're not accepting resellers on the platform."},
        ]
         },
        
    ]
}


HELP_CENTER_PAGE_ACCOUNT = {
    "page_title": "My Account",
    "side_link_links": [
        {"label": "Update My Account Information", "url": "#paymentOptions"},
        {"label": "Reset My Password", "url": "#cryptoPayment"},
        {"label": "Delete My Account", "url": "#paymentProcessing"},
    ],
    "sections": [
        {"section_title": "Update My Account Information",  "id": "paymentOptions",
        "section_paragraph": [
            {"paragraph": "To update your account information, go to the \"Dashboard\" page by clicking on \"Dashboard\" in the navigation menu to the left of the screen (bottom of the screen if you're using a mobile device). On the \"Dashboard\" page, locate the \"Personal\" section, and click the \"edit\" links to update information related to your shoe size, mailing address or payment method. Click the \"more\" link for more options."},
         ]
         },

        {"section_title": "Reset My Password",  "id": "cryptoPayment",
        "section_paragraph": [
            {"paragraph": "To reset the password of your account, click on the \"Log in\" link in the navigation bar. From there, press the \"Continue with email\" button. Next, enter your email address that you used to register your account and press the continue button. If you have an account with \"The Pop Up\", you'll be taken to the \"Login\" screen. At the bottom of the \"Login\", click on the \"Forgot Password\" link and follow the directions displayed."},
        ]
         },
         {"section_title": "Delete My Account",  "id": "paymentProcessing",
        "section_paragraph": [
            {"paragraph": "To delete your account, go to the \"Dashboard\" page by clicking on \"Dashboard\" in the navigation menu to the left of the screen (bottom of the screen if you're using a mobile device). On the \"Dashboard\" page, locate the \"Personal\" section, and click the \"more\" link. At the bottom of the page, you will find a button that will allow you to delete your account. "},
        ]
         },
        
    ]
}



HELP_CENTER_PAGE_SHIPPING = {
    "page_title": "Shipping and Tracking",
    "side_link_links": [
        {"label": "General Shipping", "url": "#generalShipping"},
        {"label": "Track Shipping", "url": "#trackShipping"},
        {"label": "International Shipping", "url": "#IntShipping"},
        {"label": "Update My Shipping Address", "url": "#shippingUpdate"},
    ],
    "sections": [
        {"section_title": "General Shipping", "id": "generalShipping",
        "section_paragraph": [
            {"paragraph": "For domestic shipments, we ship with the United States Postal Service. Upon purchasing a product, two shipping choices are offered, standard shipping and express shipping. Shipping costs vary depending on shipping location and shipping destination. "},
            {"paragraph": "Express shipping will cost more than standard shipping, and packages shipped by express shipping typically arrive to their destination faster than if shipped using standard shipping. However, unforseen circumstance including but not limited to weather, flight delays, or lack of service at the destination area can prevent packages from being delievered in a timely manner."}
         ]
         },

        {"section_title": "Track Shipping",  "id": "trackShipping",
        "section_paragraph": [
            {"paragraph": "To track your purchase, go to your dashboard and locate the \"Shipping & Tracking\" section. If the status is \"shipped\", click on the \"shipped\" link to access the tracking number of our package. With the tracking number, you can track your purchase at usps.com If the status is \"processing,\" the package has not shipped yet. "},
        ]
         },
        {"section_title": "International Shipping",  "id": "IntShipping",
        "section_paragraph": [
            {"paragraph": "At this time we do not ship purchases internationally."},
        ]
         },
        {"section_title": "Update My Shipping Address",  "id": "shippingUpdate",
        "section_paragraph": [
            {"paragraph": "There are several places to update your mailing address. Go to the \"Dashboard\" page by clicking on \"Dashboard\" in the navigation menu to the left of the screen. On the \"Dashboard\" page, locate the \"Personal\" section, and click the \"edit\" link that is in-line with \"Location.\" Add the new mailing address and press the \"Update\" button."},
            {"paragraph": "Another way to update your mailing address is by accessing the \"Account Data\" page. To access the \"Account Data\" page, click on \"Dashboard\" in the navigation menu on the left of the screen (bottom of the screen if you are using a mobile device). On the \"Dashboard\" page, locate the \"Personal\" section, and click the \"more\" link at the bottom of the \"Personal\" section. Scroll to the middle of the \"Account Data\" page and enter the new mailing address and click the \"Add Address\" button. "},
            {"paragraph": "By following the instructions in the paragraph above and scrolling past the \"Add Address\" button, you can also edit an address you already have on file, as well make an already listed address your default mailing address."},
            {"paragraph": "During the checkout process, there is an opportunity to change the shipping address and the name that the package is being shipped to. If you have items in your cart and are ready to checkout, click on \"Cart\" in the navigation menu on the left of the screen (bottom of the screen if you are using a mobile device). Locate the \"Shipping to\" section on the checkout page and press the \"Change\" link. Add the name of the package recipient and the new address and press the \"submit\" button."},
        ]
         },
        
    ]
}

HELP_CENTER_PAGE_PAYMENT = {
    "page_title": "Payment Options",
    "side_link_links": [
        {"label": "What are the Payment Options", "url": "#paymentOptions"},
        {"label": "Does The Pop Up Accept Cryptocurrency as Payment", "url": "#cryptoPayment"},
        {"label": "Payment Processing", "url": "#paymentProcessing"},
    ],
    "sections": [
        {"section_title": "What are the Payment Options", "id": "paymentOptions",
        "section_paragraph": [
            {"paragraph": "We currently accept PayPal, Venmo, Visa, Mastercard, Discover, Apple Pay, Google Pay, DAI and USDC as forms of payment."},         ]
         },

        {"section_title": "Does The Pop Up Accept Cryptocurrency as Payment",  "id": "cryptoPayment",
        "section_paragraph": [
            {"paragraph": "\"The Pop Up\" accepts DAI and USDC stable coins."},
        ]
         },
        {"section_title": "Payment Processing",  "id": "paymentProcessing",
        "section_paragraph": [
            {"paragraph": "PayPal, Venmo, credit card, debit card, Apple Pay and Google Pay payments are processed through Stripe."},
            {"paragraph": "PDAI and USDC payments are processed through BitPay."},
        ]
         },
        
    ]
}

HELP_CENTER_PAGE_FEE = {
    "page_title": "Fees",
    "side_link_links": [
        {"label": "Processing Fee", "url": "#processingFee"},
    
    ],
    "sections": [
        {"section_title": "Processing Fee", "id": "processingFee",
        "section_paragraph": [
            {"paragraph": "A processing fee is add to each purchase. Our processing fee is typically 15% of the shopping cart's subtotal. This processing fee is used to service and maintain the site as well as cover other administration expenses. Fees are subject to change without warning."},         ]
        },
        
    ]
}


SITE_MAP_COPY = {
    "page_title": "Site Map",
    "page_update_title": "Last Updated",
    "page_update_date": "January 1, 2025",
    "pages": [
        {
            "page_section" : [
                {"title": "Home", "full_url":"pop_up_home:home", 
                    "sub_page": [
                        {"sub_page_title": "About Us", "full_url":"pop_up_home:about"},
                        {"sub_page_title": "How It Works", "full_url":"pop_up_home:how-it-works"},
                        {"sub_page_title": "Verification", "full_url":"pop_up_home:verification"},
                        {"sub_page_title": "Contact Us", "full_url":"pop_up_home:contact"},
                        {"sub_page_title": "Help Center", "full_url":"pop_up_home:help-center",
                        "sub_categories": [
                            {"sub_page_title": "Buying", "sub_category_url": "pop_up_home:buying-help"},
                            {"sub_page_title": "Selling", "sub_category_url": "pop_up_home:selling-help"},
                            {"sub_page_title": "My Account", "sub_category_url": "pop_up_home:account-help"},
                            {"sub_page_title": "Shipping and Tracking", "sub_category_url": "pop_up_home:shipping-help"},
                            {"sub_page_title": "Payment Options", "sub_category_url": "pop_up_home:payment-help"},
                            {"sub_page_title": "Fees", "sub_category_url": "pop_up_home:fees-help"},
                         ]},
                        {"sub_page_title": "Site Map", "full_url":"pop_up_home:site-map"},
                        {"sub_page_title": "Terms and Conditions", "full_url":"pop_up_home:terms"},
                        {"sub_page_title": "Privacy Policy", "full_url":"pop_up_home:privacy"},
                        {"sub_page_title": "Privacy Choices", "full_url":"pop_up_home:privacy_choices"},
                    ]
                 },
                {"title": "Products", "full_url":"pop_up_auction:products"},
                {"title": "Auction", "full_url":"pop_up_home:home"},
                {"title": "Coming Soon", "full_url":"pop_up_home:home"},
                {"title": "Future Releases", "full_url":"pop_up_home:home"},
                {"title": "Cart", "full_url":"pop_up_home:home"}
            ]
        }
    ]

}

TERMS_AND_CONDITIONS_COPY = {
    "page_title": "Terms and Conditions",
    "page_update_title": "Last Updated",
    "page_update_date": "January 1, 2025",
    "sections": [
        { "section_paragraph": [
            {"class":"", "paragraph": f"These are the terms and conditions of use for https://thepopup.com/ (\"Site\"). The Site is operated by The Pop Up, LLC of 430 Lexington Avenue Brooklyn, NY 11221 USA (The Pop Up,” “we,” “us”, or “our”) and is a live marketplace that allows users to research, buy and sell certain consumer goods. These Terms and Conditions of Use, our Marketplace FAQs (the “FAQS”), and all other requirements posted on our websites, all of which are incorporated into these Terms and Conditions of Use by reference and as amended from time to time (collectively, “Terms”) describe the terms and conditions on which we provide our websites (the “Sites”), services, data, software, applications (including mobile applications) and tools (collectively “Services”) to you, whether as a guest or a registered user."},
            {"class":"", "paragraph": "Your use of the Sites and Services will be subject to these Terms and by using them you agree to be bound by them. These Terms create a legal contract between you and us. Please read them carefully. We will collect and process personal data in accordance with our Privacy Policy https://thepopup.com/privacy."},
            {"class":"bold", "paragraph": "By using our Sites and Services, or by clicking to accept these Terms, you accept and agree to be bound and abide by these Terms in full. If you do not agree to these Terms, do not use our Sites or any portion of the Services. For all purposes, the English version of the Terms shall be the original, binding instrument and understanding of the parties. In the event of any conflict between the English version of the Terms and any translation into any other language, the English version shall prevail and control."},
            ]
        },
        
    ]
}

PRIVACY_POLICY_COPY = {
    "page_title": "The Pop Up Privacy Policy",
    "page_update_title": "Last Updated",
    "page_update_date": "January 1, 2025",
    "sections": [
        { "section_paragraph": [
            {"class":"", "paragraph": "The Pop Up (The Pop Up) values its users' privacy. This Privacy Policy (\"Policy\") will help you understand how we collect and use personal information from those who visit our website or make use of our online facilities and services, and what we will and will not do with the information we collect. Our Policy has been designed and created to ensure those affiliated with The Pop Up of our commitment and realization of our obligation not only to meet, but to exceed, most existing privacy standards."},
            {"class":"", "paragraph": "We reserve the right to make changes to this Policy at any given time. If you want to make sure that you are up to date with the latest changes, we advise you to frequently visit this page. If at any point in time The Pop Up decides to make use of any personally identifiable information on file, in a manner vastly different from that which was stated when this information was initially collected, the user or users shall be promptly notified by email. Users at that time shall have the option as to whether to permit the use of their information in this separate manner."},
            {"class":"bold", "paragraph": "This Policy applies to The Pop Up, and it governs any and all data collection and usage by us. Through the use of thepopup.com, you are therefore consenting to the data collection procedures expressed in this Policy."},
            {"class":"bold", "paragraph": "Please note that this Policy does not govern the collection and use of information by companies that The Pop Up does not control, nor by individuals not employed or managed by us. If you visit a website that we mention or link to, be sure to review its privacy policy before providing the site with information. It is highly recommended and suggested that you review the privacy policies and statements of any website you choose to use or frequent to better understand the way in which websites garner, make use of and share the information collected."},
            ]
        },
        
    ],
    "ordered_list_sections_one": [
        {"section_paragraph": "Specifically, this Policy will inform you of the following",
    "ordered_list_one": [
        {"list_item": "What personally identifiable information is collected from you through our website;"},
        {"list_item": "Why we collect personally identifiable information and the legal basis for such collection;"},
        {"list_item": "How we use the collected information and with whom it may be shared;"},
        {"list_item": "What choices are available to you regarding the use of your data; and"},
        {"list_item": "The security procedures in place to protect the misuse of your information."},
    ],
        },
        
    ],
    "information_collect_sections": [
        {"section_title": "Information We Collect",
        "section_paragraph": [
            {"paragraph": "It is always up to you whether to disclose personally identifiable information to us, although if you elect not to do so, we reserve the right not to register you as a user or provide you with any products or services. This website collects various types of information, such as:"},
            ],
        "section_paragraph_two": [
            {"paragraph": "In addition, The Pop Up may have the occasion to collect non-personal anonymous demographic information, such as age, gender, household income, political affiliation, race and religion, as well as the type of browser you are using, IP address, or type of operating system, which will assist us in providing and maintaining superior quality service."},
            {"paragraph": "The Pop Up may also deem it necessary, from time to time, to follow websites that our users may frequent to gleam what types of services and products may be the most popular to customers or the general public. "},
            ],
        "section_list": [
            {"label": "Information automatically collected when visiting our website, which may include cookies, third party tracking technologies and server logs."}
        ]
         },
    ],
    "why_we_collect": [
        {"section_title": "Why We Collect Information and For How Long",
        "section_paragraph": [
            {"paragraph": "We are collecting your data for several reasons:"},
            ],
        "section_paragraph_two": [
            {"paragraph": "The data we collect from you will be stored for no longer than necessary. The length of time we retain said information will be determined based upon the following criteria: the length of time your personal information remains relevant; the length of time it is reasonable to keep records to demonstrate that we have fulfilled our duties and obligations; any limitation periods within which claims might be made; any retention periods prescribed by law or recommended by regulators, professional bodies or associations; the type of contract we have with you, the existence of your consent, and our legitimate interest in keeping such information as stated in this Policy."},
            ],
        "section_list": [
            {"label": "To better understand your needs and provide you with the services you have requested;"},
            {"label": "To fulfill our legitimate interest in improving our services and products;"},
            {"label": "To send you promotional emails containing information we think you may like when we have your consent to do so;"},
            {"label": "To contact you to fill out surveys or participate in other types of market research, when we have your consent to do so;"},
            {"label": "To customize our website according to your online behavior and personal preferences."},
        ]
         },
    ],
     "use_of_information": [
        {"section_title": "Use of Information Collected",
        "section_paragraph": [
            {"paragraph": "The Pop Up may collect and may make use of personal information to assist in the operation of our website and to ensure delivery of the services you need and request. At times, we may find it necessary to use personally identifiable information as a means to keep you informed of other possible products and/or services that may be available to you from thepopup.com."},
            {"paragraph": "The Pop Up may also be in contact with you with regards to completing surveys and/or research questionnaires related to your opinion of current or potential future services that may be offered."},
            {"paragraph": "The Pop Up may find it beneficial to all our customers to share specific data with our trusted partners in an effort to conduct statistical analysis, provide you with email and/or postal mail, deliver support and/or arrange for deliveries to be made. Those third parties shall be strictly prohibited from making use of your personal information, other than to deliver those services which you requested, and as such they are required, in accordance with this agreement, to maintain the strictest of confidentiality with regards to all your information."},
            {"paragraph": "The Pop Up uses various third-party social media features including but not limited to Facebook, X, Tumblr, TikTock, Instagram and other interactive programs. These may collect your IP address and require cookies to work properly. These services are governed by the privacy policies of the providers and are not within The Pop Up's control. "},
            ],
         },
    ],
    "disclosure_of_info": [
        {"section_title": "Disclosure of Information",
        "section_paragraph": [
            {"paragraph": "The Pop Up may not use or disclose the information provided by you except under the following circumstances:"},
            ],
        "section_list": [
            {"label": "as necessary to provide services or products you have ordered;"},
            {"label": "in other ways described in this Policy or to which you have otherwise consented;"},
            {"label": "in the aggregate with other information in such a way so that your identity cannot reasonably be determined;"},
            {"label": "as required by law, or in response to a subpoena or search warrant;"},
            {"label": "to outside auditors who have agreed to keep the information confidential;"},
            {"label": "as necessary to enforce the Terms of Service;"},
            {"label": "as necessary to maintain, safeguard and preserve all the rights and property of The Pop Up."},
        ]
         },
    ],
    "non_marketing": [
        {"section_title": "Non-Marketing Purposes",
        "section_paragraph": [
            {"paragraph": "The Pop Up greatly respects your privacy. We do maintain and reserve the right to contact you if needed for non-marketing purposes (such as bug alerts, security breaches, account issues, and/or changes in The Pop Up products and services). In certain circumstances, we may use our website, newspapers, or other public means to post a notice."},
            ],
         },
    ],
    "under_13": [
        {"section_title": "Children under the age of 13",
        "section_paragraph": [
            {"paragraph": "The Pop Up's website is not directed to, and does not knowingly collect personal identifiable information from, children under the age of thirteen (13). If it is determined that such information has been inadvertently collected on anyone under the age of thirteen (13), we shall immediately take the necessary steps to ensure that such information is deleted from our system's database, or in the alternative, that verifiable parental consent is obtained for the use and storage of such information. Anyone under the age of thirteen (13) must seek and obtain parent or guardian permission to use this website."},
            ],
         },
    ],

    "unsubscribe_opt_out": [
        {"section_title": "Unsubscribe or Opt-Out",
        "section_paragraph": [
            {"paragraph": "All users and visitors to our website have the option to discontinue receiving communications from us by way of email or newsletters. To discontinue or unsubscribe from our website please send an email that you wish to unsubscribe to pblackdevdemo@gmail.com. If you wish to unsubscribe or opt-out from any third-party websites, you must go to that specific website to unsubscribe or opt-out. The Pop Up will continue to adhere to this Policy with respect to any personal information previously collected."},
            ],
         },
    ],

    "links_to_other_sites": [
        {"section_title": "Links to Other Websites",
        "section_paragraph": [
            {"paragraph": "Our website does contain links to affiliate and other websites. The Pop Up does not claim nor accept responsibility for any privacy policies, practices and/or procedures of other such websites. Therefore, we encourage all users and visitors to be aware when they leave our website and to read the privacy statements of every website that collects personally identifiable information. This Privacy Policy Agreement applies only and solely to the information collected by our website."},
            ],
         },
    ],

    "european_users": [
        {"section_title": "Notice to European Union Users",
        "section_paragraph": [
            {"paragraph": "The Pop Up's operations are located primarily in the United States. If you provide information to us, the information will be transferred out of the European Union (EU) and sent to the United States. (The adequacy decision on the EU-US Privacy became operational on August 1, 2016. This framework protects the fundamental rights of anyone in the EU whose personal data is transferred to the United States for commercial purposes. It allows the free transfer of data to companies that are certified in the US under the Privacy Shield.) By providing personal information to us, you are consenting to its storage and use as described in this Policy."},
            ],
         },
    ],

    "security": [
        {"section_title": "Security",
        "section_paragraph": [
            {"paragraph": "The Pop Up takes precautions to protect your information. When you submit sensitive information via the website, your information is protected both online and offline. Wherever we collect sensitive information (e.g. credit card information), that information is encrypted and transmitted to us in a secure way. You can verify this by looking for a lock icon in the address bar and looking for \"https\" at the beginning of the address of the webpage."},
            {"paragraph": "While we use encryption to protect sensitive information transmitted online, we also protect your information offline. Only employees who need the information to perform a specific job (for example, billing or customer service) are granted access to personally identifiable information. The computers and servers in which we store personally identifiable information are kept in a secure environment. This is all done to prevent any loss, misuse, unauthorized access, disclosure or modification of the user's personal information under our control."},
            ],
         },
    ],

    "acceptnace_of_terms": [
        {"section_title": "Acceptance of Terms",
        "section_paragraph": [
            {"paragraph": "By using this website, you are hereby accepting the terms and conditions stipulated within the Privacy Policy Agreement. If you are not in agreement with our terms and conditions, then you should refrain from further use of our sites. In addition, your continued use of our website following the posting of any updates or changes to our terms and conditions shall mean that you agree and acceptance of such changes."},
            ],
         },
    ],

    "how_to_contact": [
        {"section_title": "How to Contact Us",
        "section_paragraph": [
            {"paragraph": "If you have any questions or concerns regarding the Privacy Policy Agreement related to our website, please feel free to contact us at the following email, telephone number or mailing address."},
            ],         },
        
    ],
    "telephone_label": "Telephone Number", "phone":"561-729-5153",
    "email_label": "Email", "email":"pblackdevedemo@gmail.com",
    "mailing_label": "Mailing Address", "address":"PO Box 220085 Rosedale, NY 11422",
    
}

PRIVACY_CHOICES_COPY = {
    "page_title": "Your Privacy Choices",
    "section_title" :"Send Opt-Out Email",
    "sections": [
        { "section_paragraph": [
            {"paragraph": "Under applicable U.S. state privacy laws (e.g., California, Colorado, etc.), residents have the right to opt-out of \"sales\" and \"shares\" of personal information, \"targeted advertising,\" and certain use/disclosure of \"sensitive\" personal information. For more information, see our Privacy Policy."},
            {"paragraph": "To opt-out, you must (1) submit the \"Opt-Out Form\" using the link below or email pblackdevdemo@gmail.com with the subject \"Opt-Out of Sales.\""},
            ]
        },     
    ],
    "buttons": [
        { "section_button": [
            {"class":"button_extra_long", "button": "Accept Cookies Targeting"},
            {"class":"button_extra_long", "button": "Opt Out of Cookies Targeting"},
            ]
        },     
    ]
}