# v-intel
Vehicle Info &amp; Challan Scraper is a Flask-based web application that retrieves detailed vehicle registration (RC) data and pending traffic fines (specifically for Karnataka State). It features AI-powered License Plate Recognition using Google Gemini to extract numbers from images and uses Selenium for automated data scraping.
# 🚗 Vehicle Info & Traffic Challan Scraper

A powerful web application built with **Flask**, **Selenium**, and **Google Gemini AI**. This tool allows users to input a vehicle registration number (manually or via image upload) to scrape detailed ownership information and check for pending traffic violations (Challans).

> **Note:** The challan retrieval module is currently configured for the **Karnataka State Police (KSP)** system.

## ✨ Features

- **📸 AI-Powered OCR:** Upload an image of a car/bike, and the app uses **Google Gemini 2.0 Flash** to extract the license plate number automatically.
- **📄 RC Details Scraping:** Retrieves vehicle details (Owner Name, Fuel Type, Registration Date, etc.) from `carinfo.app`.
- **👮 Challan/Fine Checking:** Fetches pending traffic fines, violation details, and total amounts from the KSP Traffic system.
- **evidence Retrieval:** Extracts and displays links to image/video proof of traffic violations if available.
- **Web Interface:** Clean Flask-based UI to view all data in one place.
- **Local Storage:** Automatically saves retrieved data into local `.txt` files for record-keeping.

## 🛠️ Tech Stack

- **Python 3.x**
- **Flask** (Web Framework)
- **Selenium** (Web Scraping & Automation)
- **Google Generative AI** (Image-to-Text extraction)
- **Requests** (API Endpoints handling)

## ⚙️ Prerequisites

Before running the project, ensure you have the following:

1.  **Google Chrome** installed.
2.  **Google Gemini API Key** (Get it from [Google AI Studio](https://aistudio.google.com/)).
3.  Valid Cookies for scraping (see configuration below).

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/vehicle-challan-scraper.git
    cd vehicle-challan-scraper
    ```

2.  **Install dependencies:**
    ```bash
    pip install flask requests google-generativeai selenium urllib3
    ```

3.  **Project Structure:**
    Ensure your directory looks like this:
    ```text
    /project-root
    │
    ├── app.py                # Main application code
    ├── Genai.key             # File containing your Google API Key
    ├── cookies.json          # Exported cookies for carinfo.app
    ├── templates/
    │   └── index.html        # HTML Frontend
    └── README.md
    ```

## 🔧 Configuration

### 1. Gemini API Key
Create a file named `Genai.key` in the root directory and paste your Google API key inside it (no extra spaces or newlines).

### 2. Cookies Setup (Crucial)
To avoid bot detection, this scraper relies on existing session cookies.

*   **cookies.json:** 
    1. Install a "Cookie Editor" extension in your browser.
    2. Go to `https://www.carinfo.app`.
    3. Export cookies as JSON and save them to `cookies.json` in the project root.
    
*   **Challan Session ID:**
    The code currently uses a hardcoded `JSESSIONID` for the KSP website in the variable `challan_cookie`.
    *   *If the challan search fails:* You may need to visit `https://kspapp.ksp.gov.in`, inspect network requests, grab the `JSESSIONID` from the headers, and update the `challan_cookie` variable in `app.py`.

## 🚀 Usage

1.  Run the Flask application:
    ```bash
    python app.py
    ```

2.  Open your browser and navigate to:
    ```
    http://127.0.0.1:5000/
    ```

3.  **To Use:**
    - **Option A:** Upload an image of a vehicle.
    - **Option B:** Type the vehicle number manually (e.g., `KA01AB1234`).
    - Click Submit.

4.  Wait for the scraping process to finish. The results will be displayed on the screen and saved to `[VehicleNumber].txt`.

## ⚠️ Disclaimer

This tool is intended for **educational purposes only**. 
- Scraping government websites or private platforms may violate their Terms of Service.
- The cookie sessions hardcoded or used in this script may expire and require manual updates.
- Use responsibly and do not flood servers with requests (Rate limiting is handled appropriately in the code).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[MIT License](LICENSE)
