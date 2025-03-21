from flask import Flask, render_template, request
from datetime import datetime
import os
from utils.google_vision import detect_product
from utils.scraping import (
    search_amazon, search_ebay, search_bestbuy, find_cheapest_item,
    get_amazon_product_details, get_bestbuy_product_details, get_ebay_product_details
)

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    results = {"Amazon": [], "eBay": [], "BestBuy": []}
    product_name = detected_label = error_message = suggested_purchase = None
    all_products_sorted = []

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
                    error_message = "No product detected in the image. Please try again or enter a product name manually."

        if product_name:
            with open(os.path.join(UPLOAD_FOLDER, "search_log.txt"), "a") as log_file:
                log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Query: {product_name}, Detected: {detected_label}\n")

            results["Amazon"] = search_amazon(product_name)
            results["eBay"] = search_ebay(product_name)
            results["BestBuy"] = search_bestbuy(product_name)

            suggested_purchase = find_cheapest_item(results)

            all_products = []
            for site, products in results.items():
                for product in products:
                    price = product.get("price")
                    if price:
                        price_clean = price.replace("C $", "").replace("$", "").replace(",", "").strip()
                        if price_clean.replace(".", "").isdigit():
                            product["price_clean"] = float(price_clean)
                            product["site"] = site
                            all_products.append(product)

            all_products_sorted = sorted(all_products, key=lambda x: x["price_clean"])

            if suggested_purchase:
                details = None
                if "site" in suggested_purchase:
                    if suggested_purchase["site"] == "Amazon":
                     details = get_amazon_product_details(suggested_purchase["link"])
                    elif suggested_purchase["site"] == "BestBuy":
                     details = get_bestbuy_product_details(suggested_purchase["link"])
                    elif suggested_purchase["site"] == "eBay":
                     details = get_ebay_product_details(suggested_purchase["link"])

                    if details:
                     suggested_purchase.update({
                        "description": details.get("description", "Description not found"),
                        "rating": details.get("rating", "Rating not found"),
                        "reviews": details.get("reviews", "Reviews not found")
                    })
                else:
                 print("Warning: 'site' key not found in suggested_purchase.")

    return render_template(
        "index.html",
        results=results,
        detected_label=detected_label,
        error_message=error_message,
        suggested_purchase=suggested_purchase,
        all_products_sorted=all_products_sorted
    )

if __name__ == "__main__":
    app.run(debug=True)