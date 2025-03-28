import logging
import math
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


def get_image(mathjax_container,mathjax, uuid_image_path):
    try:
        # Prepare the HTML content with the provided MathJax string
        if (mathjax_container == "quizrr"):
            try:
                html_text = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>MathJax Image Automation</title>
                    <style>
                        body, html {{
                            margin: 0;
                            padding: 0;
                            overflow: hidden;
                            height: 100%;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                        }}
                        #math-content {{
                            padding: 20px;
                            text-align: left;
                            transform-origin: center center;
                        }}
                    </style>
                    <link href="https://fonts.googleapis.com/css?family=Noto+Sans&display=swap" rel="stylesheet">
                </head>
                <body>
                    <div id="math-content">
                        {mathjax}
                    </div>
                    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
                    <script type="text/javascript"
                    src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>
                    <script type="text/javascript"
                        src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.0.0/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>
                    <script type="text/javascript"
                        src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.6/MathJax.js?config=TeX-MML-AM_HTMLorMML"></script>
                    
                    <script type="text/javascript">
                        MathJax.Hub.Config({{
                            tex2jax: {{
                                inlineMath: [["$","$"],["\\(","\\)"]],
                                processEscapes: true
                            }}
                        }});
                        
                    </script>
                </body>
                </html>
                '''
                # print("******************************")
                # print(html_text)
                # print("******************************")
                html_text = html_text.format(mathjax=mathjax)
                encoded_html = urllib.parse.quote(html_text)
                # service = Service(ChromeDriverManager().install())
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
                options.add_argument("--disable-dev-shm-usage")  # Run in background
                options.headless = True  # Enable headless mode if no GUI is needed
                driver = webdriver.Chrome(service=service, options=options)

                # Load the HTML content directly
                driver.get(f"data:text/html;charset=utf-8,{encoded_html}")

                # Wait for MathJax to render (adjust the timeout as necessary)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "math-content"))
                )


                # Wait a bit for rendering to stabilize
                time.sleep(2)

                # Find the MathJax container element
                math_element = driver.find_element(By.ID, "math-content")
                # math_element = driver.find_all(By.TAG,"body")

                # math_element = driver.find_element(By.CLASS_NAME, "math-content")
                # math_element = driver.find_element(By.CLASS_NAME, "math-tex")

                # driver.save_screenshot(uuid_image_path)
                # Take a screenshot of just the MathJax element
                math_element.screenshot(uuid_image_path)

                # Cleanup
                driver.quit()
                return True
            except Exception as e:

                print(str(e))
                logging.error(f"error in image: "+str(mathjax))
                logging.error(f"Error in get_image: "+str(e))
                return False
        if(mathjax_container =='math-tex'):
            print('yes')
            # scripts updated on 06/06/24 for link to test , previous was excel to test
            #     <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
            #         <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js" integrity="sha256-4
            # <script>
            html_text = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>MathJax Image Automation</title>
                <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400&display=swap" rel="stylesheet">

                <meta charset="UTF-8">
                <title>MathJax Image Automation</title>
                <style>
                    body, html {{
                        
                        overflow: hidden;
                        height: 100%;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        font-family: 'Lato', sans-serif !important;
                        font-size: 16px !important;
                    }}
                    #math-content {{
                        
                        padding: 2px;
                        text-align: center;
                        transform-origin: center center;
                    }}
                </style>
                <link href="https://fonts.googleapis.com/css?family=Noto+Sans&display=swap" rel="stylesheet">

            </head>
            <body>
                <div id="math-content">
                    {mathjax}
                </div>
            </body>
            <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
                <script type="text/javascript"
        src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
        </script>


                    window.onload = function() {{
                        
                        document.getElementById('math-content').style.height =
                            document.querySelector('.MathJax').getBoundingClientRect().height+5 + 'px';
                    }};
                </script>
            </html>
            '''
            # print("******************************")
            # print(html_text)
            # print("******************************")
            encoded_html = urllib.parse.quote(html_text)
            # service = Service(ChromeDriverManager().install())
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
            options.add_argument("--disable-dev-shm-usage")  # Run in background
            # Setup WebDriver
            
            options.headless = True  # Enable headless mode if no GUI is needed
            driver = webdriver.Chrome(service=service, options=options)

            # Use the data URI scheme to load the HTML content directly
            driver.get(f"data:text/html;charset=utf-8,{encoded_html}")

            # Wait for MathJax to render (adjust the timeout as necessary)
            # WebDriverWait(driver, 10).until(lambda x: driver.execute_script("hey"))
                # WebDriverWait(driver, 10).until(lambda x: driver.execute_script("return MathJax.isReady();"))

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "math-content"))
            )

            # Wait a bit for rendering to stabilize
            # time.sleep(2)

            # Find the MathJax container element
            math_element = driver.find_element(By.ID, "math-content")
            # math_element = driver.find_all(By.TAG,"body")

            # math_element = driver.find_element(By.CLASS_NAME, "math-content")
            # math_element = driver.find_element(By.CLASS_NAME, "math-tex")

            # driver.save_screenshot(uuid_image_path)
            # Take a screenshot of just the MathJax element
            math_element.screenshot(uuid_image_path)

            # Cleanup
            driver.quit()
            return True
        elif(mathjax_container == 'katex'):
            # print(mathjax)
            html_text = f'''
            <!DOCTYPE html>
            <html>
            <head>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.13.18/dist/katex.min.css">

            <meta charset="UTF-8">
                <title>MathJax Image Automation</title>
                <style>
                    body, html {{
                        
                        overflow: hidden;
                        height: 100%;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        font-family: 'Lato', sans-serif !important;
                        font-size: 16px !important;
                    }}
                    #math-content {{
                        
                        
                        text-align: center;
                        transform-origin: center center;
                    }}
                </style>
            </head>
            <body>
                <div id="math-content">
                    {mathjax}
                </div>
            </body>
                <script src="https://cdn.jsdelivr.net/npm/katex@0.13.18/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.13.18/dist/contrib/auto-render.min.js"></script>

    <!-- Automatically render all LaTeX equations on the page -->
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            renderMathInElement(document.body);
        }});
    </script>
        <script>

                    
            </html>
            '''
            # height was 65 phele
            # print("******************************")
            # print(html_text)
            # print("******************************")
            encoded_html = urllib.parse.quote(html_text)
            # service = Service(ChromeDriverManager().install())
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
            options.add_argument("--disable-dev-shm-usage")  # Run in background
            # Setup WebDriver
            
            options.headless = True  # Enable headless mode if no GUI is needed
            driver = webdriver.Chrome(service=service, options=options)

            # Use the data URI scheme to load the HTML content directly
            driver.get(f"data:text/html;charset=utf-8,{encoded_html}")

            # Wait for MathJax to render (adjust the timeout as necessary)
            # WebDriverWait(driver, 10).until(lambda x: driver.execute_script("hey"))
                # WebDriverWait(driver, 10).until(lambda x: driver.execute_script("return MathJax.isReady();"))

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "math-content"))
            )

            # Wait a bit for rendering to stabilize
            time.sleep(5)

            # Find the MathJax container element
            math_element = driver.find_element(By.ID, "math-content")



            # Take a screenshot of just the MathJax element
            math_element.screenshot(uuid_image_path)

            # Cleanup
            driver.quit()
            return True
        else:
            html_text = f'''
            <!DOCTYPE html>
            <html>
            <head>
            <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400&display=swap" rel="stylesheet">

            <meta charset="UTF-8">
                <title>MathJax Image Automation</title>
                <style>
                    body, html {{
                        
                        overflow: hidden;
                        height: 100%;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        font-family: 'Lato', sans-serif !important;
                        font-size: 16px !important;
                    }}
                    #math-content {{
                        
                        
                        text-align: center;
                        transform-origin: center center;
                    }}
                </style>
            </head>
            <body>
                <div id="math-content">
                    {mathjax}
                </div>
            </body>
                <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
                <script type="text/javascript"
        src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
        </script>
        <script>

                    
            </html>
            '''
            # height was 65 phele
            # print("******************************")
            # print(html_text)
            # print("******************************")
            encoded_html = urllib.parse.quote(html_text)
            # service = Service(ChromeDriverManager().install())
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
            options.add_argument("--disable-dev-shm-usage")  # Run in background
            # Setup WebDriver
            
            options.headless = True  # Enable headless mode if no GUI is needed
            driver = webdriver.Chrome(service=service, options=options)

            # Use the data URI scheme to load the HTML content directly
            driver.get(f"data:text/html;charset=utf-8,{encoded_html}")

            # Wait for MathJax to render (adjust the timeout as necessary)
            # WebDriverWait(driver, 10).until(lambda x: driver.execute_script("hey"))
                # WebDriverWait(driver, 10).until(lambda x: driver.execute_script("return MathJax.isReady();"))

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "math-content"))
            )

            # Wait a bit for rendering to stabilize
            time.sleep(1)

            # Find the MathJax container element
            math_element = driver.find_element(By.ID, "math-content")



            # Take a screenshot of just the MathJax element
            math_element.screenshot(uuid_image_path)

            # Cleanup
            driver.quit()
            return True

    except Exception as e:
        print(str(e))
        logging.error(f"error in image: "+str(mathjax))
        logging.error(f"Error in get_image: "+str(e))
        return False
def get_table_image(table_container, uuid_image_path):
    # Prepare the HTML content with the provided MathJax string
    html_text = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>MathJax Image Automation</title>
        <style>
        
            body, html {{
                margin: 5px;
                padding: 5px;
                overflow: hidden;
                height: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            #math-content {{
                
                padding: 2px;
                text-align: center;
                transform-origin: center center;
            }}
        </style>
    </head>
    <body>
        <div id="math-content">
            {table_container}
        </div>
    </body>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js" integrity="sha256-4 
        </script>
    </html>
    '''
    # print("******************************")
    # print(html_text)
    # print("******************************")
    encoded_html = urllib.parse.quote(html_text)
    # service = Service(ChromeDriverManager().install())
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
    options.add_argument("--disable-web-security")
    options.add_argument('--allow-file-access-from-files')
    options.add_argument('--font-render-hinting=none')
    options.add_argument("--disable-dev-shm-usage")  # Run in background
    # options.add_argument(f"--font-family='Kruti Dev 010'")  # Set custom font family

    # Setup WebDriver
    
    options.headless = False  # Enable headless mode if no GUI is needed
    driver = webdriver.Chrome(service=service, options=options)

    # Use the data URI scheme to load the HTML content directly
    driver.get(f"data:text/html;charset=UTF-8,{encoded_html}")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "math-content"))
    )
    math_element = driver.find_element(By.ID, "math-content")
    math_element.screenshot(uuid_image_path)

    # Cleanup
    driver.quit()
    return True



image_folder_path = "/var/www/html/images"
# Public_IP = "https://fc.edurev.in/images"
Public_IP = "http://167.172.89.41/images"


def find_top_most_parent_span(element):
    current = element
    while current.parent and current.parent.name == 'span':
        current = current.parent
    return current
processed_parents = set()
top_most_parents = []
def get_parent(soup):
    top_most_parents =[]
    for element in soup.find_all(lambda tag: tag.name == 'span' and tag.has_attr('data-mathml')):
        top_most_parent = find_top_most_parent_span(element)
        
        # Using id or object identity to avoid duplicates
        parent_id = id(top_most_parent)  # Fallback to object ID if no 'id' attribute
        
        if parent_id not in processed_parents:
            processed_parents.add(parent_id)
            top_most_parents.append(top_most_parent)
            # Mark the parent as 'done'
        
    return top_most_parents

def contains_katex(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # print(soup)
    # Check for KaTeX CSS or JS links
    katex_css = soup.find('link', {'href': lambda href: href and 'katex.min.css' in href})
    katex_js = soup.find('script', {'src': lambda src: src and 'katex.min.js' in src})

    # Check for KaTeX math delimiters in the text
    contains_inline_katex = r'\(' in soup.text or r'\)' in soup.text
    contains_block_katex = r'\[' in soup.text or r'\]' in soup.text

    # Check for any element with the 'katex' class
    katex_class = soup.find_all(class_='katex')
    # print(katex_class)
    # If any of the conditions are True, we assume it contains KaTeX
    if len(katex_class) > 0:
        return True, ["1"]
    if katex_css or katex_js or contains_inline_katex or contains_block_katex or katex_class:
        return True, [soup]
    return False ,[]
def replace_mathjax_with_images(html_content,quizrr = False):
    try:
        """
        Parse HTML content, identify MathJax/LaTeX, convert to images, and replace original content with images.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        first_element = "mtd"
        for element in soup.find_all('script'):
            element.decompose() 
        # elements = soup.find_all('span',class_="MJX_Assistive_MathML")
        # for element in elements:
        #     print(element)
        #     element.extract()
        if not quizrr:
            elements = soup.find_all('nobr')
            first_element ="mtd1"
            for element in elements:
                # print(element)
                element.extract()
        # print(soup)

        textBook = False
        attribute = "mathMlContainer"
        ktx_check = 0
        # Adjust this selector based on your HTML structure
        math_elements = soup.find_all(class_="mathMlContainer")
        # print(soup)
        if(len(math_elements) == 0) :
            math_elements = soup.find_all('span',class_=first_element)
            
            # data-mathm
            if (len(math_elements) == 0) :
                math_elements = soup.find_all("mjx-container")
                if (len(math_elements) == 0) :
                    math_elements = soup.find_all('span',class_='math-tex')
                    # print("***********************************")
                    # print(str(soup))
                    # print("***********************************")
                    if (len(math_elements) == 0) :
                        # print("check1")
                        math_elements = soup.find_all("span", class_="MathJax")
                        if (len(math_elements) == 0) :

                            math_elements = get_parent(soup)
                            
                            if ( len(math_elements) == 0) :
                                # math_elements = soup.find_all(class_='katex')
                                # print(math)
                                contains_ktx, math_elements_ = contains_katex(str(soup))
                                if(contains_ktx == True):
                                    if math_elements_[0] == "1":
                                        math_elements = soup.find_all(class_='katex')
                                    else:
                                        math_elements = [soup]
                                        ktx_check =1
                                # print(math_elements_)
                                # print(contains_ktx)
                                if(len(math_elements) == 0 or contains_ktx == False):
                                    return str(soup)
                                else:
                                    attribute = "katex"
                                    textBook = True
                                    # print(katex_elements
                            else:
                                textBook = True
                                attribute = "data-mathml"
                        else:
                            textBook = True
                            attribute = "mathJax"

                    else:
                        textBook = True
                        attribute = "math-tex"
                        # print(math_elements)

                    
                else:
                    textBook = True
                    # mjx_container =True
                    attribute = "mjx-container"

                    mjx_container =False
            else:
                new_maths_elements=[]
                for element in math_elements:
                    if element.get_text() != "":
                        new_maths_elements.append(element)
                math_elements = new_maths_elements
                attribute = "mjx-container"
                textBook = True
        else:
            attribute = "mathMlContainer"
            textBook = True
            # math_elements = soup.find_all(class_="mathMlContainer")
        # print(attribute)


        # print(soup)
        # print(math_elements)
        for elements in math_elements:
            if textBook == True:
                uuid_str = str(uuid.uuid4())
                # Assuming the LaTeX string can be directly obtained from the element's text
                image_url = f"{image_folder_path}/{uuid_str}.png"
                # element = elements.get('data-mathml')
                if(attribute == "mjx-container" ):
                    element = elements
                elif(attribute == "mathMlContainer" ):
                    element = elements
                elif(attribute == "math-tex" ):
                    element = elements
                else:
                    element = elements
                    # element = elements.get('data-mathml')
                # print(elements)
                # print(element)
                if get_image(attribute,element, image_url):
                    image_url =f"{Public_IP}/{uuid_str}.png"
                    # print(soup)
                    new_img_tag = soup.new_tag("img", src=image_url)
                    # print("############ IMAGE TAG ##################")
                    # print(new_img_tag)
                    # print("############ IMAGE TAG ##################")
                    if(attribute == 'data-mathml'): 
                        # print("############ PARENT TAG ##################")
                        # print(element)
                        # print("############ PARENT TAG ##################")
                        element_to_replace = element.find(lambda tag: tag.name == 'span' and tag.has_attr('data-mathml'))
                        # element_to_replace = elements.find_all(lambda tag: tag.name == 'span' and tag.has_attr('data-mathml'))
                        # print("############ INNER TAG ##################")
                        # print(element_to_replace)
                        # print("############ INNER TAG ##################")
                        if element_to_replace:
                            element_to_replace.replace_with(new_img_tag)
                    else:
                        if(ktx_check ==1):
                            # create soup with katex image :
                            soup = BeautifulSoup(str(new_img_tag), 'html.parser')
                        else:
                            elements.replace_with(new_img_tag)
                        
            else:
                uuid_str = str(uuid.uuid4())
                # Assuming the LaTeX string can be directly obtained from the element's text
                image_url = f"{os.getcwd()}/{image_folder_path}/{uuid_str}.png"
                if get_image(attribute,elements, image_url):
                    new_img_tag = soup.new_tag("img", src=image_url)
                    print(new_img_tag)
                    if(attribute == 'data-mathml'): 
                        element_to_replace = elements.find_all(lambda tag: tag.name == 'span' and tag.has_attr('data-mathml'))
                        element_to_replace.replace_with(new_img_tag)
                    else:

                        elements.replace_with(new_img_tag)
        # print(soup.prettify())
        return str(soup)
    except Exception as e:
        print(str(e))
        logging.info("error while making image of mathjax : "+str(e))
    
    

def replace_tables_with_images(html_content):
    """
    Parse HTML content, identify <table> elements, convert to images, and replace original <table> elements with images.

    Parameters:
    - html_content: A string containing the HTML content.
    - image_folder_path: The file system path where images should be stored.
    - Public_IP: The public IP address or domain where the images will be accessible.

    Returns:
    A string of the modified HTML content with <table> elements replaced by <img> elements linking to images of the tables.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table_elements = soup.find_all('table')
    
    for table in table_elements:
        uuid_str = str(uuid.uuid4())
        image_url = f"{image_folder_path}/{uuid_str}.png"

        # You would need to implement the get_table_image function. It should capture the table element,
        # convert it to an image, and save it to the provided image_url.
        if get_table_image(table, image_url):
            public_image_url = f"{Public_IP}/{uuid_str}.png"
            # print(public_image_url)
            new_img_tag = soup.new_tag("img", src=public_image_url)
            table.replace_with(new_img_tag)

    return str(soup)


# Function to map MathML to LaTeX

# Convert the example HTML to LaTeX

# Example HTML content
def mathTexToImgFun(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    math_elements = soup.find_all('span',class_="math-tex")
    for elements in math_elements:
        uuid_str = str(uuid.uuid4())
        # Assuming the LaTeX string can be directly obtained from the element's text
        image_url = f"{image_folder_path}/{uuid_str}.png"
        element = elements.get_text()
        if get_image("math-tex",element, image_url):
            image_url =f"{Public_IP}/{uuid_str}.png"
            new_img_tag = soup.new_tag("img", src=image_url)
            elements.replace_with(new_img_tag)
    return str(soup)
def excelRun(html_content,quizrr = False):

    # html_content = """<h3 ng-bind="vernacularStaticTextContent['ts_ques_detail'][8]" class="ng-binding">Explanation:</h3> <p> <span class="question_exp ng-binding" ng-bind-html="toTrustedHTML(show_single_data[6])"><p>Given-</p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="2" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mfrac><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="3"><mjx-c class="mjx-c2B"></mjx-c></mjx-mo><mjx-mfrac space="3"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mn class="mjx-n" space="4"><mjx-c class="mjx-c32"></mjx-c></mjx-mn></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mfrac><mi>A</mi><mi>B</mi></mfrac><mo>+</mo><mfrac><mi>B</mi><mi>A</mi></mfrac><mo>=</mo><mn>2</mn></math></mjx-assistive-mml></mjx-container></span><br></p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="3" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mo class="mjx-n"><mjx-c class="mjx-c21D2"></mjx-c></mjx-mo><mjx-mfrac space="4"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="3"><mjx-c class="mjx-c2B"></mjx-c></mjx-mo><mjx-mfrac space="3"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mn class="mjx-n" size="s"><mjx-c class="mjx-c31"></mjx-c></mjx-mn></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mstyle size="s"><mjx-mfrac><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac></mjx-mstyle></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mn class="mjx-n" space="4"><mjx-c class="mjx-c31"></mjx-c></mjx-mn><mjx-mo class="mjx-n" space="3"><mjx-c class="mjx-c2B"></mjx-c></mjx-mo><mjx-mfrac space="3"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mn class="mjx-n" size="s"><mjx-c class="mjx-c31"></mjx-c></mjx-mn></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mn class="mjx-n" size="s"><mjx-c class="mjx-c31"></mjx-c></mjx-mn></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mo>⇒</mo><mfrac><mi>A</mi><mi>B</mi></mfrac><mo>+</mo><mfrac><mn>1</mn><mstyle display=""><mfrac><mi>A</mi><mi>B</mi></mfrac></mstyle></mfrac><mo>=</mo><mn>1</mn><mo>+</mo><mfrac><mn>1</mn><mn>1</mn></mfrac></math></mjx-assistive-mml></mjx-container></span></p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="4" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mo class="mjx-n"><mjx-c class="mjx-c21D2"></mjx-c></mjx-mo><mjx-mfrac space="4"><mjx-frac><mjx-num><mjx-nstrut></mjx-nstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi></mjx-num><mjx-dbox><mjx-dtable><mjx-line></mjx-line><mjx-row><mjx-den><mjx-dstrut></mjx-dstrut><mjx-mi class="mjx-i" size="s"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-den></mjx-row></mjx-dtable></mjx-dbox></mjx-frac></mjx-mfrac><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mn class="mjx-n" space="4"><mjx-c class="mjx-c31"></mjx-c></mjx-mn></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mo>⇒</mo><mfrac><mi>A</mi><mi>B</mi></mfrac><mo>=</mo><mn>1</mn></math></mjx-assistive-mml></mjx-container></span><br></p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="5" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mo class="mjx-n"><mjx-c class="mjx-c21D2"></mjx-c></mjx-mo><mjx-mi class="mjx-i" space="4"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mi class="mjx-i" space="4"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mo>⇒</mo><mi>A</mi><mo>=</mo><mi>B</mi></math></mjx-assistive-mml></mjx-container></span><br></p><p><span class="mathMlContainer" contenteditable="false"><mjx-container class="MathJax CtxtMenu_Attached_0" jax="CHTML" tabindex="0" ctxtmenu_counter="6" style="font-size: 119.5%; position: relative;"><mjx-math class="MJX-TEX" aria-hidden="true"><mjx-mo class="mjx-n"><mjx-c class="mjx-c21D2"></mjx-c></mjx-mo><mjx-mi class="mjx-i" space="4"><mjx-c class="mjx-c1D434 TEX-I"></mjx-c></mjx-mi><mjx-mo class="mjx-n" space="3"><mjx-c class="mjx-c2212"></mjx-c></mjx-mo><mjx-mi class="mjx-i" space="3"><mjx-c class="mjx-c1D435 TEX-I"></mjx-c></mjx-mi><mjx-mo class="mjx-n" space="4"><mjx-c class="mjx-c3D"></mjx-c></mjx-mo><mjx-mn class="mjx-n" space="4"><mjx-c class="mjx-c30"></mjx-c></mjx-mn></mjx-math><mjx-assistive-mml unselectable="on" display="inline"><math xmlns="http://www.w3.org/1998/Math/MathML"><mo>⇒</mo><mi>A</mi><mo>-</mo><mi>B</mi><mo>=</mo><mn>0</mn></math></mjx-assistive-mml></mjx-container></span><br></p></span></p>"""
    html_res = replace_mathjax_with_images(html_content,quizrr)
    html_res = replace_mathjax_with_images(html_content,quizrr)
    html_res = replace_tables_with_images(html_res)
    # print(html_res)
    return html_res
