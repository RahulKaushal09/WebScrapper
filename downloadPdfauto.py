import requests
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

def add_watermark_to_pdf(pdf_url, watermark_path, output_path):
    try:
        # Download the PDF from the URL
        response = requests.get(pdf_url)
        response.raise_for_status()  # Check for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return

    # Load the PDF
    pdf_data = BytesIO(response.content)
    pdf_document = fitz.open(stream=pdf_data, filetype="pdf")

    # Load the watermark image
    watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
    if watermark.shape[2] == 4:  # If watermark has alpha channel
        watermark = cv2.cvtColor(watermark, cv2.COLOR_BGRA2BGR)
    watermark = cv2.cvtColor(watermark, cv2.COLOR_BGR2RGB)
    
    # Create a new PDF
    new_pdf = fitz.open()

    for page_num in range(len(pdf_document)):
        # Render the page to an image
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        page_image = Image.open(BytesIO(pix.tobytes("png")))

        # Convert page image to OpenCV format
        page_image_cv = np.array(page_image)
        page_image_cv = cv2.cvtColor(page_image_cv, cv2.COLOR_RGB2BGR)

        # Resize watermark to match page size
        height, width = page_image_cv.shape[:2]
        watermark_resized = cv2.resize(watermark, (width, height))

        # Blend watermark with the page image
        blended_image = cv2.addWeighted(page_image_cv, 1.0, watermark_resized, 0.9, 0)

        # Convert back to PIL image for saving
        blended_image_pil = Image.fromarray(cv2.cvtColor(blended_image, cv2.COLOR_BGR2RGB))

        # Save to a BytesIO object
        with BytesIO() as output_io:
            blended_image_pil.save(output_io, format='PNG')
            output_io.seek(0)  # Rewind the BytesIO object
            # Add the watermarked image to the new PDF
            new_page = new_pdf.new_page(width=page_image.size[0], height=page_image.size[1])
            new_page.insert_image(fitz.Rect(0, 0, page_image.size[0], page_image.size[1]), stream=output_io.read())

    # Save the new PDF
    new_pdf.save(output_path)

# Example usage
pdf_url = 'http://edurev.in/uploads/60ab5b32-9259-4fda-9da3-d203f471e3a0.pdf'
watermark_path = '/root/webScrapping/logo.jpg'
output_path = '/root/webScrapping/watermarked_output.pdf'
add_watermark_to_pdf(pdf_url, watermark_path, output_path)
