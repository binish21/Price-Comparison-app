import os
import io
import json
import requests
from flask import Flask, render_template, request
from google.cloud import vision
from google.oauth2 import service_account
from bs4 import BeautifulSoup
from datetime import datetime
from fuzzywuzzy import fuzz

app = Flask(__name__)

# Load Google credentials from environment variable JSON
credentials_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(credentials_info)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# GOOGLE VISION FUNCTION

def detect_product(image_data):
    client = vision.ImageAnnotatorClient(credentials=credentials)
    image = vision.Image(content=image_data)
    web_response = client.web_detection(image=image).web_detection
    web_entities = web_response.web_entities if web_response.web_entities else []
    detected_objects = [entity.description for entity in web_entities if entity.score > 0.5]
    search_term = next((entity for entity in detected_objects if "Echo" in entity or "Dot" in entity or "Show" in entity), None)
    return search_term or (detected_objects[0] if detected_objects else "Unknown Product")


def get_amazon_product_title(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-CA,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title_element = soup.select_one("#productTitle")
        return title_element.get_text(strip=True) if title_element else "Title not found"
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"


def search_amazon(query):
    url = f"https://www.amazon.ca/s?k={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-CA,en;q=0.9",
        "Referer": "https://www.amazon.ca/"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        results = []
        for product in soup.find_all("div", attrs={"data-component-type": "s-search-result"})[:5]:
            link_element = product.find("a", class_="a-link-normal")
            link = "https://www.amazon.ca" + link_element["href"] if link_element else None
            price_element = product.find("span", class_="a-price-whole")
            decimal_price_element = product.find("span", class_="a-price-symbol")
            price = f"{price_element.text.strip()}{decimal_price_element.text.strip()}" if price_element and decimal_price_element else None
            thumbnail_element = product.find("img", class_="s-image")
            thumbnail = thumbnail_element["src"] if thumbnail_element else None
            product_title = get_amazon_product_title(link) if link else "No title found"
            similarity_score = fuzz.token_sort_ratio(query.lower(), product_title.lower())
            results.append({"title": product_title, "link": link, "price": price, "thumbnail": thumbnail, "score": similarity_score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:2]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Amazon CA: {e}")
        return []


def search_ebay(query):
    url = f"https://www.ebay.ca/sch/i.html?_nkw={query.replace(' ', '+')}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for item in soup.select(".s-item")[:5]:
        title = item.select_one(".s-item__title")
        price = item.select_one(".s-item__price")
        link = item.select_one(".s-item__link")
        thumbnail = item.select_one(".s-item__image-wrapper img")
        if title and thumbnail and price and link:
            link_url = link["href"]
            link_response = requests.get(link_url)
            if link_response.status_code == 200:
                similarity_score = fuzz.token_sort_ratio(query.lower(), title.text.lower())
                results.append({"title": title.text, "price": price.text, "link": link_url, "thumbnail": thumbnail["src"], "score": similarity_score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:2]


def search_bestbuy(query):
    url = f"https://www.bestbuy.ca/api/v2/json/search?query={query.replace(' ', '+')}&page=1&pageSize=5"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-CA,en;q=0.9",
        "Referer": "https://www.bestbuy.ca/",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        results = []
        for product in data.get("products", [])[:2]:
            title = product.get("name", "No title found")
            price = product.get("salePrice", "Price not found")
            link = f"https://www.bestbuy.ca{product.get('productUrl', '')}"
            thumbnail = product.get("thumbnailImage", "")
            results.append({"title": title, "price": f"${price}" if isinstance(price, (int, float)) else price, "link": link, "thumbnail": thumbnail})
        return results
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from BestBuy CA: {e}")
        return []


def find_cheapest_item(results):
    all_products = []
    for site, products in results.items():
        for product in products:
            price = product["price"].replace("$", "").replace(",", "")
            if price.replace(".", "").isdigit():
                product["price_clean"] = float(price)
                all_products.append(product)
    if all_products:
        return min(all_products, key=lambda x: x["price_clean"])
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    results = {"Amazon": [], "eBay": [], "BestBuy": []}
    product_name = None
    detected_label = None
    error_message = None
    suggested_purchase = None
    all_products_sorted = []

    if request.method == "POST":
        if request.form.get("product_name"):
            product_name = request.form.get("product_name")
        elif "file" in request.files:
            file = request.files["file"]
            if file.filename != "":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{file.filename}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                with open(file_path, "rb") as image_file:
                    image_data = image_file.read()
                detected_label = detect_product(image_data)
                if detected_label == "Unknown Product":
                    error_message = "No product detected. Please try again or enter a product name manually."
                else:
                    product_name = detected_label

        if product_name:
            log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Query: {product_name}, Detected: {detected_label}\n"
            with open(os.path.join(UPLOAD_FOLDER, "search_log.txt"), "a") as log_file:
                log_file.write(log_entry)
            results["Amazon"] = search_amazon(product_name)
            results["eBay"] = search_ebay(product_name)
            results["BestBuy"] = search_bestbuy(product_name)
            suggested_purchase = find_cheapest_item(results)
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


if __name__ == "__main__":
    app.run(debug=True)
