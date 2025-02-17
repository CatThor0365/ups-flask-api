from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)

# UPS Credentials (Replace with real credentials)
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
TOKEN_URL = "https://onlinetools.ups.com/security/v1/oauth/token"

# Global variables for token storage
UPS_ACCESS_TOKEN = None
TOKEN_EXPIRATION = 0

def get_ups_access_token():
    """Fetch and refresh UPS OAuth token."""
    global UPS_ACCESS_TOKEN, TOKEN_EXPIRATION
    if UPS_ACCESS_TOKEN and time.time() < TOKEN_EXPIRATION:
        return UPS_ACCESS_TOKEN  # Return valid token

    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )

    if response.status_code == 200:
        token_data = response.json()
        UPS_ACCESS_TOKEN = token_data["access_token"]
        TOKEN_EXPIRATION = time.time() + token_data["expires_in"] - 60
        return UPS_ACCESS_TOKEN
    else:
        raise Exception("Failed to obtain UPS access token")

@app.route("/get_shipping_rates", methods=["POST"])
def get_ups_shipping_rates():
    """Fetch UPS shipping rates based on provided details."""
    access_token = get_ups_access_token()
    data = request.json
    origin_zip = data.get("origin_zip")
    destination_zip = data.get("destination_zip")
    weight_lbs = data.get("weight_lbs")

    RATE_URL = "https://onlinetools.ups.com/api/rating/v1/Rate"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}

    rate_request_payload = {
        "RateRequest": {
            "Shipment": {
                "Shipper": {"Address": {"PostalCode": origin_zip, "CountryCode": "US"}},
                "Recipient": {"Address": {"PostalCode": destination_zip, "CountryCode": "US"}},
                "Package": [{
                    "PackagingType": {"Code": "02"},
                    "PackageWeight": {"Weight": str(weight_lbs), "UnitOfMeasurement": {"Code": "LBS"}}
                }]
            }
        }
    }

    response = requests.post(RATE_URL, headers=headers, json=rate_request_payload)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to retrieve UPS rates", "details": response.json()}), 400

@app.route("/get_tracking_info", methods=["POST"])
def get_ups_tracking_info():
    """Fetch UPS tracking info based on a tracking number."""
    access_token = get_ups_access_token()
    data = request.json
    tracking_number = data.get("tracking_number")

    TRACKING_URL = f"https://onlinetools.ups.com/api/track/v1/details/{tracking_number}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}

    response = requests.get(TRACKING_URL, headers=headers)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to retrieve UPS tracking info", "details": response.json()}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
