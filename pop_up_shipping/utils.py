import requests
from datetime import datetime, timedelta, date
from xml.etree import ElementTree as ET

"""
NEED THE FOLLOWING TO USE USPS API
"Authorization is accomplished via the USPS® Customer Onboarding Platform, where Customer Registration 
users may grant applications access to their protected business information. All client applications 
must go through this onboarding process."
"""


USPS_USER_ID = ''

def get_usps_token(client_id, client_secret):
    url = "https://apis.usps.com/oauth/token"
    print('url', url)
    data = {"grant_type": "client_credentials"}
    print('data', data)

    resp = requests.post(url, data=data, auth=(client_id, client_secret))
    print('resp', resp)

    resp.raise_for_status()
    print('resp.raise_for_status()', resp.raise_for_status())

    return resp.json()["access_token"]


def get_usps_rate_json(token, zip_from, zip_to, weight_lbs, length, width, height):
    url = "https://apis-tem.usps.com/prices/v3/base-rates/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "originZIPCode": zip_from,
        "destinationZIPCode": zip_to,
        "weight": weight_lbs,
        "length": length,
        "width": width,
        "height": height,
        "mailClass": "PARCEL_SELECT",
        "processingCategory": "MACHINABLE",
        "destinationEntryFacilityType": "NONE",
        "rateIndicator": "DR",
        "priceType": "COMMERCIAL",
        "accountType": "EPS",
        "accountNumber": "YOUR_ACCOUNT_NUMBER",
        "mailingDate": datetime.date.today().isoformat()
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    total = data.get("totalBasePrice")
    return float(total) if total is not None else None


def get_usps_rate(zip_from, zip_to, weight_lbs=2, length=16, width=8, height=5):
    token = get_usps_token(USPS_CONSUMER_KEY, USPS_SECRET_KEY)
    return get_usps_rate_json(token, zip_from, zip_to, weight_lbs, length, width, height)


rate = get_usps_rate(zip_from="10001", zip_to="90210")
print("Estimated USPS Priority Rate:", rate)


# def get_usps_rate(zip_from, zip_to, pounds=2, ounces=0):
#     url = 'https://secure.shippingapis.com/ShippingAPI.dll'
#     xml_request = f"""
#     <RateV4Request USERID="{USPS_USER_ID}">
#     <Revision>2</Revision>
#     <Package ID="1ST">
#     <Service>PRIORITY</Service>
#     <ZipOrigination>{zip_from}</ZipOrigination>
#     <ZipOrigination>{zip_to}</ZipOrigination>
#     <Pounds>{pounds}</Pounds>
#     <Ounces>{ounces}</Ounces>
#     <Container>VARIABLE</Container>
#             <Size>REGULAR</Size>
#             <Machinable>true</Machinable>
#         </Package>
#     </RateV4Request>
#     """

#     params = {
#         "API": "RateV4", "XML": xml_request
#     }

#     response = requests.get(url, params=params)
#     tree = ET.fromstring(response.content)
    
#     try:
#         postage = tree.find(".//Postage/Rate")
#         if postage is not None:
#             return float(postage.text)
#         else:
#             return None
#     except Exception as e:
#         print('Error parsing rate:', e)
#         return None


# rate = get_usps_rate(zip_from="10001", zip_to="90210")
# print("Estimated USPS Priority Rate:", rate)