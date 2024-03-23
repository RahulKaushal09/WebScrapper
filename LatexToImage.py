from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
import time
import os

import uuid


def get_image(mathjax, uuid_image_path):
    # Prepare the HTML content with the provided MathJax string
    html_text = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MathJax Image Automation</title>
        <style>
            body, html {{
                margin: 10px;
                padding: 5px;
                overflow: hidden;
                height: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            #math-content {{
                
                padding: 10px;
                text-align: center;
                transform-origin: center center;
            }}
        </style>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script type="text/javascript" id="MathJax-script" async
                src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script>
            window.onload = function() {{
                document.getElementById('math-content').style.height =
                    document.querySelector('.MathJax').getBoundingClientRect().height+5 + 'px';
            }};
        </script>
    </head>
    <body>
        <div id="math-content">
            {mathjax}
        </div>
    </body>
    </html>
    '''
    # print("hey")
    encoded_html = urllib.parse.quote(html_text)
    service = Service(ChromeDriverManager().install())
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
    options.add_argument("--disable-dev-shm-usage")  # Run in background
    # Setup WebDriver
    
    options.headless = True  # Enable headless mode if no GUI is needed
    driver = webdriver.Chrome(service=service, options=options)

    # Use the data URI scheme to load the HTML content directly
    driver.get(f"data:text/html;charset=utf-8,{encoded_html}")

    # Wait for MathJax to render (adjust the timeout as necessary)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "math-content"))
    )

    # Wait a bit for rendering to stabilize
    time.sleep(2)

    # Find the MathJax container element
    math_element = driver.find_element(By.ID, "math-content")

    # Take a screenshot of just the MathJax element
    math_element.screenshot(uuid_image_path)

    # Cleanup
    driver.quit()
    return True


image_folder_path = "/var/www/html/images"
Public_IP = "http://52.139.218.113/images"

def replace_mathjax_with_images(html_content):
    
    """
    Parse HTML content, identify MathJax/LaTeX, convert to images, and replace original content with images.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    textBook = False
    attribute = "mathMlContainer"
    # Adjust this selector based on your HTML structure
    math_elements = soup.find_all(class_="mathMlContainer")
    if(len(math_elements) == 0) :
        math_elements = soup.find_all(lambda tag: tag.has_attr('data-mathml'))
        # data-mathm
        # print(math_elements)
        if (len(math_elements) == 0) :
            math_elements = soup.find_all("mjx-container")
            if (len(math_elements) == 0) :
                return html_content
            else:
                attribute = "mjx-container"
                textBook = True
        else:
            attribute = "data-mathml"
            textBook = True
    else:
        attribute = "mathMlContainer"
        textBook = True
        # math_elements = soup.find_all(class_="mathMlContainer")
    


    # print(soup)

    for elements in math_elements:
        if textBook == True:
            uuid_str = str(uuid.uuid4())
            # Assuming the LaTeX string can be directly obtained from the element's text
            image_url = f"{image_folder_path}/{uuid_str}.png"
            # element = elements.get('data-mathml')
            if(attribute == "mjx-container" ):
                element = elements
            else:
                element = elements.get('data-mathml')
            print(elements)
            print(element)
            if get_image(element, image_url):
                image_url =f"{Public_IP}/{uuid_str}.png"
                new_img_tag = soup.new_tag("img", src=image_url)
                print(new_img_tag)
                elements.replace_with(new_img_tag)
        else:
            uuid_str = str(uuid.uuid4())
            # Assuming the LaTeX string can be directly obtained from the element's text
            image_url = f"{os.getcwd()}/{image_folder_path}/{uuid_str}.png"
            if get_image(elements, image_url):
                new_img_tag = soup.new_tag("img", src=image_url)
                elements.replace_with(new_img_tag)
    # print(soup.prettify())
    return str(soup)



# Function to map MathML to LaTeX

# Convert the example HTML to LaTeX

# Example HTML content
def excelRun(html_content):
    
    # html_content = """<h3 ng-bind="vernacularStaticTextContent['ts_ques_detail'][8]" class="ng-binding">Explanation:</h3> <p> <span class="question_exp ng-binding" ng-bind-html="toTrustedHTML(show_single_data[6])"><p>Given-</p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="2" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mfrac><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="3"><mjx-c class="mjx-c2B"></mjx-c></mjx-mo><mjx-mfrac space="3"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mn class="mjx-n" space="4"><mjx-c class="mjx-c32"></mjx-c></mjx-mn></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mfrac><mi>A</mi><mi>B</mi></mfrac><mo>+</mo><mfrac><mi>B</mi><mi>A</mi></mfrac><mo>=</mo><mn>2</mn></math></mjx-assistive-mml></mjx-container></span><br></p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="3" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mo class="mjx-n"><mjx-c class="mjx-c21D2"></mjx-c></mjx-mo><mjx-mfrac space="4"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="3"><mjx-c class="mjx-c2B"></mjx-c></mjx-mo><mjx-mfrac space="3"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mn class="mjx-n" size="s"><mjx-c class="mjx-c31"></mjx-c></mjx-mn></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mstyle size="s"><mjx-mfrac><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac></mjx-mstyle></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mn class="mjx-n" space="4"><mjx-c class="mjx-c31"></mjx-c></mjx-mn><mjx-mo class="mjx-n" space="3"><mjx-c class="mjx-c2B"></mjx-c></mjx-mo><mjx-mfrac space="3"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mn class="mjx-n" size="s"><mjx-c class="mjx-c31"></mjx-c></mjx-mn></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mn class="mjx-n" size="s"><mjx-c class="mjx-c31"></mjx-c></mjx-mn></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mo>⇒</mo><mfrac><mi>A</mi><mi>B</mi></mfrac><mo>+</mo><mfrac><mn>1</mn><mstyle display=""><mfrac><mi>A</mi><mi>B</mi></mfrac></mstyle></mfrac><mo>=</mo><mn>1</mn><mo>+</mo><mfrac><mn>1</mn><mn>1</mn></mfrac></math></mjx-assistive-mml></mjx-container></span></p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="4" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mo class="mjx-n"><mjx-c class="mjx-c21D2"></mjx-c></mjx-mo><mjx-mfrac space="4"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mn class="mjx-n" space="4"><mjx-c class="mjx-c31"></mjx-c></mjx-mn></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mo>⇒</mo><mfrac><mi>A</mi><mi>B</mi></mfrac><mo>=</mo><mn>1</mn></math></mjx-assistive-mml></mjx-container></span><br></p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="5" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mo class="mjx-n"><mjx-c class="mjx-c21D2"></mjx-c></mjx-mo><mjx-mi class="mjx-i" space="4"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mi class="mjx-i" space="4"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mo>⇒</mo><mi>A</mi><mo>=</mo><mi>B</mi></math></mjx-assistive-mml></mjx-container></span><br></p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="6" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mo class="mjx-n"><mjx-c class="mjx-c21D2"></mjx-c></mjx-mo><mjx-mi class="mjx-i" space="4"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi><mjx-mo class="mjx-n" space="3"><mjx-c class="mjx-c2212"></mjx-c></mjx-mo><mjx-mi class="mjx-i" space="3"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mn class="mjx-n" space="4"><mjx-c class="mjx-c30"></mjx-c></mjx-mn></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mo>⇒</mo><mi>A</mi><mo>-</mo><mi>B</mi><mo>=</mo><mn>0</mn></math></mjx-assistive-mml></mjx-container></span><br></p></span></p>"""
    html_res = replace_mathjax_with_images(html_content)
    # print(html_res)
    return html_res
