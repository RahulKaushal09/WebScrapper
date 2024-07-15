import requests
import os
import uuid
from PIL import Image, UnidentifiedImageError
import numpy as np
import cv2

# Define your public IP for storing images
PUBLIC_IP = "https://fc.edurev.in/images"
location_of_images = "/var/www/html/images"
local_dir = "/home/er-ubuntu-1/webScrapping/removeWaterMark"  # Local directory to save images

# Ensure the directory exists
os.makedirs(local_dir, exist_ok=True)

def download_image(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_name = f"{uuid.uuid4()}.jpg"  # Save as .jpg or appropriate extension
        image_path = os.path.join(local_dir, image_name)
        print(image_path)
        with open(image_path, 'wb') as img_file:
            img_file.write(response.content)
        return image_path
    except requests.RequestException as e:
        print(f"Failed to download image from {image_url}: {e}")
        return None

def remove_background_and_convert_to_bw(image_path):
    try:
        img = Image.open(image_path)
        img_np = np.array(img)
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        white_background = np.full_like(img_np, fill_value=255)
        background = cv2.bitwise_and(white_background, white_background, mask=mask)
        foreground = cv2.bitwise_and(img_np, img_np, mask=mask_inv)
        result = cv2.add(background, foreground)
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        result_img = Image.fromarray(result_rgb)
        # Save the processed image with a UUID
        new_image_name = f"{uuid.uuid4()}.jpg"
        new_image_path = os.path.join(location_of_images, new_image_name)
        new_image_path_public = os.path.join(PUBLIC_IP, new_image_name)
        os.remove(image_path)
        result_img.save(new_image_path)
        return new_image_path_public
    except UnidentifiedImageError:
        print(f"Failed to process image at {image_path}. Image file may be corrupted or in an unsupported format.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
