import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz




HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "en-CA,en;q=0.9"
}


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
         

def fetch_product_details(url, selectors):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        details = {}
        for key, selector in selectors.items():
            element = soup.select_one(selector)
            details[key] = element.get_text(strip=True) if element else f"{key.capitalize()} not found"
        return details
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching data: {e}"}

def get_amazon_product_details(url):
    selectors = {
        "title": "#productTitle",
        "price": ".a-price .a-offscreen",
        "description": "#productDescription",
        "rating": ".a-icon-star .a-icon-alt",
        "reviews": "#acrCustomerReviewText"
    }
    return fetch_product_details(url, selectors)

def get_bestbuy_product_details(url):
    selectors = {
        "title": ".sku-title",
        "price": ".priceView-hero-price .priceView-customer-price",
        "description": ".product-description",
        "rating": ".c-ratings-reviews .ugc-ratings-reviews",
        "reviews": ".c-ratings-reviews .ugc-ratings-reviews"
    }
    return fetch_product_details(url, selectors)

def get_ebay_product_details(url):
    selectors = {
        "title": ".x-item-title__mainTitle",
        "price": ".x-price-primary",
        "description": ".item-description",
        "rating": ".review-item-header .review-item-stars",
        "reviews": ".review-item-header .review-item-stars"
    }
    return fetch_product_details(url, selectors)

def search_amazon(query):
    url = f"https://www.amazon.ca/s?k={query.replace(' ', '+')}"
    try:
        response = requests.get(url, headers=HEADERS)
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
            # Get the embedding for the product title
            

            # Compute cosine similarity between the query and product title
            similarity_score = fuzz.token_sort_ratio(query.lower(), product_title.lower())

            # Use a threshold (e.g., 0.7) to filter results
            if similarity_score >= 0.7:
                results.append({
                    "title": product_title,
                    "link": link,
                    "price": price,
                    "thumbnail": thumbnail,
                    "score": similarity_score
                })

        # Sort results by similarity score (descending)
        print("amazon result",results)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:2]  # Return only the top 3 most relevant items
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Amazon CA: {e}")
        return []

def search_ebay(query):
    url = f"https://www.ebay.ca/sch/i.html?_nkw={query.replace(' ', '+')}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for item in soup.select(".s-item")[:5]:
            title = item.select_one(".s-item__title")
            price = item.select_one(".s-item__price")
            link = item.select_one(".s-item__link")
            thumbnail = item.select_one(".s-item__image-wrapper img")
            if title and price and link and thumbnail and "ebay.ca/itm/" in link["href"]:
                price_text = price.text.strip().split("to")[0].strip()
                price_clean = price_text.replace("C $", "").replace("$", "").replace(",", "")
                try:
                    price_clean = float(price_clean)
                except ValueError:
                    price_clean = None
                similarity_score = fuzz.token_sort_ratio(query.lower(), title.text.lower())
                if similarity_score >= 50 and price_clean is not None:
                    results.append({
                        "title": title.text,
                        "price": price_text,
                        "price_clean": price_clean,
                        "link": link["href"],
                        "thumbnail": thumbnail["src"],
                        "score": similarity_score,
                    })
        print("ebay",results)
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from eBay CA: {e}")
        return []

def search_bestbuy(query):
    url = f"https://www.bestbuy.ca/api/v2/json/search?query={query.replace(' ', '+')}&page=1&pageSize=5"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        results = []

        for product in data.get("products", [])[:2]:
            results.append({
                "title": product.get("name", "No title found"),
                "price": f"${product.get('salePrice', 'Price not found')}" if isinstance(product.get("salePrice"), (int, float)) else product.get("salePrice", "Price not found"),
                "link": f"https://www.bestbuy.ca{product.get('productUrl', '')}",
                "thumbnail": product.get("thumbnailImage", "")
                
            })
        return results
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from BestBuy CA: {e}")
        return []

def find_cheapest_item(results):
    all_products = []
    for site, products in results.items():
        for product in products:
            price = product.get("price")  # Use .get() to avoid KeyError
            if price:  # Check if price exists and is not empty
                # Clean the price (remove currency symbols and commas)
                price_clean = price.replace("C $", "").replace("$", "").replace(",", "").strip()
                if price_clean.replace(".", "").isdigit():  # Check if price is a valid number
                    product["price_clean"] = float(price_clean)
                    all_products.append(product)

    # Return the item with the minimum price_clean if any valid products exist
    return min(all_products, key=lambda x: x["price_clean"]) if all_products else None