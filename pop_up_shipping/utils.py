import requests
from xml.etree import ElementTree as ET

USPS_USER_ID = 'the_user_id'

def get_usps_rate(zip_from, zip_to, pounds=2, ounces=0):
    url = 'https://secure.shippingapis.com/ShippingAPI.dll'
    xml_request = f"""
    <RateV4Request USERID="{USPS_USER_ID}">
    <Revision>2</Revision>
    <Package ID="1ST">
    <Service>PRIORITY</Service>
    <ZipOrigination>{zip_from}</ZipOrigination>
    <ZipOrigination>{zip_to}</ZipOrigination>
    <Pounds>{pounds}</Pounds>
    <Ounces>{ounces}</Ounces>
    <Container>VARIABLE</Container>
            <Size>REGULAR</Size>
            <Machinable>true</Machinable>
        </Package>
    </RateV4Request>
    """

    params = {
        "API": "RateV4", "XML": xml_request
    }

    response = requests.get(url, params=params)
    tree = ET.fromstring(response.content)
    
    try:
        postage = tree.find(".//Postage/Rate")
        if postage is not None:
            return float(postage.text)
        else:
            return None
    except Exception as e:
        print('Error parsing rate:', e)
        return None


rate = get_usps_rate(zip_from="10001", zip_to="90210")
print("Estimated USPS Priority Rate:", rate)