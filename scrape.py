import os
import re
import time
import requests
import io
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ----------------------------------------------------------------------------
# 1) PROJECT & FOLDER SETTINGS
# ----------------------------------------------------------------------------
project_folder = r"D:\2022\IT_RendsZERFEJLESZTÉS\II_fazis"
os.makedirs(project_folder, exist_ok=True)

image_folder = os.path.join(project_folder, "bikepro_images")
os.makedirs(image_folder, exist_ok=True)

# The site to scrape
base_url = "https://bikepro.hu/alkatresz_001/kerek_elemei_130"
total_pages = 5  # Adjust if multiple pages are needed

# ----------------------------------------------------------------------------
# 2) FALLBACK PROPERTY SETTINGS
# ----------------------------------------------------------------------------
FALLBACK_GYARTO       = "Continental"
FALLBACK_TERMEKCSALAD = "Assess"
FALLBACK_TERMEKKOR    = "..."
FALLBACK_SZIN         = "fekete"

# ----------------------------------------------------------------------------
# 3) SELENIUM SETUP
# ----------------------------------------------------------------------------
service = Service()
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # Uncomment if you want headless mode
driver = webdriver.Chrome(service=service, options=options)

# ----------------------------------------------------------------------------
# 4) HELPER FUNCTIONS
# ----------------------------------------------------------------------------
def download_and_convert_image(url, save_path):
    """Download the image (possibly WEBP) and save as JPEG."""
    if not url:
        return
    if url.startswith("//"):
        url = "https:" + url
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            try:
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                img.save(save_path, format="JPEG", quality=90)
                print("Image downloaded & converted:", save_path)
            except Exception:
                # If PIL cannot open the image, just save raw
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                print("Image saved (no conversion):", save_path)
        else:
            print("Image download error:", url, "status:", resp.status_code)
    except Exception as e:
        print("Error downloading image:", url, e)

def remove_illegal_chars(text):
    """Remove characters invalid for Excel."""
    ILLEGAL_CHARACTERS_RE = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]+')
    if isinstance(text, str):
        return ILLEGAL_CHARACTERS_RE.sub("", text)
    return text

def clean_df(df_):
    for c in df_.columns:
        df_[c] = df_[c].apply(remove_illegal_chars)

# ----------------------------------------------------------------------------
# 5) DATA STRUCTURES
# ----------------------------------------------------------------------------
main_data = []       # Rows for the Main sheet
property_data = []   # Rows for the Property sheet

product_counter = 1
image_counter = 1

# ----------------------------------------------------------------------------
# 6) SCRAPE - LIST PAGES
# ----------------------------------------------------------------------------
for page in range(1, total_pages + 1):
    page_url = base_url if page == 1 else f"{base_url}?page={page}"
    driver.get(page_url)
    print("Listing page loaded:", page_url)
    time.sleep(5)

    # Scroll for dynamic content
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    print(f"Page {page}: scrolling done.")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_boxes = soup.find_all("div", class_="product-snapshot list_div_item")
    print(f"Page {page}: found {len(product_boxes)} product boxes.")

    for box in product_boxes:
        # 1) Basic info from listing
        title_anchor = box.find("a", class_="img-thumbnail-link")
        if not title_anchor:
            continue

        product_url = title_anchor.get("href", "")
        if product_url and not product_url.startswith("http"):
            product_url = "https://bikepro.hu" + product_url
        product_name = title_anchor.get("title", "").strip() or title_anchor.get_text(strip=True)

        listing_img_tag = box.find("img", class_="card-img-top")
        listing_img_url = (
            listing_img_tag.get("data-src")
            if listing_img_tag and listing_img_tag.has_attr("data-src")
            else None
        )

        price_tag = box.find("span", class_="product-price")
        price = price_tag.get_text(strip=True) if price_tag else ""

        # 2) Load product detail page
        driver.get(product_url)
        print("Detail page loaded:", product_url)
        time.sleep(2)

        product_page_source = driver.page_source
        soup_product = BeautifulSoup(product_page_source, "html.parser")

        # Try to click "Tulajdonságok" tab
        try:
            param_tab = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "productparams-tab"))
            )
            param_tab.click()
            time.sleep(1)
        except Exception:
            pass

        # Parse parameter table
        param_soup = BeautifulSoup(driver.page_source, "html.parser")
        param_table = param_soup.find("table", class_="parameter-table")
        found_props = {}

        if param_table:
            rows = param_table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) == 2:
                    raw_key = cols[0].get_text(strip=True)
                    raw_val = cols[1].get_text(strip=True).replace("\xa0", " ")

                    # Convert "Színválaszték" => "szin"
                    if raw_key.lower() == "színválaszték":
                        raw_key = "szin"

                    found_props[raw_key] = raw_val

        # If "Gyártó" not found, check for manufacturer row
        if "Gyártó" not in found_props:
            manuf_row = param_soup.find("tr", class_="product-parameter-row manufacturer-param-row")
            if manuf_row:
                val_td = manuf_row.find("td", class_="param-value manufacturer-param")
                if val_td:
                    brand_span = val_td.find("span", attrs={"itemprop": "brand"})
                    if brand_span:
                        found_props["Gyártó"] = brand_span.get_text(strip=True)

        # Try "Leírás" tab
        try:
            desc_tab = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "productdescriptionnoparameters-tab"))
            )
            desc_tab.click()
            time.sleep(1)
        except Exception:
            pass

        desc_soup = BeautifulSoup(driver.page_source, "html.parser")
        full_description = ""
        desc_container = desc_soup.find("div", id="productdescriptionnoparameters-wrapper")
        if desc_container:
            desc_span = desc_container.find("span", class_="product-desc")
            if desc_span:
                full_description = desc_span.get_text(strip=True)

        if not full_description:
            # Fallback: short description
            short_desc_td = desc_soup.find("td", class_="product-short-description")
            if short_desc_td:
                full_description = short_desc_td.get_text(strip=True)

        # 3) Collect images (only the first one)
        all_images = []
        # a) Possibly from gallery
        gallery_wrapper = desc_soup.find("div", class_="pb-gallery-wrapper") or desc_soup.find("div", class_="gallery")
        if gallery_wrapper:
            first_img = gallery_wrapper.find("img")
            if first_img:
                detail_img_url = first_img.get("data-src") or first_img.get("src")
                if detail_img_url:
                    img_name = f"bikepro_img_{image_counter}.jpg"
                    img_path = os.path.join(image_folder, img_name)
                    download_and_convert_image(detail_img_url, img_path)
                    all_images.append(img_name)
                    image_counter += 1
        # b) Main product image container
        if not all_images:
            product_image_container = soup_product.find("div", id="product-image-container")
            if product_image_container:
                product_image = product_image_container.find("img", class_="product-image-element")
                if product_image:
                    detail_img_url = product_image.get("src")
                    if detail_img_url:
                        img_name = f"bikepro_img_{image_counter}.jpg"
                        img_path = os.path.join(image_folder, img_name)
                        download_and_convert_image(detail_img_url, img_path)
                        all_images.append(img_name)
                        image_counter += 1
        # c) Fallback: use listing image
        if not all_images and listing_img_url:
            img_name = f"bikepro_img_{image_counter}.jpg"
            fallback_path = os.path.join(image_folder, img_name)
            download_and_convert_image(listing_img_url, fallback_path)
            all_images.append(img_name)
            image_counter += 1

        # 4) Video check
        video_url = ""
        detail_video_tag = desc_soup.find("video")
        if detail_video_tag and detail_video_tag.get("src"):
            video_url = detail_video_tag.get("src")
        else:
            iframe_tag = desc_soup.find("iframe")
            if iframe_tag and "youtube" in iframe_tag.get("src", "").lower():
                video_url = iframe_tag.get("src")

        # 5) SKU/SLUG start with ALK
        sku = f"ALK{product_counter:04d}"
        slug = sku.lower()
        product_counter += 1

        # 6) Ensure fallback properties if missing
        if "Gyártó" not in found_props:
            found_props["Gyártó"] = FALLBACK_GYARTO
        if "Termékcsalád" not in found_props:
            found_props["Termékcsalád"] = FALLBACK_TERMEKCSALAD
        if "Termékkör" not in found_props:
            found_props["Termékkör"] = FALLBACK_TERMEKKOR
        if "szin" not in found_props:
            found_props["szin"] = FALLBACK_SZIN

        # 7) Build main row
        manufacturer = found_props.get("Gyártó", "")
        product_type = f"méret: {found_props.get('Kerékméret', '')}, szín: {found_props.get('szin', '')}"
        main_row = {
            "SLUG": slug,
            "Active": "YES",
            "Featured": "NO",
            "SKU": sku,
            "Name": product_name,
            "Product Type": product_type,
            "MSRP": "0,00 Ft",
            "Cost": "0,00 Ft",
            "Price": price,
            "Manufacturer": manufacturer,
            "Vendor": "",
            "Image": all_images[0] if all_images else "",
            "Description": full_description,
            "Search Keywords": "",
            "Meta Title": "",
            "Meta Description": "",
            "Meta Keywords": "",
            "Tax Schedule": "",
            "Tax Exempt": "NO",
            "Weight": "0,0000000000",
            "Length": "0,0000000000",
            "Width": "0,0000000000",
            "Height": "0,0000000000",
            "Extra Ship Fee": "0,00 Ft",
            "Ship Mode": "ShipFromSite",
            "Non-Shipping Product": "NO",
            "Ships in a Separate Box": "NO",
            "Allow Reviews": "YES",
            "Minimum Qty": "0",
            "Inventory Mode": "AlwayInStock",
            "Inventory": "0",
            "Stock Out at": "0",
            "Low Stock at": "0",
            "Roles": "",
            "Searchable": "YES",
            "AllowUpcharge": "NO",
            "UpchargeAmount": "0,0000000000",
            "UpchargeUnit": "1",
        }
        main_data.append(main_row)

        # 8) Add each property to property_data, except "Gyártó"
        for prop_key, prop_val in found_props.items():
            if prop_key == "Gyártó":
                continue  # Skip manufacturer here
            property_data.append({
                "PRODUCT SLUG": slug,
                "Property Name": prop_key,
                "Value": prop_val
            })

# ----------------------------------------------------------------------------
# 7) CREATE DATAFRAMES
# ----------------------------------------------------------------------------
main_cols = [
    "SLUG", "Active", "Featured", "SKU", "Name", "Product Type",
    "MSRP", "Cost", "Price", "Manufacturer", "Vendor", "Image", "Description",
    "Search Keywords", "Meta Title", "Meta Description", "Meta Keywords",
    "Tax Schedule", "Tax Exempt", "Weight", "Length", "Width", "Height",
    "Extra Ship Fee", "Ship Mode", "Non-Shipping Product", "Ships in a Separate Box",
    "Allow Reviews", "Minimum Qty", "Inventory Mode", "Inventory", "Stock Out at",
    "Low Stock at", "Roles", "Searchable", "AllowUpcharge", "UpchargeAmount", "UpchargeUnit"
]
df_main = pd.DataFrame(main_data, columns=main_cols)

df_property = pd.DataFrame(property_data, columns=["PRODUCT SLUG", "Property Name", "Value"])

# Clean DataFrames
clean_df(df_main)
clean_df(df_property)

# ----------------------------------------------------------------------------
# 8) WRITE TWO EXCEL FILES
# ----------------------------------------------------------------------------
excel_main_path = os.path.join(project_folder, "bikepro_hotcakes_import_tisztitott_main.xlsx")
with pd.ExcelWriter(excel_main_path, engine="openpyxl") as writer:
    df_main.to_excel(writer, sheet_name="Main", index=False)
print("Main Excel saved:", excel_main_path)

excel_property_path = os.path.join(project_folder, "bikepro_hotcakes_import_tisztitott_property.xlsx")
with pd.ExcelWriter(excel_property_path, engine="openpyxl") as writer:
    df_property.to_excel(writer, sheet_name="Property", index=False)
print("Property Excel saved:", excel_property_path)

driver.quit()
