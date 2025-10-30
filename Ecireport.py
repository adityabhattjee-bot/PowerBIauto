import os
import time
import zipfile
import glob
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

# ===========================
# CONFIG
# ===========================
BASE_DIR = os.getcwd()
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
USERNAME = "onboardinguser"
PASSWORD = "Hello@123#"

NAMES_FILE = os.path.join(BASE_DIR, "Names1.csv")

WB_URL = "https://web.onex-aura.com"

# ===========================
# HELPER FUNCTIONS
# ===========================

def login_and_download(playwright, base_url, server_name):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    page.goto(base_url, timeout=60000)

    # Fill login form
    NotLoggedin = True
    page.fill("#email", USERNAME)
    page.fill("#password", PASSWORD)
    page.click("#login_button")

    # Wait for redirect / dashboard
    page.wait_for_load_state("networkidle")
    #  if "dashboard" in page.url:
    #      NotLoggedin = False
    #      print("Logged In")
    #  else:
    #      page.goto(base_url)
    #      retry = retry + 1
          
    # Go to downloads page
    download_page_url = base_url + "/report"
    anal_page = base_url + "/analytics"
    page.goto(download_page_url)
    page.click("#pills-new_latency-report-tab")
    print("clicked Latency")
    page.wait_for_load_state("networkidle")
    page.click("#dropdownMenuLink")
    page.wait_for_load_state("networkidle")
    page.click("#download_csv")
    page.wait_for_load_state("networkidle")
    print("clicked Download")
    page.wait_for_timeout(2000)
    page.goto(download_page_url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    countingretry = 1
    nodownloadlink = True
    while nodownloadlink:
      page.goto(download_page_url)
      page.wait_for_load_state("networkidle")
      page.click("#pills-download-data-tab")
      page.wait_for_load_state("networkidle")
      page.wait_for_timeout(1000)
    
      # Find the newest link (closest to current time)
      links = page.query_selector_all("a[href^='../onex_downloads/csv/latency_report_download']")
      if not links:
          print(f"[{server_name}] ❌ No download links found.")
          countingretry = countingretry + 1
          if countingretry > 5:
            context.close()
            browser.close()
            return None
      else:
          nodownloadlink = False  

    
    # pick the most recent link
    latest_link = links[0]
    href = latest_link.get_attribute("href")

    # Start download
    with page.expect_download() as dl_info:
        page.click(f"a[href='{href}']")
    download = dl_info.value
    download_path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
    download.save_as(download_path)
    print(f"[{server_name}] ✅ Downloaded: {download_path}")

    context.close()
    browser.close()
    return download_path


def unzip_and_rename(zip_path, new_name):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(DOWNLOAD_DIR)
        csv_files = [f for f in zip_ref.namelist() if f.endswith(".csv")]
        if csv_files:
            extracted_csv = os.path.join(DOWNLOAD_DIR, csv_files[0])
            new_csv_path = os.path.join(DOWNLOAD_DIR, new_name)
            os.rename(extracted_csv, new_csv_path)
            print(f"🗂️ Renamed {csv_files[0]} → {new_name}")
            return new_csv_path
    return None


# ===========================
# MAIN SCRIPT
# ===========================
def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    with sync_playwright() as p:
        file1_zip = login_and_download(p, WB_URL, "Server 1")

    if not (file1_zip):
        print("❌ One or both downloads failed. Exiting.")
        return

    csv1 = unzip_and_rename(file1_zip, "summary.csv")

    # Merge the CSVs

    # Inner join with names.csv
    names = pd.read_csv(NAMES_FILE)
    final = pd.merge(names, csv1, on="TUC ID", how="inner")

    # Save final output
    output_path = os.path.join(DOWNLOAD_DIR, "final_report.csv")
    final.to_csv(output_path, index=False)
    print(f"✅ Final report saved to: {output_path}")

    # Clean old zips (optional)
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*.zip")):
        os.remove(f)

    print("🏁 Automation completed successfully!")


if __name__ == "__main__":
    main()
