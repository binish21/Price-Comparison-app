# Price Comparison App

This is a Flask-based web app that allows users to compare product prices from **Amazon, eBay, and BestBuy**.  
It also supports **image-based product recognition** using Google Vision API.

---

## 🚀 How to Run Locally

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/binish21/Price-Comparison-app.git
cd Price-Comparison-App
```

### 2️⃣ Create a Virtual Environment (Recommended)
```bash
python -m venv venv
```
Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up Google Cloud Vision (Important)
1. Get your **Google API Key** from [Google Cloud Console](https://console.cloud.google.com/).
2. Download the `google_credentials.json` file.
3. Place it inside the project folder.
4. Set up environment variable inside Python:
```python
link your api key file with correct path eg : /user/path/to/key.json
GOOGLE_APPLICATION_CREDENTIALS = "google_credentials.json"
```

### 5️⃣ Run the App
```bash
python app.py
```
Go to `http://127.0.0.1:5000/` in your browser.  

### 6️⃣ (Optional) Deploy on Cloud  
To make it live, consider **deploying on platforms like Render, Vercel, or Railway**.

---

## 📂 Project Structure
```
PriceComparisonApp/
│── app.py                  # Main Flask application
│── templates/               # HTML templates (if any)
│── static/                  # Static files (CSS, JS, images)
│── uploads/                 # For storing uploaded images
│── requirements.txt         # All dependencies
│── .gitignore               # Ignore unnecessary files
│── README.md                # Documentation for setup
│── venv/                    # (if using a virtual environment - should be ignored in Git)
│── google_credentials.json  # Google API key 
```

---


