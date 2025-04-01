from flask import Flask, render_template, request, session, jsonify
from datetime import datetime
import os
import json
from utils.google_vision import detect_product
from utils.scraping import (
    search_amazon, search_ebay, search_bestbuy, find_cheapest_item,
    get_amazon_product_details, get_bestbuy_product_details, get_ebay_product_details
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Replace with a real secret key
UPLOAD_FOLDER = "uploads"
FAVORITES_FILE = "favorites.json"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize favorites file if it doesn't exist
if not os.path.exists(FAVORITES_FILE):
    with open(FAVORITES_FILE, 'w') as f:
        json.dump({}, f)

def get_user_favorites():
    user_id = session.get('user_id', 'default_user')
    try:
        with open(FAVORITES_FILE, 'r') as f:
            all_favorites = json.load(f)
        return all_favorites.get(user_id, [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_user_favorites(favorites):
    user_id = session.get('user_id', 'default_user')
    try:
        with open(FAVORITES_FILE, 'r') as f:
            all_favorites = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_favorites = {}
    
    all_favorites[user_id] = favorites
    with open(FAVORITES_FILE, 'w') as f:
        json.dump(all_favorites, f, indent=4)

@app.route("/", methods=["GET", "POST"])
def index():
    if 'user_id' not in session:
        session['user_id'] = str(datetime.now().timestamp())

    # Initialize all variables
    results = {"Amazon": [], "eBay": [], "BestBuy": []}
    product_name = detected_label = error_message = None
    suggested_purchase = None
    all_products_sorted = []
    favorites = get_user_favorites()

    if request.method == "POST":
        if request.form.get("product_name"):
            product_name = request.form.get("product_name")
        elif "file" in request.files:
            file = request.files["file"]
            if file.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{file.filename}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                with open(file_path, "rb") as image_file:
                    detected_label = detect_product(image_file.read())
                product_name = detected_label if detected_label != "Unknown Product" else None
                if not product_name:
                    error_message = "No product detected. Please try again or enter a product name."

        if product_name:
            with open(os.path.join(UPLOAD_FOLDER, "search_log.txt"), "a") as log_file:
                log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Query: {product_name}, Detected: {detected_label}\n")

            results["Amazon"] = search_amazon(product_name)
            results["eBay"] = search_ebay(product_name)
            results["BestBuy"] = search_bestbuy(product_name)

            suggested_purchase = find_cheapest_item(results)
            if suggested_purchase:
                # Ensure suggested_purchase has required fields
                suggested_purchase.setdefault('site', 'Unknown')
                suggested_purchase.setdefault('link', '#')
                
                # Get additional details only if we have a valid site
                if 'site' in suggested_purchase and suggested_purchase['site']:
                    details = None
                    try:
                        if suggested_purchase["site"] == "Amazon":
                            details = get_amazon_product_details(suggested_purchase["link"])
                        elif suggested_purchase["site"] == "BestBuy":
                            details = get_bestbuy_product_details(suggested_purchase["link"])
                        elif suggested_purchase["site"] == "eBay":
                            details = get_ebay_product_details(suggested_purchase["link"])
                    except Exception as e:
                        print(f"Error fetching details: {e}")

                    if details:
                        suggested_purchase.update({
                            "description": details.get("description", "No description"),
                            "rating": details.get("rating", "No rating"),
                            "reviews": details.get("reviews", "No reviews")
                        })

                # Set default values for missing fields
                suggested_purchase.setdefault('title', 'Unknown Product')
                suggested_purchase.setdefault('price', 'N/A')
                suggested_purchase.setdefault('thumbnail', '')
                suggested_purchase.setdefault('description', 'No description available')
                suggested_purchase.setdefault('rating', '')
                suggested_purchase.setdefault('reviews', '')
            all_products = []
            for site, products in results.items():
                for product in products:
                    if product.get("price"):
                        price_clean = product["price"].replace("C $", "").replace("$", "").replace(",", "").strip()
                        if price_clean.replace(".", "", 1).isdigit():
                            product["price_clean"] = float(price_clean)
                            product["site"] = site
                            all_products.append(product)

            all_products_sorted = sorted(all_products, key=lambda x: x["price_clean"])

    return render_template(
        "index.html",
        results=results,
        detected_label=detected_label,
        error_message=error_message,
        suggested_purchase=suggested_purchase,
        all_products_sorted=all_products_sorted,
        favorites=favorites
    )

@app.route("/add_favorite", methods=["POST"])
def add_favorite():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    product_data = request.get_json()
    required_fields = ["title", "price", "link"]
    if not all(field in product_data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    favorites = get_user_favorites()
    if not any(fav['link'] == product_data['link'] for fav in favorites):
        favorites.append({
            "title": product_data["title"],
            "price": product_data["price"],
            "link": product_data["link"],
            "thumbnail": product_data.get("thumbnail", ""),
            "site": product_data.get("site", "Unknown"),
            "rating": product_data.get("rating", ""),
            "reviews": product_data.get("reviews", "")
        })
        save_user_favorites(favorites)
    
    return jsonify({"status": "success"})

@app.route("/remove_favorite", methods=["POST"])
def remove_favorite():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    product_link = request.get_json().get("link")
    if not product_link:
        return jsonify({"status": "error", "message": "Missing product link"}), 400

    favorites = get_user_favorites()
    favorites = [fav for fav in favorites if fav["link"] != product_link]
    save_user_favorites(favorites)
    
    return jsonify({"status": "success"})

@app.route("/favorites")
def view_favorites():
    favorites = get_user_favorites()
    return render_template("favorites.html", favorites=favorites)

if __name__ == "__main__":
    app.run(debug=True)