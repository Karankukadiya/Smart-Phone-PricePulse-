import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from datetime import datetime

data = []

headers = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URL = "https://www.flipkart.com"

# ----------------------------
# Helper Functions
# ----------------------------

def clean_price(price):
    if price:
        return re.sub(r"[₹,]", "", price)
    return None


def extract_reviews(review_text):
    if review_text:
        numbers = re.findall(r'[\d,]+', review_text)

        rating_count = numbers[0] if len(numbers) > 0 else None
        review_count = numbers[1] if len(numbers) > 1 else None

        return rating_count, review_count

    return None, None


def extract_specs(specs_list):

    ram = None
    rom = None
    battery = None
    processor = None
    display = None
    camera = None
    network = None

    for spec in specs_list:

        spec_lower = spec.lower()

        # RAM / ROM
        if "ram" in spec_lower and "rom" in spec_lower:
            parts = spec.split("|")

            if len(parts) >= 2:
                ram = parts[0].strip()
                rom = parts[1].strip()

        # Display
        elif "display" in spec_lower:
            display = spec

        # Camera
        elif "camera" in spec_lower:
            camera = spec

        # Battery
        elif "battery" in spec_lower:
            battery = spec

        # Processor
        elif "processor" in spec_lower:
            spec = str(spec)

            # Remove line breaks
            spec = spec.replace("\n", " ")

            # Remove extra processor details
            processor = spec.split("Max clock speed")[0].strip()

        # Network
        if "5g" in spec_lower:
            network = "5G"

        elif "4g" in spec_lower:
            network = "4G"

    return ram, rom, battery, processor, display, camera, network


# ----------------------------
# Scraping
# ----------------------------

empty_pages = 0
for page in range(1, 100):

    url = f"https://www.flipkart.com/search?q=smart+phones&page={page}"

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    products = soup.find_all("div", class_="jIjQ8S")

    print(f"Page {page} -> {len(products)} products")

    if not products:
        empty_pages += 1
        print(f"Empty page count: {empty_pages}")

        if empty_pages >= 3:
            print("3 continuous empty pages found. Stopping scraper.")
            break

        continue

        empty_pages = 0

    for product in products:

        # Product Name
        name_tag = product.find("div", class_="RG5Slk")
        name = name_tag.text.strip() if name_tag else None

        # Brand
        brand = name.split()[0] if name else None

        # Price
        price_tag = product.find("div", class_="hZ3P6w DeU9vF")
        price = clean_price(price_tag.text) if price_tag else None

        # Original Price
        original_price_tag = product.find("div", class_="kRYCnD gxR4EY")
        original_price = clean_price(original_price_tag.text) if original_price_tag else None

        # Discount
        discount_tag = product.find("div", class_="HQe8jr")
        discount = discount_tag.text.strip() if discount_tag else None

        # Rating
        rating_tag = product.find("div", class_="MKiFS6")
        rating = rating_tag.text.strip() if rating_tag else None

        # Reviews
        review_container = product.find("span", class_="PvbNMB")

        rating_count = None
        review_count = None

        if review_container:
            rating_count, review_count = extract_reviews(review_container.text)

        # Specs
        specs = product.find_all("li", class_="DTBslk")

        specs_list = [spec.text.strip() for spec in specs]

        ram, rom, battery, processor, display, camera, network = extract_specs(specs_list)

        # Product URL
        link_tag = product.find("a", class_="k7wcnx")

        product_url = (
            BASE_URL + link_tag["href"]
            if link_tag and link_tag.get("href")
            else None
        )

        # Scraped Date
        scraped_date = datetime.now().strftime("%Y-%m-%d")

        # Append Data
        data.append({
            "Product Name": name,
            "Brand": brand,
            "Price": price,
            "Original Price": original_price,
            "Discount": discount,
            "Rating": rating,
            "Rating Count": rating_count,
            "Review Count": review_count,
            "RAM": ram,
            "ROM": rom,
            "Battery": battery,
            "Processor": processor,
            "Display Size": display,
            "Camera": camera,
            "Network Type": network,
            "Product URL": product_url,
            "Scraped Date": scraped_date
        })

    time.sleep(2)

# ----------------------------
# DataFrame
# ----------------------------

df = pd.DataFrame(data)

df.insert(0, "S.No", range(1, len(df) + 1))

# ----------------------------
# Save CSV
# ----------------------------

path = f"data/Smart_Phones_{datetime.now().strftime('%Y-%m-%d')}.csv"

df.to_csv(path, index=False, encoding="utf-8-sig")

print("\nScraping Completed Successfully")
print(df.head())
print(df.shape)
