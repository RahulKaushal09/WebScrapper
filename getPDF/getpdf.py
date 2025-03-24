from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from fpdf import FPDF
from PIL import Image
import os
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By

# # Initialize Selenium WebDriver (e.g., Chrome)
# service = Service('/root/.wdm/drivers/chromedriver/linux64/114.0.5735.90/chromedriver-linux64/chromedriver')
# options = webdriver.ChromeOptions()
# user_agent_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
# options.add_argument(f"user-agent={user_agent_string}")
# options.add_argument('--headless')  # Run in background
# options.add_argument("window-size=1400,1500")
# options.add_argument("--disable-gpu")
# options.add_argument("--no-sandbox")
# options.add_argument("start-maximized")
# options.add_argument("enable-automation")
# options.add_argument("--disable-infobars")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
# options.add_argument('--disable-extensions')  # Disable extensions 



# driver = webdriver.Chrome(service=service, options=options)

# # Open the webpage
# url = 'https://www.notopedia.com/read/189904/Tm90ZXMgSUk=/MzMtNzUtMjkwLXBkZi0yMDIzMDEwOTEwMjkyODcyNjEucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/TGF3IE9mIENvbnRyYWN0IEluIEVuZ2xpc2g='
# driver.get(url)

# # Wait until the page is fully loaded (optional)
# driver.implicitly_wait(10) 

# # Find the section with images
# sections = driver.find_elements(By.CSS_SELECTOR, 'section.ib_page')

# print(sections)
# i =0
# for section in sections:
#     # Get all the image elements within the section
#     try:
#         img = section.find_element(By.TAG_NAME, 'img')

#         # List to store image paths
#         image_paths = []

#         # Create a directory to store downloaded images
#         # if not os.path.exists("images"):
#         #     os.makedirs("images")

#         # Download each image
#         img_url = img.get_attribute('src')
#         response = requests.get(img_url)
        
#         if response.status_code == 200:
#             # Save the image locally
#             image_path = f'/root/webScrapping/getPDF/images/image_{i}.png'
#             with open(image_path, 'wb') as file:
#                 file.write(response.content)
#                 image_paths.append(image_path)
#         else:
#             print(f"Failed to download image: {img_url}")
#         i+=1
#     except Exception as e:
#         print(f"Failed to download image: {e}")

# # Close the Selenium driver
# driver.quit()
image_path = f'/root/webScrapping/getPDF/images/'
# Create a PDF document using FPDF

pdf = FPDF()


# Add each image to the PDF
for i in range (0,233):
    # Open the image using PIL to get its dimensions
    if i == 82:
        continue
    else:
        image_path = f'/root/webScrapping/getPDF/images/image_{i}.png'
        image = Image.open(image_path)
        img_width, img_height = image.size
        
        # Get the aspect ratio of the image
        img_aspect = img_width / img_height
        
        # Set PDF page size to match the image aspect ratio
        pdf_aspect = pdf.w / pdf.h
        
        # Adjust the size based on the aspect ratio
        if img_aspect > pdf_aspect:
            # Image is wider than the page
            width = pdf.w
            height = width / img_aspect
        else:
            # Image is taller than the page
            height = pdf.h
            width = height * img_aspect
        
        # Add a new page with custom dimensions
        pdf.add_page()
        
        # Place the image at (0, 0) and scale it to fit the entire page
        pdf.image(image_path, x=0, y=0, w=width, h=height)

# Save the PDF to a file
pdf.output("output.pdf")

print("pdf created")