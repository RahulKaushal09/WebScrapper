from bs4 import BeautifulSoup
import requests
import os
import uuid
from PIL import Image, UnidentifiedImageError
import numpy as np
import cv2
from streamlit import image

# Define your public IP for storing images
PUBLIC_IP = "https://fc.edurev.in/images"
# Public_IP = "http://167.172.89.41/images/"

location_of_images = "/var/www/html/images"
local_dir = "/removeWaterMark"  # Local directory to save images

# Ensure the directory exists
os.makedirs(local_dir, exist_ok=True)
from PIL import Image
from io import BytesIO
def download_image_direct_link(image_url):
    """Download an image from a URL."""
    response = requests.get(image_url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        print("Error downloading image:", response.status_code)
        return None
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



import requests
import time

# JWT token to be used in the headers
headers = {
  'Cookie': '_ga=GA1.1.21850187.1729853842; i18n_redirected=en; _fbp=fb.1.1729853852318.251930519160225066; _ga_JTP8GYBTE1=GS1.1.1729853842.1.1.1729853904.60.0.1580891050',
  'Authorization': 'JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFpZWFzZV8xODA1OTJkMGJjMWMwODcyIiwiZXhwIjoxNzMwNDU4NjQ3LCJzdWIiOiJhY2Nlc3MifQ.iK_3WDZcRdcdFWD8q_EMUGQst3RmjbrJTvgrXfpPNZQ'
}# Step 1: Upload the image
def upload_image(image_path):
    url = "https://www.aiease.ai/api/api/id_photo/raw_picture"
    # files = {'file': open(image_path, 'rb')}
    # data = {'max_size': '5', 'ignore_pixel': '1'}
    payload = {'max_size': '5',
    'ignore_pixel': '1'}
    files=[
    ('file',('watermark.png',open(image_path,'rb'),'image/png'))
    ]
    
    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    if response.status_code == 200:
        return response.json()['result']['presigned_url']
    else:
        print("Error uploading image:", response.json())
        return None

# Step 2: Send a request to remove text from the image
def request_watermark_text_removal(img_url):
    url = "https://www.aiease.ai/api/api/gen/img2img"
    data = {
        "gen_type": "text_remove",
        "text_remove_extra_data": {
            "img_url": img_url,
            "mask_url": ""
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()['result']['task_id']
    else:
        print("Error requesting text removal:", response.json())
        return None

# Step 3: Check the task status until it's complete
def check_watermark_task_status(task_id):
    url = f"https://www.aiease.ai/api/api/id_photo/task-info?task_id={task_id}"
    
    while True:
        time.sleep(3)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(response.json())
            result = response.json()
            if('result' in result and 'data' in result['result'] and 'queue_info' in result['result']['data'] and 'status' in result['result']['data']['queue_info']):
                status = result['result']['data']['queue_info']['status']
                if status == "success":
                    return result['result']['data']['results'][0]['origin']
                elif status == "processing":
                    print("Task is still processing. Checking again in 5 seconds...")
                elif status == "uploading":
                    print("Task is still uploading. Checking again in 5 seconds...")
                    # time.sleep(5)
                else:
                    print("Unexpected task status:", status)
                    return None
        else:
            print("Error checking task status:", response.json())
            return None

# Main function to process the image
def RemoveWaterMarkWithAi(image_path):
    try:
        img_url = upload_image(image_path)
        if not img_url:
            return None

        task_id = request_watermark_text_removal(img_url)
        if not task_id:
            return None

        final_image_url = check_watermark_task_status(task_id)
        if final_image_url:
            print("Text-removed image is available at:", final_image_url)
            return final_image_url
        else:
            print("Failed to process image.")
            return image_path
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return image_path

def convert_to_black_and_white(imageurl,imagePath = ""):
    # Open the image file
    if(imageurl != "" ):
        img = download_image_direct_link(imageurl)
    else:
        img = Image.open(imagePath)
    # Convert the image to grayscale (black and white)
    bw_img = img.convert("L")
    # Save the converted image
    image_name = f"{uuid.uuid4()}.jpg"  # Save as .jpg or appropriate extension
    image_path = os.path.join(local_dir, image_name)
    print(image_path)
    bw_img.save(image_path)
    return image_path

def HtmlToRemoveWaterMark(htmlContent):
    try:
        soup = BeautifulSoup(htmlContent, 'html.parser')
        images = soup.find_all('img')
        for img in images:
            image_url = img['src']
            image_path = download_image(image_url)
            if image_path:
                new_image_url = RemoveWaterMarkWithAi(image_path)
                if(new_image_url):
                    new_img_with_bw = convert_to_black_and_white(new_image_url)
                    if new_img_with_bw:
                        img['src'] = new_img_with_bw
                    else:
                        img['src'] = new_image_url
        return str(soup)
    except Exception as e:
        print(e)
        return htmlContent
