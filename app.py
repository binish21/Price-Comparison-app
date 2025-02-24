import os
import io
import requests
from flask import Flask, render_template, request
from google.cloud import vision
from google.oauth2 import service_account
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

# Path to your Google Cloud service account JSON key file make sure to mind with forward slash and backward slash while linking
#recomended to be in same directory and use '/' insted of '\'
GOOGLE_CREDENTIALS_PATH = "PATH-TO-JSON-API-FILE.json"

# ✅ Load credentials explicitly
credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH)

# Ensure the uploads folder exists
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# GOOGLE VISION FUNCTION (Integrated with recognize_image logic)
def detect_product(image_data):
    client = vision.ImageAnnotatorClient(credentials=credentials)  # ✅ Use loaded credentials
    image = vision.Image(content=image_data)

    # Web Detection (for detailed product name)
    web_response = client.web_detection(image=image).web_detection
    web_entities = web_response.web_entities if web_response.web_entities else []

    # Extract and filter out web entities with score > 0.5
    detected_objects = [entity.description for entity in web_entities if entity.score > 0.5]

    print("Identified Objects:", detected_objects)

    # Refine search term by selecting a more specific product (e.g., Echo, Dot, etc.)
    search_term = None
    for entity in detected_objects:
        if "Echo" in entity or "Dot" in entity or "Show" in entity:  # More specific identifiers
            search_term = entity
            break

    # If no specific term found, return the first detected object or "Unknown Product"
    return search_term if search_term else detected_objects[0] if detected_objects else "Unknown Product"

# FUNCTION TO GET AMAZON PRODUCT TITLE FROM URL
def get_amazon_product_title(url):
    """Fetches the product title from an Amazon.ca product page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-CA,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Amazon's product title is inside #productTitle ID
        title_element = soup.select_one("#productTitle")
        title = title_element.get_text(strip=True) if title_element else "Title not found"

        return title

    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

# SCRAPING FUNCTION FOR AMAZON
from fuzzywuzzy import fuzz  # For string matching

# SCRAPING FUNCTION FOR AMAZON (Refined to get 2 most relevant items)
def search_amazon(query):
    url = f"https://www.amazon.ca/s?k={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-CA,en;q=0.9",
        "Referer": "https://www.amazon.ca/"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        results = []

        for product in soup.find_all("div", attrs={"data-component-type": "s-search-result"})[:5]:  # Limit to 5 items initially
            # Get link
            link_element = product.find("a", class_="a-link-normal")
            link = "https://www.amazon.ca" + link_element["href"] if link_element else None

            # Get price (whole price and decimals)
            price_element = product.find("span", class_="a-price-whole")
            decimal_price_element = product.find("span", class_="a-price-symbol")  # For decimals
            price = f"{price_element.text.strip()}{decimal_price_element.text.strip()}" if price_element and decimal_price_element else None

            # Get thumbnail URL
            thumbnail_element = product.find("img", class_="s-image")
            thumbnail = thumbnail_element["src"] if thumbnail_element else None

            # Fetch the product title from the product page
            if link:
                product_title = get_amazon_product_title(link)
            else:
                product_title = "No title found"

            # Calculate similarity score between the query and product title
            similarity_score = fuzz.token_sort_ratio(query.lower(), product_title.lower())

            results.append({"title": product_title, "link": link, "price": price, "thumbnail": thumbnail, "score": similarity_score})

        # Sort results by similarity score (descending) and return top 2
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:2]  # Return only the top 2 most relevant items

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Amazon CA: {e}")
        return []

# SCRAPING FUNCTION FOR EBAY (Refined to get 2 most relevant items)
def search_ebay(query):
    url = f"https://www.ebay.ca/sch/i.html?_nkw={query.replace(' ', '+')}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for item in soup.select(".s-item")[:5]:  # Limit to 5 items initially
        title = item.select_one(".s-item__title")
        price = item.select_one(".s-item__price")
        link = item.select_one(".s-item__link")
        thumbnail = item.select_one(".s-item__image-wrapper img")
        

        if title and thumbnail and price and link:
            link_url = link["href"]
             
            # Check if the link is valid
            link_response = requests.get(link_url)
            if link_response.status_code == 200:
                # Calculate similarity score between the query and product title
                similarity_score = fuzz.token_sort_ratio(query.lower(), title.text.lower())
                results.append({"title": title.text, "price": price.text, "link": link_url,"thumbnail": thumbnail["src"], "score": similarity_score})

    # Sort results by similarity score (descending) and return top 2
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:2]  # Return only the top 2 most relevant items


# SCRAPING FUNCTION FOR BESTBUY
import requests
from bs4 import BeautifulSoup

def search_bestbuy(query):
    # BestBuy Canada search URL
    url = f"https://www.bestbuy.ca/api/v2/json/search?query={query.replace(' ', '+')}&page=1&pageSize=5"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-CA,en;q=0.9",
        "Referer": "https://www.bestbuy.ca/",
    }

    try:
        # Send a GET request to the BestBuy API
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        results = []
        for product in data.get("products", [])[:2]:  # Limit to 2 items
            # Extract product details
            title = product.get("name", "No title found")
            price = product.get("salePrice", "Price not found")
            link = f"https://www.bestbuy.ca{product.get('productUrl', '')}"
            thumbnail = product.get("thumbnailImage", "")

            results.append({
                "title": title,
                "price": f"${price}" if isinstance(price, (int, float)) else price,
                "link": link,
                "thumbnail": thumbnail,
            })

        return results

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from BestBuy CA: {e}")
        return []

# Add this function to find the cheapest item
def find_cheapest_item(results):
    all_products = []
    for site, products in results.items():
        for product in products:
            # Clean the price (remove $ and commas)
            price = product["price"].replace("$", "").replace(",", "")
            if price.replace(".", "").isdigit():  # Check if price is a valid number
                product["price_clean"] = float(price)
                all_products.append(product)

    # Find the cheapest item
    if all_products:
        cheapest_item = min(all_products, key=lambda x: x["price_clean"])
        return cheapest_item
    return None

# FLASK ROUTES
@app.route("/", methods=["GET", "POST"])
def index():
    results = {"Amazon": [], "eBay": [], "BestBuy": []}
    product_name = None
    detected_label = None
    error_message = None
    suggested_purchase = None
    all_products_sorted = []

    if request.method == "POST":
        # If user enters a product name manually
        if request.form.get("product_name"):
            product_name = request.form.get("product_name")

        # If user uploads an image
        elif "file" in request.files:
            file = request.files["file"]
            if file.filename != "":
                #  Generate a unique filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{file.filename}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                
                #  Save the uploaded file
                file.save(file_path)

                #  Reopen the saved file for Google Vision
                with open(file_path, "rb") as image_file:
                    image_data = image_file.read()
                
                #  Detect product from the image
                detected_label = detect_product(image_data)  
                if detected_label == "Unknown Product":
                    error_message = "No product detected in the image. Please try again or enter a product name manually."
                else:
                    product_name = detected_label  # Use detected object for search

        if product_name:
            # Log the search query and detected product name
            log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Query: {product_name}, Detected: {detected_label}\n"
            with open(os.path.join(UPLOAD_FOLDER, "search_log.txt"), "a") as log_file:
                log_file.write(log_entry)

            # Perform searches
            results["Amazon"] = search_amazon(product_name)
            results["eBay"] = search_ebay(product_name)
            results["BestBuy"] = search_bestbuy(product_name)

            #  Find the cheapest item among all results
            suggested_purchase = find_cheapest_item(results)

            # Combine and sort all products by price
            all_products = []
            for site, products in results.items():
                for product in products:
                    price = product["price"].replace("$", "").replace(",", "")
                    if price.replace(".", "").isdigit():
                        product["price_clean"] = float(price)
                        product["site"] = site  
                        all_products.append(product)

            all_products_sorted = sorted(all_products, key=lambda x: x["price_clean"])

    return render_template(
        "index.html",
        results=results,
        detected_label=detected_label,
        error_message=error_message,
        suggested_purchase=suggested_purchase,
        all_products_sorted=all_products_sorted
    )



# RUN FLASK APP
if __name__ == "__main__":
    app.run(debug=True)
