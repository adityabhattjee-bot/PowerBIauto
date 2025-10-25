import requests
import os

def get_access_token(client_id, client_secret, refresh_token):
    token_url = "https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "offline_access Files.ReadWrite"
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def upload_to_onedrive(access_token, file_path, target_name):
    # Upload to root of OneDrive (you can modify the path)
    upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{target_name}:/content"
    headers = {"Authorization": f"Bearer {access_token}"}

    with open(file_path, "rb") as f:
        r = requests.put(upload_url, headers=headers, data=f)
    r.raise_for_status()
    print("✅ File uploaded:", r.json()["name"])

if __name__ == "__main__":
    CLIENT_ID = os.environ["CLIENT_ID"]
    CLIENT_SECRET = os.environ["CLIENT_SECRET"]
    REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    upload_to_onedrive(access_token, "server1_records.csv", "server1_records.csv")
