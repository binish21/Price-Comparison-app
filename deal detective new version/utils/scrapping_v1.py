import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

def get_amazon_product_details(url):
    """Fetches the product details from an Amazon.ca product page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-CA,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Product title
        title_element = soup.select_one("#productTitle")
        title = title_element.get_text(strip=True) if title_element else "Title not found"

        # Product price
        price_element = soup.select_one(".a-price .a-offscreen")
        price = price_element.get_text(strip=True) if price_element else "Price not found"

        # Product description
        description_element = soup.select_one("#productDescription")
        description = description_element.get_text(strip=True) if description_element else "Description not found"

        # Product rating
        rating_element = soup.select_one(".a-icon-star .a-icon-alt")
        rating = rating_element.get_text(strip=True) if rating_element else "Rating not found"

        # Product reviews
        reviews_element = soup.select_one("#acrCustomerReviewText")
        reviews = reviews_element.get_text(strip=True) if reviews_element else "Reviews not found"

        return {
            "title": title,
            "price": price,
            "description": description,
            "rating": rating,
            "reviews": reviews
        }

    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

def get_bestbuy_product_details(url):
    """Fetches the product details from a BestBuy.ca product page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-CA,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Product title
        title_element = soup.select_one(".sku-title")
        title = title_element.get_text(strip=True) if title_element else "Title not found"

        # Product price
        price_element = soup.select_one(".priceView-hero-price .priceView-customer-price")
        price = price_element.get_text(strip=True) if price_element else "Price not found"

        # Product description
        description_element = soup.select_one(".product-description")
        description = description_element.get_text(strip=True) if description_element else "Description not found"

        # Product rating
        rating_element = soup.select_one(".c-ratings-reviews .ugc-ratings-reviews")
        rating = rating_element.get_text(strip=True) if rating_element else "Rating not found"

        # Product reviews
        reviews_element = soup.select_one(".c-ratings-reviews .ugc-ratings-reviews")
        reviews = reviews_element.get_text(strip=True) if reviews_element else "Reviews not found"

        return {
            "title": title,
            "price": price,
            "description": description,
            "rating": rating,
            "reviews": reviews
        }

    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

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

    price_text = price.text if price else "0"  # Default to "0" if price missing
    price_clean = "".join(filter(lambda x: x.isdigit() or x == ".", price_text))  # Extract only digits and dot
    if price_clean:
        product_price = float(price_clean)
    else:
        product_price = 0  # Default value if price is invalid

    if similarity_score >= 50:
        results.append({
        "title": title.text, "price": f"${product_price:.2f}",
        "link": link_url, "thumbnail": thumbnail["src"], "score": similarity_score
    })

            
    
    # Sort results by similarity score (descending) and return top 2
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:2]  # Return only the top 2 most relevant items

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

def find_cheapest_item(results):
    all_products = []
    for site, products in results.items():
        for product in products:
            # Clean the price (remove $ and commas)
            price = product["price"].replace("$", "").replace(",", "") if product["price"] else "0"
            if price.replace(".", "").isdigit():  # Check if price is a valid number
                product["price_clean"] = float(price)
                all_products.append(product)

    # Find the cheapest item
    if all_products:
        cheapest_item = min(all_products, key=lambda x: x["price_clean"])
        return cheapest_item
    return None