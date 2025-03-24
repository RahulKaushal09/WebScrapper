from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from fpdf import FPDF
from PIL import Image
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from fpdf import FPDF
from PIL import Image
# Initialize Selenium WebDriver (e.g., Chrome)
service = Service('/root/.wdm/drivers/chromedriver/linux64/114.0.5735.90/chromedriver-linux64/chromedriver')
options = webdriver.ChromeOptions()
user_agent_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
options.add_argument(f"user-agent={user_agent_string}")
options.add_argument('--headless')  # Run in background
options.add_argument("window-size=1400,1500")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("start-maximized")
options.add_argument("enable-automation")
options.add_argument("--disable-infobars")
options.add_argument("--disable-dev-shm-usage")
options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
options.add_argument('--disable-extensions')  # Disable extensions 



driver = webdriver.Chrome(service=service, options=options)

# Open the webpage



# List to store image paths
image_paths = []

# Create a directory to store downloaded images
if not os.path.exists("/root/webScrapping/getPDF/images"):
    os.makedirs("/root/webScrapping/getPDF/images")
links = ["https://www.notopedia.com/read/189932/Tm90ZXM=/MzMtNzUtMjkwLXBkZi0yMDIzMDEwOTEyMTE1NDU2MjcucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/Q3JpbWluYWwgTGF3IEluIEVuZ2xpc2g=","https://www.notopedia.com/read/189943/Tm90ZXM=/MzMtNzUtMjkwLXBkZi0yMDIzMDEwOTEyMTQxNTgwNDMucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/UHJvcGVydHkgTGF3IEluIEVuZ2xpc2g=","https://www.notopedia.com/read/189944/Tm90ZXM=/MzMtNzUtMjkwLXBkZi0yMDIzMDEwOTEyMjQxNDYwNzgucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/Q29tcGFueSBMYXcgSW4gRW5nbGlzaA==","https://www.notopedia.com/read/189945/Tm90ZXM=/MzMtNzUtMjkwLXBkZi0yMDIzMDEwOTEyMzYxMzEyMjMucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/UHVibGljIEludGVybmF0aW9uYWwgTGF3IEluIEVuZ2xpc2g=","https://www.notopedia.com/read/189891/Tm90ZXM=/MzMtNzUtMTczLXBkZi0yMDIyMTIyMDA4MzAwNDE2OTQucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/VGF4IExhdyBJbiBFbmdsaXNoIEluIEVuZ2xpc2g=","https://www.notopedia.com/read/189946/Tm90ZXM=/MzMtNzUtMjkwLXBkZi0yMDIzMDEwOTEyNDAwNjM1MjUucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/RW52aXJvbm1lbnRhbCBMYXcgSW4gRW5nbGlzaA==","https://www.notopedia.com/read/189947/Tm90ZXMgSQ==/MzMtNzUtMjkwLXBkZi0yMDIzMDEwOTEyNDIzNDYxMzQucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/TGFib3VyIExhdyBJbiBFbmdsaXNo","https://www.notopedia.com/read/189948/Tm90ZXMgSUk=/MzMtNzUtMjkwLXBkZi0yMDIzMDEwOTEyNDIzNjM1ODYucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/TGFib3VyIExhdyBJbiBFbmdsaXNo","https://www.notopedia.com/read/189949/Tm90ZXM=/MzMtNzUtMjkwLXBkZi0yMDIzMDEwOTEyNDU1NjQxMDEucGRm/5/Q29sbGVnZSBFbnRyYW5jZQ==/33/Q0xBVA==/75/UEc=/290/bm90ZXM=/SnVyaXNwcnVkZW5jZSBJbiBFbmdsaXNo"]
title = ["Criminal Law","Property Law","Company Law","Public International Law","Tax Law","Environmental Law","Labour Law 1","Labour Law 2","Jurisprudence"]
ends = [97,113,203,137,30,208,257,192,148]
for i in range(0,len(ends)):
    link = links[i]
    end = ends[i]
    pdfName = title[i].strip().replace(" ","_") + ".pdf"
    url = link
    driver.get(url)

    # Wait until the page is fully loaded (optional)
    driver.implicitly_wait(10) 
    start = 1
# end = 241
    # Loop through id values from 1 to 232
    for i in range(start, end):
        try:
            # Find the section by id
            section_id = str(i)
            section = driver.find_element(By.ID, section_id)
            
            # Get the image within the section
            img = section.find_element(By.TAG_NAME, 'img')
            img_url = img.get_attribute('src')
            
            # Download the image
            response = requests.get(img_url)
            
            if response.status_code == 200:
                # Save the image locally
                image_path = f'/root/webScrapping/getPDF/images/image_{section_id}.png'
                with open(image_path, 'wb') as file:
                    file.write(response.content)
                    image_paths.append(image_path)
                print(f"Downloaded image for section id {section_id}")
            else:
                print(f"Failed to download image: {img_url}")
        
        except Exception as e:
            print(f"Failed to download image for section id {section_id}: {e}")

    # # Close the Selenium driver
    
    image_path = f'/root/webScrapping/getPDF/images/'
    # Create a PDF document using FPDF

    pdf = FPDF()


    # Add each image to the PDF
    for i in range (start, end):
        # Open the image using PIL to get its dimensions
        
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
    pdf.output(pdfName)

    print("pdf created -> " + pdfName )
# Optional: Code to create a PDF using the downloaded images can go here
driver.quit()