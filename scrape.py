import os
import re
import time
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io

# ----------------------------------------------------------------------------
# 1) PROJECT & FOLDER SETTINGS
# ----------------------------------------------------------------------------
project_folder = r"D:\2022\IT_Rendszerfejlesztes\II_fazis"
mentes_folder = os.path.join(project_folder, "kiegeszitok_kulacsok")
os.makedirs(project_folder, exist_ok=True)

# Az új image folder: basepath + "\ruhak\images"
image_folder = os.path.join(project_folder, "kiegeszitok_kulacsok", "images")
os.makedirs(image_folder, exist_ok=True)

# ----------------------------------------------------------------------------
# 2) SITE SETTINGS
# ----------------------------------------------------------------------------
base_url = "https://bikepro.hu/kerekpar_kiegeszitok/kulacs_kulacstarto_329/kulacs_486"
total_pages = 6  # szükség szerint módosítsd

# ----------------------------------------------------------------------------
# 3) SELENIUM SETUP
# ----------------------------------------------------------------------------
service = Service()
options = webdriver.ChromeOptions()
# options.add_argument('--headless')
driver = webdriver.Chrome(service=service, options=options)

# ----------------------------------------------------------------------------
# 4) HELPER FUNCTIONS
# ----------------------------------------------------------------------------
def remove_illegal_chars(text):
    """Törli az Excel számára illegális karaktereket."""
    ILLEGAL_CHARACTERS_RE = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]+')
    return text if not isinstance(text, str) else ILLEGAL_CHARACTERS_RE.sub("", text)

def download_and_convert_image(url, save_path):
    """Kép letöltése és JPEG formátumban mentése."""
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
                print(f"Kép letöltve és mentve: {save_path}")
            except Exception:
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                print(f"Kép mentve (konvertálás nélkül): {save_path}")
    except Exception as e:
        print("Error downloading image:", url, e)

# ----------------------------------------------------------------------------
# 5) TARGET EXCEL STRUCTURES
# ----------------------------------------------------------------------------
# Ezek a fix oszlopnevek a bringaland_hotcakes_import_tisztitott_main.xlsx-ben:
MAIN_HEADERS = [
    "SLUG",
    "Active",
    "Featured",
    "SKU",
    "Name",
    "Product Type",
    "MSRP",
    "Cost",
    "Price",
    "Manufacturer",
    "Vendor",
    "Image",
    "Description",
    "Search Keywords",
    "Meta Title",
    "Meta Description",
    "Meta Keywords",
    "Tax Schedule",
    "Tax Exempt",
    "Weight",
    "Length",
    "Width",
    "Height",
    "Extra Ship Fee",
    "Ship Mode",
    "Non-Shipping Product",
    "Ships in a Separate Box",
    "Allow Reviews",
    "Minimum Qty",
    "Inventory Mode",
    "Inventory",
    "Stock Out at",
    "Low Stock at",
    "Roles",
    "Searchable",
    "AllowUpcharge",
    "UpchargeAmount",
    "UpchargeUnit",
]

# Ezek a fix oszlopnevek a bringaland_hotcakes_import_tisztitott_property.xlsx-ben:
PROPERTY_HEADERS = [
    "PRODUCT SLUG",
    "Property Name",
    "Value",
]

# ----------------------------------------------------------------------------
# 6) SCRAPE
# ----------------------------------------------------------------------------
main_data = []       # A main sheet adatai
property_data = []   # A property sheet adatai

product_counter = 1

for page in range(1, total_pages + 1):
    page_url = base_url if page == 1 else f"{base_url}?page={page}"
    driver.get(page_url)
    time.sleep(5)

    # Görgetés a dinamikus tartalom betöltéséhez
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_boxes = soup.find_all("div", class_="product-snapshot list_div_item")
    print(f"Oldal: {page_url} - Talált termékek száma: {len(product_boxes)}")
    
    for box in product_boxes:
        title_anchor = box.find("a", class_="img-thumbnail-link")
        if not title_anchor:
            continue
        product_url = title_anchor.get("href", "")
        if product_url and not product_url.startswith("http"):
            product_url = "https://bikepro.hu" + product_url
        
        product_name = title_anchor.get("title", "").strip() or title_anchor.get_text(strip=True)
        
        price_tag = box.find("span", class_="product-price")
        price = price_tag.get_text(strip=True) if price_tag else ""

        # Generáljunk egy SLUG-ot a product_counter alapján (pl. alk0001, alk0002, stb.)
        slug_str = f"kit{product_counter:04d}"
        
        # Termék részletes oldal betöltése
        driver.get(product_url)
        time.sleep(2)
        soup_product = BeautifulSoup(driver.page_source, "html.parser")
        
        # Tulajdonságok kinyerése
        try:
            param_tab = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "productparams-tab"))
            )
            param_tab.click()
            time.sleep(1)
        except Exception:
            pass

        param_soup = BeautifulSoup(driver.page_source, "html.parser")
        param_table = param_soup.find("table", class_="parameter-table")
        found_props = {}
        if param_table:
            for row in param_table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) == 2:
                    key = cols[0].get_text(strip=True)
                    val = cols[1].get_text(strip=True).replace("\xa0", " ")
                    # Példa: "Színválaszték" -> "szin"
                    if key.lower() == "színválaszték":
                        key = "Szín"
                    found_props[key] = val

        # Gyártó
        manufacturer = found_props.get("Gyártó")
        if not manufacturer:
            manufacturer = random.choice(["Acor", "Laken", "SKS", "Bikefun"])
        found_props["Gyártó"] = manufacturer

        # Fix property
        if "Alapanyag" not in found_props:
            found_props["Vázméret"] = "Műanyag"
        if "Űrtartalom" not in found_props:
            found_props["Űrtartalom"] = "0,75 Liter"

        # Leírás kinyerése
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
            short_desc = desc_soup.find("td", class_="product-short-description")
            if short_desc:
                full_description = short_desc.get_text(strip=True)
        
        # Csak az első kép kinyerése
        image_url = ""
        product_image_main = soup_product.find("div", class_="product-image-main")
        if product_image_main:
            image_link = product_image_main.find("a", id="product-image-link")
            if image_link and image_link.has_attr("href"):
                image_url = image_link["href"]
        if not image_url:
            image_url_tag = soup_product.find("img", {"itemprop": "image"})
            if image_url_tag and image_url_tag.has_attr("src"):
                image_url = image_url_tag["src"]
        
        image_filename = os.path.join(image_folder, f"product_image_alkouv_{product_counter}.jpg")
        download_and_convert_image(image_url, image_filename)
        
        # ----------------------------------------------------------------------------
        # MAIN SHEET FELÉPÍTÉSE
        # ----------------------------------------------------------------------------
        # A sample “main” oszlopok kitöltése (SLUG, Name, Price, Manufacturer, stb.)
        # A hiányzókat default értékre állítjuk (pl. 0 Ft, NO, YES, stb.)

        main_row = {
            "SLUG": slug_str,
            "Active": "YES",
            "Featured": "NO",
            "SKU": slug_str.upper(),
            "Name": product_name,
            "Product Type": "", 
            "MSRP": "0,00 Ft",
            "Cost": "0,00 Ft",
            "Price": price if price else "0 Ft",
            "Manufacturer": manufacturer,
            "Vendor": "",
            "Image": os.path.basename(image_filename),  # pl. "product_image_ruha_1.jpg"
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

        # ----------------------------------------------------------------------------
        # PROPERTY SHEET FELÉPÍTÉSE
        # ----------------------------------------------------------------------------
        # A property Excel-ben a “PRODUCT SLUG” oszlopban csak az első tulajdonságsornál
        # tüntetjük fel az adott SLUG-ot, utána üres marad (lásd a felhasználó kérése).
        found_prop_items = list(found_props.items())  # (key, val) párok
        for i, (prop_name, prop_value) in enumerate(found_prop_items):
            if prop_name != "Gyártó":
                property_row = {
                "PRODUCT SLUG": slug_str if i == 0 else "",
                "Property Name": prop_name,
                "Value": prop_value,
            }
            property_data.append(property_row)
        product_counter += 1

driver.quit()

# ----------------------------------------------------------------------------
# 7) ADATOK ÁTALAKÍTÁSA ÉS MENTÉSE KÉT KÜLÖN EXCELBE
# ----------------------------------------------------------------------------
df_main = pd.DataFrame(main_data)
df_prop = pd.DataFrame(property_data)

# 1) Igazítjuk az oszlopokat a kívánt sorrendhez
df_main = df_main.reindex(columns=MAIN_HEADERS)
df_prop = df_prop.reindex(columns=PROPERTY_HEADERS)

# 2) Tisztítjuk a cellákat
for df in [df_main, df_prop]:
    for col in df.columns:
        df[col] = df[col].apply(remove_illegal_chars)

# 3) Exportáljuk két külön Excel fájlba
main_export_path = os.path.join(mentes_folder, "bikepro_hotcakes_import_tisztitott_main.xlsx")
property_export_path = os.path.join(mentes_folder, "bringaland_hotcakes_import_tisztitott_property.xlsx")

df_main.to_excel(main_export_path, sheet_name='Main', index=False)
df_prop.to_excel(property_export_path, index=False)

print("Export complete:")
print(f"Main Excel: {main_export_path}")
print(f"Property Excel: {property_export_path}")
