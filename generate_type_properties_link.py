# Global configuration
STARTING_TRANSLATION_ID = 91    # The first ProductPropertyValueTranslationId
STARTING_VALUE_ID = 91          # The first ProductPropertyValueId
NUM_OFFSET = 120              # The number of rows to generate (last value = STARTING + NUM_OFFSET)

OUTPUT_FILE = 'insert_translations.sql'
CULTURE = 'en-US'
PROPERTY_LOCALIZABLE_VALUE = 'NULL'  # Always NULL

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    # Enable explicit inserts for identity columns
    f.write("SET IDENTITY_INSERT [PerfektDatabase].[dbo].[hcc_ProductPropertyValueTranslations] ON;\n\n")
    
    # Generate the INSERT statements
    for i in range(NUM_OFFSET + 1):
        translation_id = STARTING_TRANSLATION_ID + i
        value_id = STARTING_VALUE_ID + i
        
        sql = (
            f"INSERT INTO [PerfektDatabase].[dbo].[hcc_ProductPropertyValueTranslations] "
            f"(ProductPropertyValueTranslationId, ProductPropertyValueId, Culture, PropertyLocalizableValue) "
            f"VALUES ({translation_id}, {value_id}, '{CULTURE}', {PROPERTY_LOCALIZABLE_VALUE});"
        )
        f.write(sql + "\n")
    
    # Disable explicit identity inserts after we're done
    f.write("\nSET IDENTITY_INSERT [PerfektDatabase].[dbo].[hcc_ProductPropertyValueTranslations] OFF;\n")

print(f"SQL insert statements have been written to {OUTPUT_FILE}")
