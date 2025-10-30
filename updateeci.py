import requests
import os

# -------------------------------------------------------------
# 1. Get Access Token
# -------------------------------------------------------------
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
    token_data = response.json()
    return token_data["access_token"]

# -------------------------------------------------------------
# 2. Delete file from OneDrive (if exists)
# -------------------------------------------------------------
def delete_onedrive_file(access_token, file_path):
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{file_path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"🗑️ Deleted existing file: {file_path}")
    elif response.status_code == 404:
        print(f"⚠️ File not found (nothing to delete): {file_path}")
    else:
        print(f"❌ Error deleting file: {response.text}")
        response.raise_for_status()

# -------------------------------------------------------------
# 3. Rename/Move file in OneDrive
# -------------------------------------------------------------
def rename_onedrive_file(access_token, old_path, new_path):
    move_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{old_path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "parentReference": {"path": "/drive/root:" + os.path.dirname("/" + new_path)},
        "name": os.path.basename(new_path)
    }
    response = requests.patch(move_url, headers=headers, json=payload)
    if response.status_code in (200, 201, 204):
        print(f"✅ Renamed '{old_path}' → '{new_path}' successfully.")
    elif response.status_code == 404:
        print(f"⚠️ File '{old_path}' not found — skipping rename.")
    else:
        print(f"❌ Error renaming file: {response.text}")
        response.raise_for_status()

# -------------------------------------------------------------
# 4. Upload file to OneDrive
# -------------------------------------------------------------
def upload_to_onedrive(access_token, file_path, drive_path):
    upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{drive_path}:/content"
    headers = {"Authorization": f"Bearer {access_token}"}

    with open(file_path, "rb") as f:
        response = requests.put(upload_url, headers=headers, data=f)
    response.raise_for_status()

    uploaded_info = response.json()
    print(f"✅ Uploaded '{uploaded_info['name']}' successfully at {uploaded_info['lastModifiedDateTime']}")

# -------------------------------------------------------------
# 5. Main
# -------------------------------------------------------------
if __name__ == "__main__":
    CLIENT_ID = os.environ["CLIENT_ID"]
    CLIENT_SECRET = os.environ["CLIENT_SECRET"]
    REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)

    local_file = "/home/runner/work/PowerBIauto/PowerBIauto/downloads/final_report.csv"
    folder = "Reports"
    newreport = f"{folder}/newreport.csv"
    oldreport = f"{folder}/oldreport.csv"

    # Step 1: Delete oldreport if exists
    delete_onedrive_file(access_token, oldreport)

    # Step 2: Rename newreport → oldreport
    rename_onedrive_file(access_token, newreport, oldreport)

    # Step 3: Upload new output file as newreport
    if os.path.exists(local_file):
        upload_to_onedrive(access_token, local_file, newreport)
