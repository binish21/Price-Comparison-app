# Price Comparison App

This is a Flask-based web app that allows users to compare product prices from **Amazon, eBay, and BestBuy**.  
It also supports **image-based product recognition** using Google Vision API.

---

## 🚀 How to Run Locally

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/binish21/Price-Compression-app.git
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
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"
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
│── google_credentials.json  # Google API key (Optional - should NOT be committed)
```

---

## 🚀 Upload to GitHub

1. **Initialize a Git repository (if not done already):**
   ```bash
   git init
   ```
2. **Connect to GitHub (Replace with your repo URL):**
   ```bash
   git remote add origin https://github.com/your-username/PriceComparisonApp.git
   ```
3. **Add and commit your files:**
   ```bash
   git add .
   git commit -m "Initial commit"
   ```
4. **Push the code to GitHub:**
   ```bash
   git push origin main
   ```
   If `main` branch doesn't exist, use:
   ```bash
   git push origin master
   ```

---

## ✅ Summary
- **Ensure `requirements.txt` is ready.**
- **Create a `.gitignore` to exclude unnecessary files.**
- **Add a `README.md` with setup instructions.**
- **Push to GitHub.**
- **Users can clone, install dependencies, and run easily.**  

Now your app is **GitHub-ready!** 🚀
