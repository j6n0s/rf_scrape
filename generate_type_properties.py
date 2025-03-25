import os
import pandas as pd

# Global variable: the suffix to remove from property names in the mapping file
SUFFIX_TO_REMOVE = "_kiegeszitok_kulacsok"

# ------------------------------------------------------------------------------
# Define the base project path (adjust if necessary)
# ------------------------------------------------------------------------------
base_path = r'D:\2022\IT_Rendszerfejlesztes\II_fazis\kiegeszitok_kulacsok'

# ------------------------------------------------------------------------------
# 1) Read the Excel file (Sheet1) from 'bringaland_hotcakes_import_tisztitott_property.xlsx'
# ------------------------------------------------------------------------------
excel_file = os.path.join(base_path, 'bringaland_hotcakes_import_tisztitott_property.xlsx')
df_props = pd.read_excel(excel_file, sheet_name='Sheet1')

# Clean only the column headers for internal use (lowercase).
# This does NOT alter the actual "Property Name" or "Value" text in the cells.
df_props.columns = df_props.columns.str.strip().str.lower()

# Forward-fill the 'product slug' column. Convert product slugs to lowercase
# if your SKUs are also in lowercase. (Adjust as needed.)
df_props['product slug'] = df_props['product slug'].ffill().str.lower()

# ------------------------------------------------------------------------------
# 2) Read the property mapping file (ruhak_property.txt)
#    This file contains the mapping of property names to IDs.
# ------------------------------------------------------------------------------
property_file = os.path.join(base_path, 'kulacsok_property.txt')
df_property = pd.read_csv(property_file, delimiter='\t')

# Clean the column headers in the property file (this does NOT affect the data).
df_property.columns = df_property.columns.str.strip().str.lower()

# Remove the suffix _dzsekik from the property names before building the dictionary
df_property['propertyname'] = df_property['propertyname'].str.strip().str.replace(SUFFIX_TO_REMOVE, '', regex=False)

# Build the property mapping dictionary dynamically
# Key: the property name as it appears in the file (minus _dzsekik)
# Value: the corresponding ID
property_mapping = dict(zip(df_property['propertyname'], df_property['id']))

print("Mapped Property Names (suffix removed) and IDs:")
for prop_name, prop_id in property_mapping.items():
    print(f"'{prop_name}': {prop_id}")

# ------------------------------------------------------------------------------
# 3) Read the bvin-SKU mapping file (ruhak_bvin_sku.txt)
#    This file maps SKU to bvin.
# ------------------------------------------------------------------------------
bvin_sku_file = os.path.join(base_path, 'kulacsok_bvin_sku.txt')
df_bvin = pd.read_csv(bvin_sku_file, delimiter='\t')

# Clean column headers and ensure SKU is in lowercase (if needed).
df_bvin.columns = df_bvin.columns.str.strip().str.lower()
df_bvin['sku'] = df_bvin['sku'].str.lower()

# ------------------------------------------------------------------------------
# 4) Merge the Excel data with the bvin mapping using product slug == sku
# ------------------------------------------------------------------------------
merged = pd.merge(
    df_props,
    df_bvin,
    left_on='product slug',
    right_on='sku',
    how='left'
)

# ------------------------------------------------------------------------------
# 5) Generate SQL INSERT statements
#
# For each row:
#   - Use the bvin from the bvin-SKU mapping.
#   - Use the property mapping to look up the PropertyId based on the "Property Name"
#     from the Excel, with no forced lowercasing.
#   - Escape any single quotes in the property value.
# ------------------------------------------------------------------------------
store_id = 1
output_file = os.path.join(base_path, 'insert_statements.sql')
count = 0

with open(output_file, 'w', encoding='utf-8') as f:
    for _, row in merged.iterrows():
        bvin = row.get('bvin')
        # Use the original case from the Excel data (now in 'property name' column).
        tab_name = row.get('property name')
        tab_desc = row.get('value')
        
        # Skip rows with missing bvin, property name, or value
        if pd.isna(bvin) or pd.isna(tab_name) or pd.isna(tab_desc):
            continue
        
        # Because we removed _dzsekik from the property file,
        # we must match exactly what is in Excel to the new dictionary keys.
        # No lowercasing or suffix removal is done on the Excel side.
        prop_id = property_mapping.get(tab_name.strip())
        if not prop_id:
            # If the property is not mapped, skip or optionally print a debug message
            continue
        
        # Escape single quotes in the property value
        prop_value = str(tab_desc).replace("'", "''")
        
        # Construct the SQL INSERT statement
        sql = (
            f"INSERT INTO [PerfektDatabase].[dbo].[hcc_ProductPropertyValue] "
            f"(ProductBvin, PropertyId, PropertyValue, StoreId) "
            f"VALUES ('{bvin}', {prop_id}, '{prop_value}', {store_id});"
        )
        f.write(sql + "\n")
        count += 1

print(f"SQL insert statements have been written to {output_file}")
print(f"Total {count} records processed.")
