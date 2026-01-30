from flask import Flask, render_template, request
import ast
import os
import json
import time
import requests
import google.generativeai as genai
from selenium import webdriver
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

cookie_file = "cookies.json"
challan_cookie = "PASTE THE JSESSIONID HERE"

dry_run = False

# Configure Gemini API
try:
    with open("Genai.key", "r") as r:
        api_key = r.read().strip()
    genai.configure(api_key=api_key)
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    model = genai.GenerativeModel("gemini-2.0-flash", generation_config=generation_config)
except Exception as e:
    print(f"Warning: Genai key missing or invalid. Image upload will fail. {e}")
    model = None

# Session config
session = requests.Session()
retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

def upload_img(file_content, mime_type=None):
    return genai.upload_file(file_content, mime_type=mime_type)

def extract_vehicle_number(image_file):
    if not model: return "None"
    file = [genai.upload_file(image_file.stream, mime_type="image/jpeg")]
    response = model.generate_content([
        file[0],
        "Extract only the vehicle number from the given image. If you don't see a number, just say 'None'."
    ])
    return response.text.strip().replace(" ", "").replace(",", "\n")

def load_cookies(driver, cookie_file):
    if not os.path.exists(cookie_file):
        print("Cookie file not found.")
        return
    with open(cookie_file, "r") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "sameSite" not in cookie or cookie["sameSite"] not in ["Strict", "Lax", "None"]:
            cookie["sameSite"] = "Lax"
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"❌ Failed to add cookie {cookie.get('name')}: {e}")

def save_data_to_file(data: dict, filename: str):
    with open(filename, "a+", encoding="utf-8") as f:
        for key, value in data.items():
            f.write(f"{key}: {value}\n")

def extract_vehicle_data(driver):
    data = {}
    try:
        time.sleep(5)
        values = driver.find_elements(By.CLASS_NAME, "expand_component_itemSubTitle__ElsYf")
        labels = driver.find_elements(By.CLASS_NAME, "expand_component_itemText__cbigB")
        for label, value in zip(labels, values):
            key = label.text.strip()
            val = value.text.strip()
            data[key] = val
    except Exception as e:
        print(f"Error extracting vehicle data: {e}")
    return data

def main(vehicle_number, output_file):
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--user-agent=Mozilla/5.0")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.carinfo.app")
        time.sleep(3)
        load_cookies(driver, cookie_file)

        vehicle_url = f"https://www.carinfo.app/rc-details/{vehicle_number}"
        driver.get(vehicle_url)
        
        print(f'Extracting {vehicle_number} information please wait a moment...')
        try:
            data = extract_vehicle_data(driver)
        except Exception:
            data = None

        if not data or "login" in driver.current_url:
            print("❌ Extraction failed. Returning 'Cookie Expired'")
            return "Cookie Expired"

        save_data_to_file(data, output_file)
        print(f"✅ Vehicle data saved to {output_file}")
        return "Success"

    except Exception as e:
        print(f"Critical Error: {e}")
        return "Cookie Expired"
    finally:
        if driver:
            driver.quit()

def fetch_challan(vehicle_number):
    url = "https://kspapp.ksp.gov.in/ksp/api/traffic-challan/get-challans"
    params = {'vehicleRegNumber': vehicle_number, 'web': 'true'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Cookie': challan_cookie, 
    }
    print(f'Searching for challans for: {vehicle_number}')
    try:
        response = requests.get(url, headers=headers, params=params)
        with open(f"{vehicle_number}.txt", "a+") as file: # Changed from "+a" to "a+"
            if response.status_code == 200:
                challan = response.json()
                if challan:
                    total_fine = sum(int(item.get('OFFENCE_FINE_AMOUNT', 0)) for item in challan)
                    file.write('\nTraffic Rules violation:\n')
                    for item in challan:
                        file.write(f'{str(item)}\n') 
                    file.write(f"Total Fine Amount: {total_fine}\n") 
                    
                    notice_numbers = [item.get('NOTICE_NUMBER') for item in challan if item.get('NOTICE_NUMBER')]
                    if notice_numbers:
                        for notice_no in notice_numbers:
                            media_urls = extract_proof_urls(vehicle_number, notice_no)
                            if media_urls:
                                file.write(f"\nMedia URLs for Notice No: {notice_no}\n")
                                for key, url in media_urls.items():
                                        file.write(f"{key}: {url}\n")
            else:
                if response.status_code == 403:
                    file.write(f"\nError: Session Expired (403) for Challan API.\n")
                elif response.status_code == 429:
                    file.write("\nError: Rate limit exceeded while fetching challans.\n")
                else:
                    file.write(f"\nError: Failed to retrieve challans, status code: {response.status_code}\n")
    except Exception as e:
        print(f"Error: {e}")

def extract_proof_urls(vehicle_number, notice_no):
    url = "https://kspapp.ksp.gov.in/ksp/api/traffic-challan/get-challan-image"
    params = {"vehicleRegNumber": vehicle_number, "noticeNumber": notice_no}
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json;charset=UTF-8", "Cookie": challan_cookie}
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {
                "ImageURL": data.get("ImageURL", "Not Found"),
                "ZoomedURL": data.get("ZoomedURL", "Not Found"),
                "VideoURL": data.get("VideoURL", "Not Found"),
                "VideoURL2": data.get("VideoURL2", "Not Found"),
            }
        return None
    except Exception:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    vehicle_number = None
    file_content = None
    error_message = None  # New variable to hold error text

    if request.method == "POST":
        if "vehicle_image" in request.files and request.files["vehicle_image"].filename != "":
            image_file = request.files["vehicle_image"]
            vehicle_number = extract_vehicle_number(image_file)
            if vehicle_number and vehicle_number.lower() == "none":
                vehicle_number = None
        elif "vehicle_number" in request.form:
            vehicle_number = request.form["vehicle_number"].strip()
            
        if vehicle_number:
            output_file = f"{vehicle_number}.txt"
            # Ensure fresh start
            if os.path.exists(output_file):
                os.remove(output_file)
            
            # 1. Run Scraper and check status
            scrape_status = main(vehicle_number, output_file) 
            
            if scrape_status == "Cookie Expired":
                error_message = "Warning: Unable to extract RC Details. The system session/cookie has expired."
            
            # 2. Run Challan Fetcher
            fetch_challan(vehicle_number)

            # 3. Read the file
            if os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8") as f:
                    file_content = f.read()

    media_links = {}
    challan_entries = []
    total_fine_amount = None
    vehicle_details = []
    no_challan_message = None

    if file_content:
        lines = file_content.splitlines()
        current_section = "VEHICLE"
        current_notice_for_media = None

        for line in lines:
            line = line.strip()
            if not line: continue

            # Check for Errors written to file
            if line.startswith("Error:"):
                # Append to existing error message or create new one
                if error_message:
                    error_message += " | " + line
                else:
                    error_message = line
                continue

            # Detect Section Changes
            if line == "Traffic Rules violation:":
                current_section = "CHALLAN"
                continue
            if line.startswith("Media URLs for Notice No:"):
                current_section = "MEDIA"
                current_notice_for_media = line.split(":")[-1].strip()
                media_links[current_notice_for_media] = {}
                continue
            if "No challans found for" in line:
                no_challan_message = line
                continue

            # Parse based on section
            if current_section == "VEHICLE":
                vehicle_details.append(line)

            elif current_section == "CHALLAN":
                if line.startswith("Total Fine Amount:"):
                    total_fine_amount = line.split(":")[-1].strip()
                elif line.startswith("{") and line.endswith("}"):
                    try:
                        entry_dict = ast.literal_eval(line)
                        challan_entries.append(entry_dict)
                    except Exception as e:
                        print(f"Error parsing dict line: {e}")

            elif current_section == "MEDIA":
                if ":" in line and current_notice_for_media:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        url = parts[1].strip()
                        media_links[current_notice_for_media][key] = url

    return render_template("index.html", 
                           vehicle_number=vehicle_number, 
                           vehicle_details=vehicle_details, 
                           no_challan_message=no_challan_message, 
                           media_links=media_links, 
                           challan_entries=challan_entries, 
                           total_fine_amount=total_fine_amount,
                           error_message=error_message) # Pass error message

if __name__ == "__main__":
    app.run(debug=True)
