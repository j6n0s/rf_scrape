import pandas as pd

# ------------------------------------------------------------------------------
# 1) Read the “Type Properties” sheet from the Excel file
# ------------------------------------------------------------------------------
excel_file = 'masodik_sample\\bringaland_hotcakes_import_tisztitott.xlsx'
df_props = pd.read_excel(excel_file, sheet_name='Type Properties')

# Rename columns to lowercase, strip extra whitespace
df_props.columns = df_props.columns.str.strip().str.lower()
# Example: columns become ['product slug', 'tab name', 'tab description']

# ------------------------------------------------------------------------------
# 2) Convert data format by forward-filling the product slug
#    This fills blank cells in 'product slug' with the value above
# ------------------------------------------------------------------------------
df_props['product slug'] = df_props['product slug'].ffill()

# ------------------------------------------------------------------------------
# 3) Lowercase the slug to match your mapping file
# ------------------------------------------------------------------------------
df_props['product slug'] = df_props['product slug'].str.lower()

# ------------------------------------------------------------------------------
# 4) Read the mapping file (properties.txt), which has SKU and bvin columns
# ------------------------------------------------------------------------------
mapping_file = 'properties.txt'
df_mapping = pd.read_csv(mapping_file, delimiter='\t')

# Rename columns in the mapping file and lowercase them
df_mapping.columns = df_mapping.columns.str.strip().str.lower()
# Make sure the 'sku' column is also in lowercase for merging
df_mapping['sku'] = df_mapping['sku'].str.lower()

# ------------------------------------------------------------------------------
# 5) Merge the two DataFrames so each row gets its corresponding bvin
# ------------------------------------------------------------------------------
merged = pd.merge(
    df_props, 
    df_mapping, 
    left_on='product slug',  # from the Excel
    right_on='sku',          # from the mapping file
    how='left'
)

# ------------------------------------------------------------------------------
# 6) Define property mapping (Tab Name -> PropertyId).
#    Adjust as needed for your actual property IDs.
# ------------------------------------------------------------------------------
property_mapping = {
    'evjarat': 26,   # example
    'meret': 24,     # example
    'szin': 25,       # example
    'Anyag': 8,
    'Kerek_meret': 18,
    'Kerekpar_fajta': 20,
    'Kerekpar_meret': 19,
    'Kormany': 11,
    'Nem': 21,
    'Nyereg': 12,
    'Ruha_meret': 5,
    'Vaz': 9
}

store_id = 1
output_file = 'insert_statements.sql'

# ------------------------------------------------------------------------------
# 7) Generate SQL INSERT statements and write them to a file
# ------------------------------------------------------------------------------
count = 0
with open(output_file, 'w', encoding='utf-8') as f:
    for _, row in merged.iterrows():
        count += 1
        bvin = row['bvin']
        tab_name = row['tab name']
        tab_desc = row['tab description']

        # Skip if bvin or property fields are missing
        if pd.isna(bvin) or pd.isna(tab_name) or pd.isna(tab_desc):
            continue
        
        # Convert the tab_name to lowercase for the property mapping
        prop_id = property_mapping.get(tab_name.lower())
        if not prop_id:
            # If this Tab Name isn't in your property_mapping, skip it
            continue
        
        # Escape single quotes in the property value
        prop_value = str(tab_desc).replace("'", "''")

        # Construct the SQL statement
        sql = (
            f"INSERT INTO [PerfektDatabase].[dbo].[hcc_ProductPropertyValue] "
            f"(ProductBvin, PropertyId, PropertyValue, StoreId) "
            f"VALUES ('{bvin}', {prop_id}, '{prop_value}', {store_id});"
        )
        
        f.write(sql + "\n")

print(f"SQL insert statements have been written to {output_file}")
print (f"Total {count} records processed.")
