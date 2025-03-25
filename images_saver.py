import pandas as pd
import os
import shutil
from PIL import Image

def standardize_image(img, target_size=(730, 730), background_color=(255, 255, 255)):
    """
    Standardizes the given image by fitting it into a fixed-size canvas (target_size).
    The image is resized to fit within target_size while preserving its aspect ratio,
    then pasted into the center of a new image of size target_size with the specified background color.
    """
    # Convert image to RGB if not already
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # Create a new blank image with the target size and background color
    standardized = Image.new("RGB", target_size, background_color)
    
    # Resize the image to fit within target_size while maintaining aspect ratio
    img.thumbnail(target_size, Image.Resampling.LANCZOS)
    
    # Calculate coordinates to center the resized image on the canvas
    left = (target_size[0] - img.width) // 2
    top = (target_size[1] - img.height) // 2
    
    # Paste the resized image onto the canvas
    standardized.paste(img, (left, top))
    return standardized

# --- Script Configuration ---
base_path = r"D:\2022\IT_Rendszerfejlesztes\II_fazis\kiegeszitok_kulacsok"

# Paths
txt_file = os.path.join(base_path, "kulacsok.txt")
output_dir = os.path.join(base_path, "import_images")
source_dir = os.path.join(base_path, "images")

# Thumbnail sizes
SMALL_THUMB = (530, 530)
MEDIUM_THUMB = (530, 530)
# Main (standardized) image size
MAIN_IMAGE_SIZE = (530, 530)

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Read the tab-separated text file
df = pd.read_csv(txt_file, sep='\t')

# Process each row in the DataFrame
for index, row in df.iterrows():
    # bvin becomes the folder name; image_name is the source filename
    bvin = str(row['bvin'])
    image_name = str(row['ImageFileSmall'])  # or row['ImageFileMedium'] if they differ

    # Create the product folder under the output directory
    product_folder = os.path.join(output_dir, bvin)
    os.makedirs(product_folder, exist_ok=True)
    
    # Create 'medium' and 'small' subfolders
    medium_folder = os.path.join(product_folder, 'medium')
    small_folder = os.path.join(product_folder, 'small')
    os.makedirs(medium_folder, exist_ok=True)
    os.makedirs(small_folder, exist_ok=True)
    
    # Full path to the source image
    source_image_path = os.path.join(source_dir, image_name)
    
    if os.path.exists(source_image_path):
        # Copy the original image into the product folder
        dest_image_path = os.path.join(product_folder, image_name)
        shutil.copy2(source_image_path, dest_image_path)
        
        # Open the copied image, standardize it to a larger canvas, and overwrite
        with Image.open(dest_image_path) as img:
            # Create the standardized main image
            std_img = standardize_image(img, target_size=MAIN_IMAGE_SIZE)
            std_img.save(dest_image_path)  # Overwrite the main image in the product folder
            
            # Create a small thumbnail from the standardized main image
            img_small = std_img.copy()
            img_small.thumbnail(SMALL_THUMB, Image.Resampling.LANCZOS)
            small_save_path = os.path.join(small_folder, image_name)
            img_small.save(small_save_path)
            
            # Create a medium thumbnail from the standardized main image
            img_medium = std_img.copy()
            img_medium.thumbnail(MEDIUM_THUMB, Image.Resampling.LANCZOS)
            medium_save_path = os.path.join(medium_folder, image_name)
            img_medium.save(medium_save_path)
        
        print(f"Processed: {bvin} - {image_name}")
    else:
        print(f"Image not found: {source_image_path}")

print("Processing complete!")
