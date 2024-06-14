import base64
from flask import Flask, request, jsonify
import requests
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, Comment
import re
import matplotlib.pyplot as plt
from handleLatex import convert_latex
from handleLatex import latex_to_image
from LatexToImage import replace_tables_with_images
from LatexToImage import excelRun
from urllib.parse import urljoin, urlparse
import html
# try:
#     from HTMLParser import HTMLParser
# except ImportError:
#     from html.parser import HTMLParser

from removeWaterMark import download_image, remove_background_and_convert_to_bw
import datetime
import time
import json
# import spacy
import random
import openai 
from dotenv import load_dotenv
from pathlib import Path
import subprocess
from icrawler.builtin import GoogleImageCrawler
# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Rest of the code...
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from sentence_transformers import SentenceTransformer, util
import logging
import os
from dotenv import load_dotenv
logging.basicConfig(filename='currentAffairslogfile.log', level=logging.INFO)

model = SentenceTransformer('all-MiniLM-L6-v2')
locations_of_images = "/var/www/html/images/"
Public_IP = "http://52.139.218.113/images/"


from flask_cors import CORS
app = Flask(__name__)
CORS(app)

def simplify_latex_limits(latex_code):
    # Replace the verbose limit syntax with the conventional syntax
    simplified_code = latex_code.replace(r"\mathop {\lim }\limits", r"\lim")
    # Additional cleanup if necessary, for example removing extra spaces or handling other cases
    return simplified_code
   
def scrape_text(text):
    # Setup Selenium WebDriver
    # latex to image 
    html_text = excelRun(text)
    soup = BeautifulSoup(html_text, 'html.parser')
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()
    for style in soup.find_all('style'):
        style.extract()
    for nav in soup.find_all('nav'):
        nav.extract()
    header_tags = soup.find_all('header')
    for tag in header_tags:
        tag.clear()
    tags_to_remove = ['footer','ins','iframe','nav','aside','link','meta', 'option', 'header','style',
                      'label', 'input', 'script', 'button']
    for tag in tags_to_remove:
        for element in soup.find_all(tag):
            element.decompose()  # Remove the tag and its content
    empty_div_tags = soup.find_all('div', class_=True)
    for tag in empty_div_tags:
        if not tag.text.strip():
            tag.decompose()
    empty_li_tags = soup.find_all('li', class_=True)
    for tag in empty_li_tags:
        if not tag.text.strip():
            tag.decompose()
    empty_ul_tags = soup.find_all('ul', class_=True)
    for tag in empty_ul_tags:
        if not tag.text.strip():
            tag.decompose()

    body_tag = soup.find('body')
    if body_tag:
        body_content = body_tag.prettify()
    else:
        body_content = soup.prettify()
    # print(body_content)

    # Write the body content to the output file
    html = body_content
    # print(html)

    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(html, 'html.parser')

    # Extract text from each tag while maintaining the order
    text_list = []
    processed_texts = set()
    first = True
    h2_tags = 0
    count_p = 0
    previous_content_length = 0
    for tag in soup.descendants:
        if tag.name in ['h2']:
            h2_tags += 1

    for tag in soup.descendants:
        if tag.name in ['p', 'img', 'span', 'h1', 'h2', 'h3', 'tr', 'td', 'h4', 'h5', 'h6', 'ul', 'li']:
            if tag.name == 'span':
                if str(tag) not in processed_texts:
                    text = str(tag)
                    processed_texts.add(text)
                    # Handle <img> tags inside <span> separately
                    for img_tag in tag.find_all('img'):
                        if str(img_tag) not in processed_texts:
                            img_text = str(img_tag)
                            processed_texts.add(img_text)
                            text_list.append(img_text)
            elif tag.name == 'img':
                if str(tag) not in processed_texts:
                    text = str(tag)
                    processed_texts.add(text)
                    text_list.append(text)
            else:
                text = tag.get_text(strip=True)
                if text and text not in processed_texts:
                    text = re.sub(r'\s+', ' ', text)
                    processed_texts.add(text)
                    text = "<" + tag.name + ">" + text + "</" + tag.name + ">"
                    previous_content_length += len(text)
                    if (tag.name == 'h2' and previous_content_length > 700):
                        text = "\n ********** \n" + text
                        previous_content_length = 0
                    elif (tag.name == 'p' and previous_content_length > 1500):
                        text = text + "\n ********** \n"
                        previous_content_length = 0
                        first = False
                else:
                    processed_texts.add(str(tag))
                text_list.append(text)
                if (tag.name == 'h2'):
                    text_list.append("\n ")
                    
      
    result = ""
    for text in text_list:
        result += text + '\n'
    # print(result)
    result = re.sub(r'\n+', '', result)
    result_in_parts = result.split("**********")
    output = ""
    first = True
    for text in result_in_parts:
        if (len(text) != 0):
            if (first):
                first = False
                output += text
            else:
                if (len(text) < 100):
                    output += text
                else:

                    output += "\n ********** \n"+text
    return output



def contains_latex(text):
    # A simple check for LaTeX code. You can make this more sophisticated.
    return "$" in text or "\\" in text
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

def convert_latex_to_image(matches, image_path):
    # tex_file = f"{uuid.uuid4()}.tex"
    for match in matches:
        # match = "$" + match + "$"
        print("match: "+match)
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, match, size=12, ha='center', va='center')
        ax.axis('off')
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        plt.close(fig)
        img_data = buffer.getvalue()

        # Now you can save the image, display it, or use it as needed
        # For example, to display the image:
        with open(image_path, 'wb') as f:
            f.write(img_data)
            print(image_path)
       
def ensure_math_mode(latex_code):
    # Enclose text in math mode using \( ... \) if not already enclosed
    return re.sub(r'\\\((.*?)\\\)', r'$\1$', latex_code)

def process_html_convert_latex_to_image(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = soup.find_all('p')
    
    for i, p in enumerate(paragraphs):
        if contains_latex(p.text):
            latex_code = p.text
            image_name = str(uuid.uuid4()) + '.png'
            image_path = os.path.join(locations_of_images, image_name)
            image_url = Public_IP + image_name
            # image_path = f"latex_image_{i}.png"
            print("latex code: "+latex_code)
            pattern = r'\\\(.*?\\\)'
            matches = re.findall(pattern, latex_code)
            convert_latex_to_image(matches, image_path)

            print("converted to latex "+image_url)
            p.string = f"<img src='{image_url}' alt='LaTeX image'>"
    
    return str(soup)

import requests
from lxml.html import fromstring
from itertools import cycle

def getScrollerTest(url):
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
   
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    

    driver.implicitly_wait(10)
    html_ = driver.execute_script("return document.documentElement.outerHTML")

    # Get page source after JavaScript execution
    # html = driver.page_source
    # print(html)
    driver.quit()  # Close the browser
    html_text = convert_latex(str(html_))
    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(html_text, 'html.parser')
    formatted_questions = {"questions":[]}
    if 'www.mockers.in/' in url:
        question_div = soup.find('ul', class_='ques-list')
        questions = question_div.find_all('li')
        for question in questions:
            
            question_text = question.find('div', class_='qsn-here').text.strip()
            for child in question.find('div', class_='qsn-here').children:
                if child.name == 'img':
                    image_url = child['src']
                    # image_url = urljoin(url, image_url)
                    new_img_tag = f'<img src="{image_url}" alt="Question Image">'
                    question_text += new_img_tag

            options = question.find_all('div', class_='form-group')
            option_texts = [opt.find('h6').text.strip() for opt in options]

            correct_option = question.find('label', class_='thisIsCorrect').find('span',class_="optionIndex").text.strip()
            # answer = f'Option {correct_option}: {option_texts[ord(correct_option) - ord("A")]}'
            answer = f'Option {correct_option}'
            # answer = f' {option_texts[ord(correct_option) - ord("A")]}'

            solution_text = question.find('div', class_='qn-solution').text.strip()

            formatted_question = f"\n{question_text}\n"
            # formatted_options = "\n".join([f"Option {chr(ord('A') + i)}: {option_texts[i]}" for i in range(len(option_texts))])
            formatted_options = []
            formatted_options.append(f" {option_texts[0]}")
            formatted_options.append(f" {option_texts[1]}")
            formatted_options.append(f" {option_texts[2]}")
            formatted_options.append(f" {option_texts[3]}")
            formatted_answer = f" {answer}\n"
            formatted_solution = f"\n{solution_text}"
            if 'Solutions' in formatted_solution:
                formatted_solution = formatted_solution.replace('Solutions','')
            formatted_questions.get("questions").append({"question":formatted_question, "options":formatted_options, "answer":formatted_answer, "solution":formatted_solution})

            # formatted_output = formatted_question + formatted_options + formatted_answer + formatted_solution
            # formatted_questions.append(formatted_output)
        # for i, formatted_question in enumerate(formatted_questions, start=1):
        #     print(f"Question {i}:\n{formatted_question}\n")\
        return formatted_questions
    elif 'https://www.educationquizzes.com/' in url:
        
        question_div = soup.find('div', class_='quiz__questions')
        questions = question_div.find_all('div', class_='quiz__question')
        for question in questions:
            question_text = question.find('div', class_='quiz__question__question').text.strip()
            question_image = question.find('div', class_='quiz__question__image')
            if question_image:
                image_url = question_image.find('img')['src']
                image_url = urljoin(url, image_url)
                new_img_tag = f'<img src="{image_url}" alt="Question Image">'
                question_text += new_img_tag
            options = question.find_all('div', class_='quiz__question__answers__answer')
            i=0
            for opt in options :
                if opt['data-iscorrect'] == "true":
                    if i == 0:
                        correct_option = 'A'
                    elif i == 1:
                        correct_option = 'B'
                    elif i == 2:
                        correct_option = 'C'
                    elif i == 3:
                        correct_option = 'D'
                i+=1
                    # correct_option = opt.text.strip()
            option_texts = [opt.text.strip() for opt in options]
            # option_texts = [opt.find('span').text.strip() for opt in options]
            # correct_option = question.find('div', class_='quiz__question__answers__answer', data-iscorrect="true").text.strip()
            # correct_option = question.find('div', class_='correct-answer').text.strip()
            answer = f'{correct_option}'
            solution_text = question.find('div', class_='quiz__question__result__helpful-comment').text.strip()

            formatted_question = f"\n{question_text}\n"
            # formatted_options = "\n".join([f"Option {chr(ord('A') + i)}: {option_texts[i]}" for i in range(len(option_texts))])
            formatted_options = []
            formatted_options.append(f" {option_texts[0]}")
            formatted_options.append(f" {option_texts[1]}")
            formatted_options.append(f" {option_texts[2]}")
            formatted_options.append(f" {option_texts[3]}")
            formatted_answer = f" {answer}\n"
            formatted_solution = f"\n{solution_text}"
            formatted_questions.get("questions").append({"question":formatted_question, "options":formatted_options, "answer":formatted_answer, "solution":formatted_solution})

        return formatted_questions
    elif "https://testseries.edugorilla.com" in url:
        # url = https://testseries.edugorilla.com/my_report/0/6217196
        formatted_questions = {
            'questions':[]
        }
        rid = url.split('/')[-1]
        import random
        
        url_to_get_sid = "https://testseries.edugorilla.com/api/v1/testapp/testreport/"+rid
        User_Agent='PostmanRuntime/7.37.3'
        # cookies ='_gcl_au=1.1.199337151.1717414285; _ga=GA1.1.453678585.1717414285; _fbp=fb.1.1717414286838.1680460923; MicrosoftApplicationsTelemetryDeviceId=93bce8ac-e995-44db-941e-0f8be7664ef3; MicrosoftApplicationsTelemetryFirstLaunchTime=2024-06-03T11:31:33.295Z; eg_user="2|1:0|10:1717418631|7:eg_user|56:NTc2ODExNDtiZjJiNDE3NzNmMjg0NjY2YTQxYjgzZTI4NzUxOTQxZQ==|7b296cb981c31352d57ca978c4d24f71d5c69f2c5aaa86d49225deea7912cc86"; lang=1; client_meta=%7B%22android_main_app_url%22%3A%22https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.app.testseries.edugorilla%22%2C%22homepage_masthead%22%3A%22%7B%5C%22show_banner%5C%22%3A%20%5C%221%5C%22%2C%20%5C%22background%5C%22%3A%20%5B%5C%22c92627%5C%22%2C%20%5C%22f8693d%5C%22%5D%2C%20%5C%22show_actv_key%5C%22%3A%20%5C%221%5C%22%2C%20%5C%22usm_so%5C%22%3A%20%5C%220%5C%22%2C%20%5C%22usm_cceg%5C%22%3A%2040000000%7D%22%2C%22url_advertise_with_us%22%3A%22%22%7D; profile_img_url=%2Fstatic%2Fimages%2Fuser_profile.png; _ga_GQ7KE47SJQ=GS1.1.1717476445.3.1.1717476480.25.0.1830568007'
        cookies ='_gcl_au=1.1.199337151.1717414285; _ga=GA1.1.453678585.1717414285; _fbp=fb.1.1717414286838.1680460923; MicrosoftApplicationsTelemetryDeviceId=93bce8ac-e995-44db-941e-0f8be7664ef3; MicrosoftApplicationsTelemetryFirstLaunchTime=2024-06-03T11:31:33.295Z; lang=1; eg_user="2|1:0|10:1717745023|7:eg_user|56:NTc2ODExNDs0NmM3NGNlOTJlNjY0NWZiOWYzYTUzNDQ1ODIyZTcxNQ==|2908dec869015f490a28395eaaa2850443b96cbe03646699651ceddb6944c2d2"; _ga_GQ7KE47SJQ=GS1.1.1717745012.14.1.1717745025.47.0.1783449336; profile_img_url=%2Fstatic%2Fimages%2Fuser_profile.png'
        response = requests.get(url_to_get_sid, headers={'Cookie': cookies})
        print("url_to_get_sid: ",url_to_get_sid)
        print("Response status code: ", response.status_code)
        print("Response headers: ", response.headers)
        print("cookies: " ,cookies)
        response = response.json()
        scorecards = response['result']['data']['scorecard'][0]
        sid = ""
        for scorecard in scorecards:
            if type(scorecard) == str and "Section" not in scorecard:
                sid = scorecard
        url_to_get_test = "https://testseries.edugorilla.com/api/v1/mytests/submitdata"
        params = {
            "rid":rid,
            "sid":sid
        }
        response = requests.get(url_to_get_test, headers={"Cookie": cookies}, params=params)
        response = response.json()

        questions = response['result']['data']['sec_questions']
        for question in questions :

            question_text = question[2]
            formatted_options = question[3]
            for option in formatted_options:
                option = process_html_convert_latex_to_image(option)
            correct_option = chr(ord('A') + question[4][0])
            solution_text = question[6]
            paragraph_id_1 = question[13]
            paragraph_id_2 = question[14]
            if paragraph_id_2 != None:
                paragraph = response['result']['data']['passages'][paragraph_id_2][paragraph_id_1]
                question_text = paragraph+"\n" +question_text
                
            formatted_question = f"\n{question_text}\n"
            # formatted_options = []
            # formatted_options.append(f" {options[0]}")
            # formatted_options.append(f" {options[1]}")
            # formatted_options.append(f" {options[2]}")
            # formatted_options.append(f" {options[3]}")
            formatted_answer = f" {correct_option}\n"
            formatted_solution = f"\n{solution_text}"
            formatted_question = process_html_convert_latex_to_image(formatted_question)
            formatted_answer = process_html_convert_latex_to_image(formatted_answer)
            formatted_solution = process_html_convert_latex_to_image(formatted_solution)
            formatted_questions.get("questions").append({"question":formatted_question, "options":formatted_options, "answer":formatted_answer, "solution":formatted_solution})
    elif "https://testbook.com/" in url:
        test_id = url.split('?')[0].split('/')[-1]
        # ashwini code,sushil code
        auth_codes = [
            'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjY1Nzk5NTRmODBiN2U5MGU2NDhkN2VjZCIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNC0wNy0wNFQwNjo1NToxMS4xNzQ4OTk0MzlaIiwiaWF0IjoiMjAyNC0wNi0wNFQwNjo1NToxMS4xNzQ4OTk0MzlaIiwibmFtZSI6IkFzaHdhbmkiLCJlbWFpbCI6Im1pc2hyYWFzaHdhbmkwNzNAZ21haWwuY29tIiwib3JnSWQiOiIiLCJpc0xNU1VzZXIiOmZhbHNlLCJyb2xlcyI6InN0dWRlbnQifQ.osA0FinT0lTKuHBFJcczsrAr5S9cGfXKQ8gZVnUGLXPZcLm1NzUh-z6vNgJ-yIniWF97J7S9LHSc6GSEiDzXXzZhyLquTtpdZ09pfyJIjhKP4W6FAQEA3VnxS9nwQ9pVcjJJxhvERtZSLokh8GXtL_PcTqUCvlJZdSENmdy1aDg',
            'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjViZWE2NTlkNmZmNmZlMjFhNDczZmNkMiIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNC0wNy0wM1QwNDoxMzoyOC41NjkyODE5ODJaIiwiaWF0IjoiMjAyNC0wNi0wM1QwNDoxMzoyOC41NjkyODE5ODJaIiwibmFtZSI6Imx1Y2t5IiwiZW1haWwiOiJsdWNreXRhbmVqYTk5OUBnbWFpbC5jb20iLCJvcmdJZCI6IiIsImlzTE1TVXNlciI6ZmFsc2UsInJvbGVzIjoic3R1ZGVudCJ9.iCEKSYJmciL8Znd4XaEtU5Wna0v07Y9n1jMxmPKsS7ELtGqfxQhuw196hM_E4blvzoFRMoOcvgO2ZgEXWygHysFP-RJMWGN18Yhzc9g6xQtpZiI6912kgMDU5mnnzm6u31hno5J66rXukLc3bkiyDLQLnXVx8H1-4-Z9LYre0k0'
        ]
        params = {
            'auth_code':"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjViZWE2NTlkNmZmNmZlMjFhNDczZmNkMiIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNC0wNy0wM1QwNDoxMzoyOC41NjkyODE5ODJaIiwiaWF0IjoiMjAyNC0wNi0wM1QwNDoxMzoyOC41NjkyODE5ODJaIiwibmFtZSI6Imx1Y2t5IiwiZW1haWwiOiJsdWNreXRhbmVqYTk5OUBnbWFpbC5jb20iLCJvcmdJZCI6IiIsImlzTE1TVXNlciI6ZmFsc2UsInJvbGVzIjoic3R1ZGVudCJ9.iCEKSYJmciL8Znd4XaEtU5Wna0v07Y9n1jMxmPKsS7ELtGqfxQhuw196hM_E4blvzoFRMoOcvgO2ZgEXWygHysFP-RJMWGN18Yhzc9g6xQtpZiI6912kgMDU5mnnzm6u31hno5J66rXukLc3bkiyDLQLnXVx8H1-4-Z9LYre0k0"
        }
        get_answere_url = f"https://api.testbook.com/api/v2/tests/{test_id}/answers".format(test_id)    
        get_questions_url = f"https://api.testbook.com/api/v2/tests/{test_id}".format(test_id)
        formatted_questions = {
        'questions':[]
        }
        response = requests.get(get_questions_url, params=params)
        # if test is not attempted
        #         {
        #     "success": false,
        #     "message": "You have not completed the test, can not serve solutions.",
        #     "curTime": "2024-06-05T11:38:08.758Z"
        # }
        answers = requests.get(get_answere_url, params=params)
        # h = HTMLParser()
        questions = response.json()['data']['sections']
        for section in questions:
            if section['questions'] :
                section_name = ""
                if 'title' in section:
                    section_name = section['title']
                
                for question in section['questions']:
                    formatted_options = []
                    question_data = question['en']['value']
                    if 'comp' in question['en']:
                       question_data = question['en']['comp'] + " \n" +question_data
                    
                    question_id = question['_id']
                    for option in question['en']['options']:
                        # option = html.unescape(option)
                        option = option['value']
                        option = html.unescape(option)
                        option = BeautifulSoup(option, 'html.parser')
                        formatted_options.append(str(option))
                    answer = answers.json()['data'][question_id]['correctOption']
                    question = html.unescape(question_data)
                    question = html.unescape(question)
                    answer = html.unescape(answer)
                    answer = html.unescape(answer)
                    solution = answers.json()['data'][question_id]['sol']['en']['value']
                    solution = html.unescape(solution)
                    solution = html.unescape(solution)
                    question = BeautifulSoup(question, 'html.parser')
                    answer = BeautifulSoup(answer, 'html.parser')
                    solution = BeautifulSoup(solution, 'html.parser')
                    answer = str(answer)
                    question = str(question)
                    solution = str(solution)

                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/key-point-image.png\" style=\"user-select: auto;\" width=\"26px\"/>','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/additional-information-image.png\" width=\"26px\"/>','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/key-point-image.png\" width=\"26px\"/>','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/hint-text-image.png\" width=\"26px\"/>','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/important-point-image.png\" width=\"26px\"/>','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/key-point-image.png\" width=\"26px\" />','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/additional-information-image.png\" width=\"26px\" /><strong><span style=\"vertical-align: middle;font-size: 21px;\">','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/in_news.png\" width=\"26px\">','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/shortcut-trick-image.png\" width=\"26px\">','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/alternate-methord-image.png\" width=\"26px\">','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/mistake-point-image.png\" width=\"26px\">','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/confusion-points-image.png\" width=\"26px\">','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/hint-text-image.png\" style=\"color: rgb(33, 37, 41);\" width=\"26px\">','')
                    solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/hint-text-image.png\" width=\"26px\">','')
                    solution = solution.replace('<img alt=\"\" src=\"//cdn.testbook.com/images/production/quesImages/quesImage56.png\">','')
                    solution = solution.replace('<img alt=\"\" src=\"//cdn.testbook.com/images/production/quesImages/quesImage56.png\" style=\"text-align: justify;\">','')
                    solution = solution.replace('<img alt=\"\" src=\"//storage.googleapis.com/tb-img/production/21/08/601920026219d63b9af13913_16298844340631.png\">','')
                    solution = solution.replace('<img alt=\"\" src=\"//storage.googleapis.com/tb-img/production/21/09/new_16311073401211.png\">','')
                    solution = solution.replace('<img alt=\"\" src=\"//cdn.testbook.com/images/production/quesImages/quesImage218.png\">','')
                    solution = solution.replace('<img src=\"//cdn.testbook.com/images/production/quesImage4.png\"/>','<strong>Additional Information</strong>')
                    solution = solution.replace('<img alt=\"\" src=\"//storage.googleapis.com/tb-img/production/21/09/6017b26a8181d1a29b65ffe4_16322947252551.png\">','')
                    solution = solution.replace('<img alt=\"\" src=\"//cdn.testbook.com/images/production/quesImages/quesImage398.png\" style=\"text-align: justify;\">','')
                    solution = solution.replace('<img alt=\"\" src=\"//cdn.testbook.com/images/production/quesImages/quesImage534.png\">','')
                    
                    
                    question_data = scrapeExcel(question_data)
                    answer = scrapeExcel(answer)
                    solution = scrapeExcel(solution)
                    for option in formatted_options:
                        option = scrapeExcel(option)
                    formatted_questions['questions'].append({
                        'question':question_data,
                        'options':formatted_options,
                        'answer':answer,
                        'solution':solution,
                        'section_name':section_name
                    })
        with open ('testbook.json','w') as f:
            json.dump(formatted_questions,f) 
    elif "https://www.tcyonline.com" in url:
        formatted_questions = {
        'questions':[]
        }
        formatted_options =[]
        # url = https://www.tcyonline.com/Analyse/decideURL.php?rqstP=analytics&testid=248228&testtakenid=54056318&WhichCategory=795850&action_retake=&type=QuestionWise
        testtakenid = url.split('&')[2].split('=')[1]  
        testid = url.split('&')[1].split('=')[1]
        print("testtakenid: ",testtakenid)
        print("testid: ",testid)
        get_first_question = "https://www.tcyonline.com/Analyse/question-wise.php"
        params = {
            'testid':testid,
            'testtakenid':testtakenid
        }
        Cookie ='MicrosoftApplicationsTelemetryDeviceId=890775c7-e13f-4fb0-9b38-deb8b65d3a5c; MicrosoftApplicationsTelemetryFirstLaunchTime=2024-06-06T08:02:21.310Z; PHPSESSID=16e6eb412639c690d902cd1c66aa1443; url_tcy=www.tcyonline.com%2Flogin; _gcl_au=1.1.1753120369.1717660937; browser_cookie_track=Chrome 125; user_agent_track=mozilla%2F5.0%20(windows%20nt%2010.0%3B%20win64%3B%20x64)%20applewebkit%2F537.36%20(khtml%2C%20like%20gecko)%20chrome%2F125.0.0.0%20safari%2F537.36; platform_track=Windows; networkType_track=; _fbp=fb.1.1717660939975.251871928702264880; _gid=GA1.2.1601205457.1717660940; MicrosoftApplicationsTelemetryDeviceId=890775c7-e13f-4fb0-9b38-deb8b65d3a5c; MicrosoftApplicationsTelemetryFirstLaunchTime=2024-06-06T08:02:21.310Z; tcy_userid=6496416; tcy_username=Khushdeep+Singh; 3f8f7c239a59a0a7f599f8f1f242690211f6ff7a=a2RzMTY2OTlAZ21haWwuY29t; TCYRatingPopupForOneDay1=1; _ga=GA1.1.79017069.1717660940; _ga_QN62S1X466=GS1.1.1717660939.1.1.1717661908.60.0.0; _ga_6WWD32Q07K=GS1.1.1717660939.1.1.1717661908.60.0.0'
        # curl_request = f"curl 'https://www.tcyonline.com/Analyse/question-wise.php?testid={testid}&testtakenid={testtakenid}' -H 'authority: www.tcyonline.com' -H 'sec-ch-ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"99\", \"Google Chrome\";v=\"99\"' -H 'sec-ch-ua-mobile: ?0' -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/
        response_html = requests.get(get_first_question, params=params, headers={"Cookie": Cookie,'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
        print(response_html)
        soup = BeautifulSoup(response_html.text, 'html.parser')
        # question = soup.find('div', class_='questionText')
        question = soup.find('div', class_='questionText').get_text(strip=True)
        question = "<p>"+question+"</p>"
        # Extract options
        options_divs = soup.find_all('div', class_='QBYQ_questionNormal')
        
        for option in options_divs:
                option = option.get_text(strip=True)
                option = "<p>" + option + "</p>"
                formatted_options.append(option)
        
        option = soup.find('div', class_='QBYQ_questioncorrect')
        if option.find('span', class_='answerMsg'):
            remove_span = option.find('span', class_='answerMsg')
            remove_span.decompose()
            option = option.get_text(strip=True)
            option = "<p>" + option + "</p>"
            formatted_options.append(option)
        formatted_options_shuffle = formatted_options.copy()
        random.shuffle(formatted_options_shuffle)
        formatted_options = formatted_options_shuffle
        answer = ''
        for i in range(4):
            if formatted_options[i] == option:
                answer = chr(ord('A') + i)
        solution = soup.find('pre', class_='ckquesSol').get_text(strip=True)
        solution = "<p>"+solution+"</p>"
        question_data = scrapeExcel(question_data)
        answer = scrapeExcel(answer)
        solution = scrapeExcel(solution)
        for option in formatted_options:
            option = scrapeExcel(option)
        formatted_questions['questions'].append({
            'question':question,
            'options':formatted_options,
            'answer':answer,
            'solution':solution
        })
    return formatted_questions

def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

def scrape_website(url,website):
    # Setup Selenium WebDriver
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
   
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    

    driver.implicitly_wait(10)
    html = driver.execute_script("return document.documentElement.outerHTML")

    # Get page source after JavaScript execution
    driver.quit()  # Close the browser
    html_text = convert_latex(str(html))
    # Use BeautifulSoup to parse the HTML content
    if 'www.savemyexams.com/' in url:
        html_text = replace_tables_with_images(html_text)
    soup = BeautifulSoup(html_text, 'html.parser')
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()
    for style in soup.find_all('style'):
        style.extract()
    for nav in soup.find_all('nav'):
        nav.extract()
    text_list = []
    

    if  website == "edurev":
        try:
            ads = soup.find_all('div', class_='cnt_ad_bnr')
            for ad in ads:
                ad.extract()
            ads = soup.find_all('h2', id='Last_Updated__')
            for ad in ads:
                ad.extract()
            ads = soup.find_all('span', class_='gbp-cntnr')
            for ad in ads:
                ad.extract()
            ads = soup.find_all('span', class_='gbp-btn-cntnr')
            for ad in ads:
                ad.extract()
            ads = soup.find_all('span', class_='gbp-btn-cntnr-dnldapp')
            for ad in ads:
                ad.extract()
            questions = soup.find_all('div', class_='ed_question')
            for ques in questions:
                ques.extract()
            # ads = soup.find_all('div', class_='ER_Model_dnwldapp')
            # for ad in ads:
            #     ad.extract()

            body_content = soup.find('div', class_='contenttextdiv')
            # print(body_content)
            html = str(body_content)
            # Use BeautifulSoup to parse the HTML content
            # print(html)
            soup = BeautifulSoup(html, 'html.parser')

            # Extract text from each tag while maintaining the order
            processed_texts = set()
            processed_uls = set()  # Track processed 'ul' elements

            first = True
            h2_tags = 0
            count_p = 0
            previous_content_length = 0
            for tag in soup.descendants:
                if tag.name in ['h2']:
                    h2_tags += 1
            # try:
            # if (h2_tags > 4):
            for tag in soup.descendants:
                if tag.name in ['p','img','strong', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6']:
                    # print(tag)
                    if tag.name == 'img':
                       
                        text = str(tag)
                        text_list.append(text)
                    else:
                        text = tag.get_text()
                        
                        if text and text not in processed_texts:
                            # Remove extra spaces using regex
                            text = re.sub(r'\s+', ' ', text)
                            processed_texts.add(text)
                            text = "<"+tag.name+">"+text+"</"+tag.name+">"
                            previous_content_length+=len(text)
                            # if(tag.name == 'h2'):
                            #     print(tag)
                            if (tag.name == 'h2' and previous_content_length > 700):
                                text = "\n ********** \n"+text
                                previous_content_length = 0 
                           
                            elif(tag.name == 'h3' and previous_content_length >1500):
                                text = "\n ********** \n" + text
                                previous_content_length =0 
                                first = False
                            elif(tag.name == 'p' and previous_content_length >2000):
                                text = text+"\n ********** \n"
                                previous_content_length =0 
                                first = False
                            text_list.append(text)
                            if (tag.name == 'h2'):
                                text_list.append("\n ")
                elif tag.name == 'ul':
                    # Process 'ul' elements and add their id to the processed_uls set
                    text = tag.get_text()
                    if text and text not in processed_texts:
                        text = re.sub(r'\s+', ' ', text)
                        processed_texts.add(text)
                        previous_content_length+=len(text)
                        processed_uls.add(id(tag))  # Track that this 'ul' has been processed
                        if(tag.name == 'ul' and previous_content_length >1500):
                                text = text+"\n ********** \n"
                                previous_content_length =0 
                                first = False
                        text_list.append(f"<ul>{text}</ul>")
                elif tag.name == 'li':
                    # Only process 'li' elements if their parent 'ul' hasn't been processed
                    if id(tag.find_parent('ul')) not in processed_uls:
                        text = tag.get_text()
                        if text and text not in processed_texts:
                            text = re.sub(r'\s+', ' ', text)
                            processed_texts.add(text)
                            previous_content_length+=len(text)
                            processed_uls.add(id(tag))  # Track that this 'ul' has been processed
                            
                            text_list.append(f"<li>{text}</li>")
                elif tag.name == 'span':
                    # Only process 'li' elements if their parent 'ul' hasn't been processed
                    if id(tag.find_parent('ul')) not in processed_uls:
                        text = tag.get_text()
                        if text and text not in processed_texts:
                            text = re.sub(r'\s+', ' ', text)
                            processed_texts.add(text)
                            previous_content_length+=len(text)
                            processed_uls.add(id(tag))  # Track that this 'ul' has been processed
                            
                            text_list.append(f"<span>{text}</span>")
                        
        except Exception as e:
            print(e)
    elif  website == "geeksforgeeks":
        try:
            sidebars = soup.find_all('div', class_='sidebar_wrapper')
            for sidebar in sidebars:
                sidebar.extract()
            sidebars = soup.find_all('div', class_='three_dot_dropdown')
            for sidebar in sidebars:
                sidebar.extract()
            sidebars = soup.find_all('div', class_='article-bottom-buttons')
            for sidebar in sidebars:
                sidebar.extract()
            sidebars = soup.find_all('div', class_='discussion_panel')
            for sidebar in sidebars:
                sidebar.extract()
            sidebars = soup.find_all('div', class_='article-buttons drop')
            for sidebar in sidebars:
                sidebar.extract()
            topbars = soup.find_all('div', class_='header-main__slider')
            for topbar in topbars:
                topbar.extract()
            topbars = soup.find_all('div', class_='discussion_panel')
            for topbar in topbars:
                topbar.extract()
            topbars = soup.find_all('div', class_='article--recommended')
            for topbar in topbars:
                topbar.extract()
            topbars = soup.find_all('div', class_='article-meta')
            for topbar in topbars:
                topbar.extract()
            topbars = soup.find_all('div', class_='article-pgnavi')
            for topbar in topbars:
                topbar.extract()
            ads = soup.find_all('span', class_='gbp-cntnr')
            for ad in ads:
                ad.extract()
            ads = soup.find_all('span', class_='gbp-btn-cntnr')
            for ad in ads:
                ad.extract()
            ads = soup.find_all('span', class_='gbp-btn-cntnr-dnldapp')
            for ad in ads:
                ad.extract()
            questions = soup.find_all('div', class_='ed_question')
            for ques in questions:
                ques.extract()
           
            body_content = soup.find('div', class_='leftBar')
            # print(body_content)
            html = str(body_content)

            # Use BeautifulSoup to parse the HTML content
            # print(html)
            soup = BeautifulSoup(html, 'html.parser')

            # Extract text from each tag while maintaining the order
            processed_texts = set()
            first = True
            h2_tags = 0
            count_p = 0
            previous_content_length = 0
            for tag in soup.descendants:
                if tag.name in ['h2']:
                    h2_tags += 1
            # try:
            # if (h2_tags > 4):
            for tag in soup.descendants:
                if tag.name in ['p','img','strong','span', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li','code']:
                    # print(tag)
                    if tag.name == 'img':
                        text = str(tag)
                        # print(tag)
                        text_list.append(text)
                    else:

                        text = tag.get_text()
                        
                        if text and text not in processed_texts:
                            # Remove extra spaces using regex
                            text = re.sub(r'\s+', ' ', text)
                            processed_texts.add(text)
                            text = "<"+tag.name+">"+text+"</"+tag.name+">"
                            previous_content_length+=len(text)
                            # if(tag.name == 'h2'):
                            #     print(tag)
                            if (tag.name == 'h2' and previous_content_length > 700):
                                text = "\n ********** \n"+text
                                previous_content_length = 0 
                                
                            elif(tag.name == 'h3' and previous_content_length >1500):
                                text = "\n ********** \n" + text
                                previous_content_length =0 
                                first = False
                            elif(tag.name == 'p' and previous_content_length >2000):
                                text = text+"\n ********** \n"
                                previous_content_length =0 
                                first = False
                            elif(tag.name == 'ul' and previous_content_length >1500):
                                text = text+"\n ********** \n"
                                previous_content_length =0 
                                first = False
                            text_list.append(text)
                            if (tag.name == 'h2'):
                                text_list.append("\n ")
        except Exception as e:
            print(e)
    elif 'https://www.studyrankers.com/' in url :
        text_list =[]
        div_elements = soup.find_all('div', class_='post-body')

        for div in div_elements:
            text_list.append(div.get_text())
        result = ""
        for text in text_list:
            result += text + '\n'
        # print(result)
        result = re.sub(r'\n+', '', result)
        result_in_parts = result.split('.')
        output = ""
        first = True
        previous_text_len = 0
        previous_text =''
        for text in result_in_parts:
            previous_text +=text
            previous_text_len += len(text)
            if (previous_text_len >= 1500):
                if (first):
                    first = False
                    output += previous_text
                    previous_text_len = 0
                    previous_text=''
                else:
                    output += "\n ********** \n"+previous_text
                    previous_text=''
                    previous_text_len = 0
            else:
                output += previous_text
                previous_text = ''

        return output
        
    else:    
        # return str(soup)
        divs_to_remove = [
            'super-coaching',
            'sticky-header',
            'tabs__container',
            'updates',
            'faqs',
            'faq',
            'web-signup-sticky-footer',
            'target-test-series',
            'target-test-series',
            'pass-pro-banner',
            'faqWrapper_last',
            'hashover-form-section',
            'comments',

            
        ]

        for div_id in divs_to_remove:
            div_elements = soup.find_all('div', id=div_id)
            for div in div_elements:
                div.extract()

        divs_to_remove_classes = [
            'tabs__container',
            'updates',
            'faq',
            'web-signup-sticky-footer',
            'target-test-series',
            'pass-pro-banner',
            'gb-container-6149bc38a',
            'tags-links',
            'widget-area',
            'right-sidebar',
            'wp-faq-schema-wrap',
            'Gb-container-52018004',
            'comments-area',
            'dpsp-share-text',
            'adda-faq-wrapp',
            'top-package',
            'sidebar_main',
            'olive-after-content',
            'AlsoRead',
            'List_ReadingList__K0aAk',
            'seoText',
            'SectionTitle',
            'Header_topNav__NnKZp',
            'GlobalNews_LatestNotifi__ascJG',
            'NativeAd',
            'pwa_l2menu',
            'ppBox',
            'sectional-faqs',
            'newTocWrapper',
            'exam_rhs_content',
            'defaultCard',
            'similarExams',
            'ask-qryDv',
            'addtoany_share_save_container',
            'header-menu',
            'prefooter-adda',
            'signup-description',
            'login-modal-div',
            'author-container',
            'tags-wrapp-bx',
            'dpsp-content-wrapper',
            'gb-grid-wrapper',
            'adp_blog',
            '_container abt-athr-wrap',
            'announcementWidget',
            'faqWrapper',
            'FeatureSliderCTA_container__8yplH',
            'AuthorCard_wrapper__K_xAj',
            'ContentFeedbackButtons_wrapper__O_leo',
            'ssrcss-1nq6mya-PromoComponentWrapper',
            'ssrcss-105wvvp-Wrapper e1x17m8s0',
            'ssrcss-1wnvszv-FooterStack e1k195vp4',
            'ssrcss-xifqb-SidebarWrapper e107fkov4',
            'ssrcss-16cbu9t-HideAndReveal esxewyl4',
            'penci-headline',
            'headerify-wrap',
            'banner-live-pop',
            'footer-slider',
            "universal-search",
            'flotingbar',
            'create-free-account',
            'share-lesson',
            'popular-tips iot-widget',
            'footer-content',
            'footerexamswrap'

        ]
        

        for div_class in divs_to_remove_classes:
            if 'https://edukemy.com/' in url:
                if div_class !='right-sidebar':
                    div_elements = soup.find_all('div', class_=div_class)
            else:
                div_elements = soup.find_all('div', class_=div_class)

            for div in div_elements:
                div.extract()
      
        section_element = soup.find_all('section', class_="related-articles")
        for section in section_element:
            section.extract()
        section_element = soup.find_all('figure', class_="ssrcss-quwkth-ComponentWrapper e15ii8li2")
        for section in section_element:
            section.extract()
        for div_class in divs_to_remove_classes:
            div_elements = soup.find_all('p', class_='dpsp-share-text ')
            for div in div_elements:
                div.extract()

        spans_to_remove = [
            'tags-links',
        ]


        for span_class in spans_to_remove:
            span_elements = soup.find_all('span', class_=span_class)
            for span in span_elements:
                span.extract()
        def convert_divs(original_divs):
            formatted_div = original_divs.replace(r"\(\begin{array}{l}", "").replace(r"\end{array} \)", "")
            formatted_div = formatted_div.replace("Cos", r"\cos").replace("Cosec", r"\csc")
            formatted_div = formatted_div.replace("tan", r"\tan").replace("cos", r"\cos").replace("sin", r"\sin")
            formatted_div = formatted_div.replace("cot", r"\cot")
            formatted_div = formatted_div.replace("cosec", "csc")
            formatted_div = formatted_div.replace(r"\\c", r"\c")
            formatted_div =  formatted_div 
            return formatted_div

        div_elements = soup.find_all('div', class_="mathjax-scroll")
        for div in div_elements:
            div_formatted = convert_divs(r""+div.text)
            # print(div_formatted)
            img_tags = latex_to_image(soup,div_formatted)
            # print( img_tags)
            div.replace_with(img_tags)

        ids_to_remove = [
            'right-sidebar',
        ]

        for id_value in ids_to_remove:
            id_element = soup.find('div', id=id_value)
            if id_element:
                id_element.extract()
        # 01/04/2024
        # header_tags = soup.find_all('header')
        # for tag in header_tags:
        #     tag.clear()
        tags_to_remove = ['footer','video','ins','iframe','nav','aside','link','meta', 'option','style','header',
                        'label', 'input', 'script', 'button']
        for tag in tags_to_remove:
            if 'https://www.savemyexams.com' in url :
                if tag != 'header':
                    for element in soup.find_all(tag):
                        element.decompose()  # Remove the tag and its content
            else:
                for element in soup.find_all(tag):
                    element.decompose()  # Remove the tag and its content
        
        empty_p_tags = soup.find_all('p', class_=True)
        for tag in empty_p_tags:
            if not tag.text.strip():
                tag.decompose()
        body_content = soup.find('body').prettify()

        # Write the body content to the output file
        html = body_content
        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(html, 'html.parser')
        # Extract text from each tag while maintaining the order
        text_list = []
        processed_texts = set()
        first = True
        h2_tags = 0
        count_p = 0
        previous_content_length = 0
        for tag in soup.descendants:
            if tag.name in ['h2']:
                h2_tags += 1
        # try:
        # if (h2_tags > 4):
        for tag in soup.descendants:
            if tag.name in ['p','img','strong', 'h1', 'h2', 'h3', 'span','tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li']:
                if tag.name == 'img':
                    image_url = tag['src']
                    
                    text = str(tag)
                    # text_list.append(text)
                    text_list.append(text)
                else:
                    text = tag.get_text()
                    
                    if text and text not in processed_texts:
                        # Remove extra spaces using regex
                        text = re.sub(r'\s+', ' ', text)
                        processed_texts.add(text)
                        text = "<"+tag.name+">"+text+"</"+tag.name+">"
                        previous_content_length+=len(text)
                        # if(tag.name == 'h2')
                        if (tag.name == 'h2' and previous_content_length > 700):
                            text = "\n ********** \n"+text
                            previous_content_length = 0 
                          
                        elif(tag.name == 'h3' and previous_content_length >1500):
                            text = "\n ********** \n" + text
                            previous_content_length =0 
                            first = False
                        elif(tag.name == 'p' and previous_content_length >1500):
                            text = text+"\n ********** \n"
                            previous_content_length =0 
                            first = False
                        elif(tag.name == 'ul' and previous_content_length >1500):
                            text = "\n ********** \n" + text
                            previous_content_length =0 
                            first = False
                        if 'Test your knowledge' not in text and 'Test questions' not in text:
                            text_list.append(text)
                        if (tag.name == 'h2'):
                            text_list.append("\n ")
                        
    # print()
    result = ""
    for text in text_list:
        result += text + '\n'
    # print(result)
    result = re.sub(r'\n+', '', result)
    result_in_parts = result.split("**********")
    output = ""
    first = True
    for text in result_in_parts:
        if (len(text) != 0):
            if (first):
                first = False
                output += text
            else:
                if (len(text) < 100):
                    output += text
                else:

                    output += "\n ********** \n"+text

    return output
    
    # except Exception as e:
    #     print(e)
def scrapeExcel(text):
    # Setup Selenium WebDriver
    # latex to image 
    html_text = excelRun(text)
  
    return html_text

    


@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')
    # url = "view-source:"+url
    print(url)

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        # edurev = False
        website = ""
        # geeksforgeeks = False
        if "edurev.in" in url:
            website = "edurev"
        if "geeksforgeeks.org" in url:
            # geeksforgeeks = True
            website = "geeksforgeeks"
        output_text = scrape_website(url,website)
        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error: "+str(e)}), 500


@app.route('/textToScrape', methods=['POST'])
def scrapeText():
    data = request.json
    text = data.get("url")
    if not text:
        return jsonify({'error': 'text is required'}), 400
    try:
        output_text = scrape_text(text)
        # output_text = scrapeExcel(text)

        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error: "+str(e)}), 500


@app.route('/create/scroller/test', methods=['POST'])
def createScrollerTest():
    data = request.json
    url = data.get("url")
    quizId = data.get("quizId")
    quizGuid = data.get("quizGuid")
    logging.info("INFO : TEST SCROLLER quizId: " + quizId)
    logging.info("INFO : TEST SCROLLER quizGuid: " + quizGuid)
    logging.info("INFO : TEST SCROLLER url: " + url)

    if not url:
        return jsonify({'error': 'text is required'}), 400
    # try:
    all_questions = getScrollerTest(url)
    api_to_send_questions = "https://p1.edurev.in/Tools/PDF_TO_QuizQuestions_Automation"
    res = {
        "quizId": quizId,
        "quizGuid": quizGuid,
        "api_token" : "45b22444-3023-42a0-9eb4-ac94c22b15c2",
        "result": all_questions
    }
    logging.info("INFO : TEST SCROLLER Sending Result to API : " + api_to_send_questions)
    logging.info(res)
        # output_text = scrapeExcel(text)
    send_question = requests.post(api_to_send_questions, json=res)
    if send_question.status_code == 200:
        print("Question sent successfully!")
        logging.info("***********************************Question sent successfully!***********************************")


    return jsonify(res), 200
# url = "https://www.mockers.in/test-solution1/test-575422"


@app.route('/excel/scrapper', methods=['POST'])
def excelScrapper():
    data = request.json
    text = data.get('url')
    # url = "view-source:"+url
    # print(url)

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    try:
        output_text = scrapeExcel(text)
        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error Happend at Excel Scrapper "}), 500


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    print(request.get_json())
    data = request.get_json()
    pdf_url = data.get('pdf_url')
    if not pdf_url:
        return jsonify({'error': 'No PDF URL provided'}), 400

    response = requests.get(pdf_url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to download PDF'}), 500

    pdf_data = response.content

    # Open the PDF from memory
    pdf_document = fitz.open(stream=pdf_data, filetype='pdf')
    first_page = pdf_document.load_page(0)

    # Convert first page to an image
    pix = first_page.get_pixmap()
    image = Image.open(io.BytesIO(pix.tobytes("png")))
    width, height = image.size

    # Calculate the cropping box to make the image square
    if width > height:
        left = (width - height) // 2
        top = 0
        right = left + height
        bottom = height
    else:
        top = (height - width) // 2
        left = 0
        bottom = top + width
        right = width

    # Crop the image to a square
    image = image.crop((left, top, right, bottom))

    # Resize the image to 70x70 pixels
    image = image.resize((300, 300), Image.LANCZOS)

    image_name = str(uuid.uuid4()) + ".png"
    image_path = locations_of_images + image_name
    image.save(image_path)
    image_url = Public_IP + image_name
    print(image_url)
    return jsonify({'image_url': image_url})

    # return jsonify({'image_url': image_url})




def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url
def get_ordinal(n):
    # Add the correct ordinal suffix to a day of the month
    if 11 <= n <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix


def scrape_website_civilDaily(url):
    # Setup Selenium WebDriver
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
   
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    

    driver.implicitly_wait(10)
    html = driver.execute_script("return document.documentElement.outerHTML")

   
    driver.quit()  # Close the browser
    # html_text = convert_latex(str(html))
    
    soup = BeautifulSoup(html, 'html.parser')
    header = soup.find('header', class_="entry-header")
    title = header.find('h1', class_="entry-title default-max-width").text
    subjects = header.find('div', class_="entry-meta").find_all('a')
    # print(subjects)
    subject = subjects[1].text
    div = soup.find('div', class_="entry-content")
    all_data = ""
    all_data +=title + "\n"+subject + "\n"
    for child in div.descendants:
        
        if child.string and child.string.strip() and child.string.strip() not in all_data and "Get an IAS/IPS ranker as your 1: 1 personal mentor for UPSC" not in child.string.strip() and "Attend Now" not in child.string.strip():
            all_data += child.string.strip() + "\n"
    all_data+="**********"+"\n"
    
    # print(all_data)
    return all_data.strip()


def scrape_website_iasbaba(url):
    # Setup Selenium WebDriver
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
   
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    

    driver.implicitly_wait(10)
    html = driver.execute_script("return document.documentElement.outerHTML")

    # Get page source after JavaScript execution
    # html = driver.page_source
    # print(html)
    driver.quit()  # Close the browser
    # html_text = convert_latex(str(html))
    soup = BeautifulSoup(html, 'html.parser')
    
    div_elements = soup.find_all('div', class_="su-box su-box-style-soft")
    all_data = ""
    
    for i, div in enumerate(div_elements):
        if i == len(div_elements) - 1:
            break
        for child in div.descendants:
            if child.name == "img":
                all_data += str(child) + "\n"
            if child.string and child.string.strip() and child.string.strip() not in all_data:
                all_data += child.string.strip() + "\n"
        all_data+="**********"+"\n"
    
    # print(all_data)
    return all_data.strip()

def get_data_vija(soup):
    div_element = soup.find('div', class_="box-body")
    all_data = ""
    for child in div_element.descendants:
        if child.string and child.string.strip() and child.string.strip() not in all_data:
            all_data += child.string.strip() + "\n"
    all_data+="**********"+"\n"
    
    # print(all_data)
    return all_data.strip()
def scrape_website_vaji(url):
    # Setup Selenium WebDriver
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
   
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    

    driver.implicitly_wait(10)
    
    # Get the initial height of the document
    # last_height = driver.execute_script("return document.body.scrollHeight")
    t =5
    while t > 0:
        t-=1
        # Scroll down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for new content to load
        time.sleep(1)

    # Get the HTML after all content is loaded
    html = driver.execute_script("return document.documentElement.outerHTML")
    # print(html)
    driver.quit()  # Close the browser

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    # print(soup)
    soups = soup.find_all('div', class_='feed_item_box load_more_item')
    result = ""
    for soup in soups:
        try:
            
            if "Article" in soup.find('div', class_='box-header').find("h3").text:
                date_element = soup.find('small')
                date_text = date_element.text.strip()
                # print(date_text)
                if "hour ago" not in str(date_text) and "hours ago" not in str(date_text) and "days ago" not in date_text and "day ago" not in date_text:
                    formats = ["%B %d, %Y", "%d %B %Y", "%d %B, %Y", "%d %b %Y"]

                    date_obj = None

                    for fmt in formats:
                        try:
                            date_obj = datetime.datetime.strptime(date_text, fmt)
                            break
                        except ValueError:
                            pass
                    

                today_date = datetime.datetime.now().strftime("%B %d, %Y")
                if date_obj:
                    # print("dateobj = "+date_obj.strftime("%B %d, %Y"))
                    if "hour ago"  in str(date_text) or "hours ago"  in str(date_text):
                        result+= get_data_vija(soup)
                        
                        # break
                    elif date_obj.strftime("%B %d, %Y") == today_date:
                    # elif date_obj.strftime("%B %d, %Y") == "June 01, 2024":
                        result+= get_data_vija(soup)

        except Exception as e:
            print("error: "+str(e))
            
    return result
       
def scrape_website_current_affair(url):
    # Setup Selenium WebDriver
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
   
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    

    driver.implicitly_wait(10)
    html = driver.execute_script("return document.documentElement.outerHTML")

    # Get page source after JavaScript execution
    # html = driver.page_source
    # print(html)
    driver.quit()  # Close the browser
    # html_text = convert_latex(str(html))
    soup = BeautifulSoup(html, 'html.parser')
    if url == "https://iasbaba.com/current-affairs-for-ias-upsc-exams/":
        today_date = datetime.datetime.now()  # Format like '22 May 2024'
        formatted_date = f"{get_ordinal(today_date.day)} {today_date.strftime('%B %Y')}"  # Format like '22nd May 2024'
        # Find the link for today's date
        ul_elements = soup.find_all('ul', class_='lcp_catlist')
        result = ""
        print(ul_elements)
        for ul_element in ul_elements:
            li_elements = ul_element.find_all('li')
            for li in li_elements:
                a_element = li.find('a')
                print(formatted_date, a_element.text)
                if a_element and formatted_date in a_element.text:
                    result += scrape_website_iasbaba(a_element['href'])
        return result
                    
    elif url == "https://www.civilsdaily.com/":
        div_elements = soup.find_all('div', class_="news-block")
        
        result = ""
        for div in div_elements:
            date_div = div.find('h1', class_="date-strip").text
            date_div = date_div[1:]
            # print(date_div)
            today_date = datetime.datetime.now()  # Format like '22 May 2024'
            formatted_date = f"{get_ordinal(today_date.day)} {today_date.strftime('%B')}"
            if date_div == formatted_date:
                articles = div.find_all('article')
                for article in articles:
                    link = article.find('h2', class_ = "entry-title default-max-width").find("a")['href']
                    result += scrape_website_civilDaily(link)
        return result
    return ""       
def getGPTResponse(prompt):
    try:
        # Your user prompt as a dictionary
        user_prompt_document = {
            "Role": '''You are a proficient educational content creator specializing in summarizing and synthesizing complex information from PDF books into concise, comprehensible notes and test materials. Your expertise lies in extracting key theoretical concepts, providing clear definitions, and offering illustrative examples. When presenting information in a list, use only 'li' tags without 'p' tags inside them. Ensure the notes are well-organized and visually appealing, employing HTML tags for structure without using paragraph tags inside list items. Your goal is to optimize the learning experience for your audience by Explaining in Detail from the lengthy content into digestible formats while maintaining educational rigor. You are a content formatter specializing in converting text into HTML elements. Your expertise lies in structuring text into well-formatted HTML tags, including <li>, <ul>, and <p>, without using special characters like * or #. Your goal is to ensure that the HTML output is organized, visually appealing . i need the output in this format :
            "
            [Subject name in p tag] // you observe the given input and pick from this list ["GS1/Geography" , "GS1/Indian Society",  "GS1/History & Culture",  "GS2/Polity", "GS2/Governance", "GS2/International Relations", "GS3/Economy", "GS3/Environment", "GS3/Science and Technology", "GS3/Defence & Security", "GS4/Ethics"] the subject name and give in p tag
            [Title/Heading Name] //just the heading of the content give in h1 tag
            Why in news?
            [Content] // contain all the information about the current affairs give in p tag
            "
            also you give all the data in HTML code only with proper formatting

            ''',
            "objective": prompt +"\nParaphrase the information given, elaborate and explain with examples wherever required. Give all points in bullet format with proper heading across (add li tag to html of bullet points). Make sure you do not miss any topic . Make sure not more than 2 headings have a HTML tag H7 and not more than 4 Subheadings have an HTML tag H8 otherwise make the headings bold. Make sure everything is paraphrased and in detail and keep the language easy to understand. Give response as a teacher but do not mention it. Please Do not promote any website other than EduRev and do not give references. Your response should be in HTML only and do not change the images HTML in given in HTML above. Again, always remember to never skip any image in the HTML of your response. Also, table should always be returned as table. Please keep same the headings given under <H2> tag and <H3> tag and don't paraphrase them."
        }
        

        user_prompt_test = {
            "Role": '''You are an expert in creating JSON formatted test materials based on current affairs that is provided to you in input html code. Your task is to understand the input deeply and create test questions that follow the specified format. When presenting information in a list, use only 'li' tags without 'p' tags inside them. The test should include multiple-choice questions (MCQs) and should follow this specific JSON format:
                {
                    questions': [
                        {
                        'question': '[Question Text]',
                        'options': [
                            '[Option A]',
                            '[Option B]',
                            '[Option C]',
                            '[Option D]'
                            ],
                        'answer': '[Correct Answer]',
                        'solution': '[Solution]'
                        },
                    
                        ...
                    ]
                }
                Your goal is to ensure the JSON output is organized, educationally rigorous, and reflects a deep understanding of the content provided in the HTML. just give the json in output so not add anything else''',
            # "Role": "You are a proficient educational content creator specializing in summarizing and synthesizing complex information from PDF books into concise, comprehensible notes and test materials. Your expertise lies in extracting key theoretical concepts, providing clear definitions, and offering illustrative examples. When presenting information in a list, use only 'li' tags without 'p' tags inside them. Ensure the notes are well-organized and visually appealing, employing HTML tags for structure without using paragraph tags inside list items. Your goal is to optimize the learning experience for your audience by Explaining in Detail from the lengthy content into digestible formats while maintaining educational rigor. You are a content formatter specializing in converting text into HTML elements. Your expertise lies in structuring text into well-formatted HTML tags, including <li>, <ul>, and <p>, without using special characters like * or #. Your goal is to ensure that the HTML output is organized, visually appealing",
            "objective": prompt +'''
                Make questions in this statement type only and extract same level :
                    question : "
                    Consider the following statements with reference to the Eurasian Whimbrel:

                    1. It is a wading bird endemic to the western margins of Europe.

                    2. It is classified as ‘Endangered’ under the IUCN Red List.

                    Which of the statements given above is/are correct?
                    "
                    options: "
                    A.	
                    1 only

                    B.	
                    2 only

                    C.	
                    Both 1 and 2

                    D.	
                    Neither 1 nor 2
                    "

                    Solution :

                    "For the first time, a long-distance migratory bird, the Eurasian or common whimbrel, tagged with a Global Positioning System (GPS) transmitter, was captured on camera in the state of Chhattisgarh.

                    About Eurasian Whimbrel:

                    It is a wading bird in the large family Scolopacidae.
                    Scientific Name: Numenius phaeopus
                    Distribution:
                    They have an extensive range that spans across five continents: North America, South America, Asia, Africa, and Europe.
                    They breed in the subarctic regions of Siberia and Alaska during the summer months before migrating south to wintering grounds in southern USA, Central America, South America, Africa, and South Asia, including Nepal.
                    Habitat: Winters mainly along the coastline, coastal wetlands, mangroves, marshes, and larger rivers.
                    Features:
                    A fairly large greyish-brown bird with a long, decurved bill with a kink.
                    It has a distinct head pattern with dark eye-stripes and crown-sides.
                    It is mottled dark brown above, pale below, with much brown streaking on the throat and breast. 
                    Generally solitary when nesting, the Whimbrel tends to become gregarious outside of the breeding season. 
                    Whimbrels are known for their high-pitched call consisting of a repetitive series of seven notes.
                    Conservation Status: 
                    IUCN Red List: Least Concern
                    Hence both statements are not correct."
'''
        }
        # print(user_prompt)
        current_date = datetime.datetime.now()
        # Format the date as a string in a specific format
        formatted_date = current_date.strftime("%Y-%m-%d")
        # Adjusted code for the new API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are ChatGPT, a large language model trained by OpenAI, based on the GPT-3.5 architecture. Knowledge cutoff: 2021-09 Current date: "+formatted_date
                },
                {
                    "role": "user",
                    "content": json.dumps(user_prompt_document)
                }
            ],
            max_tokens=4096,
            temperature=0.7
        )
        response_test = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are ChatGPT, a large language model trained by OpenAI, based on the GPT-3.5 architecture. Knowledge cutoff: 2021-09 Current date: "+formatted_date
                },
                {
                    "role": "user",
                    "content": json.dumps(user_prompt_test)
                }
            ],
            max_tokens=4096,
            temperature=0.7
        )

        # Print the response
        if response.choices:
            # Access the content from the response
            data_res = response.choices[0].message.content
            if "```html" in data_res:
                data_res = data_res.split("```html")[1]
                data_res = data_res.split("```")[0]
            if "<body>" in data_res:
                data_res = data_res.split("<body>")[1]
                data_res = data_res.split("</body>")[0]
            data_res = data_res.replace('<ul>\n', '<ul>')
            data_res = data_res.replace('</li>\n', '</li>')
            data_res = data_res.replace("/n<br>", "</br>")
            data_res = data_res.replace("<br>\n", "<br>")
            data_res = data_res.replace("<h1>", "<h7>")
            data_res = data_res.replace("</h1>", "</h7>")
            data_res = data_res.replace("</h2>\n", "</h2>")
            data_res = data_res.replace("</h7>\n", "</h7>")
            data_res = data_res.replace("</h3>\n", "</h3>")
            data_res = data_res.replace("</h8>\n", "</h8>")
            data_res = data_res.replace("</p>\n", "</p>")
            data_res = data_res.replace("</h2><br>", "</h2>")
            data_res = data_res.replace("</h7><br>", "</h7>")
            data_res = data_res.replace("</h3><br>", "</h3>")
            data_res = data_res.replace("<html>", "")
            data_res = data_res.replace("</html>", "")
            data_res = data_res.replace("</h8><br>", "</h8>")
            data_res = data_res.replace("</p><br>", "</p>")
            data_res = data_res.replace("</ul>\n", "</ul>")
            data_res = data_res.replace("</ul><br>", "</ul>")
            data_res = data_res.replace("</ol>\n", "</ol>")
            data_res = data_res.replace("</ol><br>", "</ol>")
                # print(data_res)


        if response_test.choices:
            # Access the content from the response
            data_res_test = response_test.choices[0].message.content
            # print(content)
            logging.info("INFO : Response test: " + data_res_test)
            if "```json" in data_res_test:
                data_res_test = data_res_test.split("```json")[1]
                data_res_test = data_res_test.split("```")[0]
                # data_res_test = json.loads(data_res_test)
                try:
                    data_res_test = json.loads(data_res_test)
                    
                            
                except json.JSONDecodeError as e:
                    logging.info(f"ERROR : JSON decoding error: {e}")
        else:
            logging.info("ERROR : No test response generated.")
        
        
        data_res = str(data_res) 
        if '<body>' in data_res:
            data_res = data_res.split('<body>')[1].split('</body>')[0]
        # return data_res 
        return data_res , data_res_test
    except Exception as e:  
        print(e)
        return jsonify({'error': 'An error occurred'}), 500
    
# @app.route('/getCurrentAffairs', methods=['GET'])
def scrape_websites_current_affair():
    websites = [
        "https://iasbaba.com/current-affairs-for-ias-upsc-exams/",
        "https://vajiramias.com/",
        "https://www.civilsdaily.com/"
    ]
    result = ""
    for url in websites:
        if url == "https://vajiramias.com/":
            date = scrape_website_vaji(url)
            if len(date) > 0:
                result += date
        else:
            date = scrape_website_current_affair(url)
            if len(date) > 0:
                if url == "https://iasbaba.com/current-affairs-for-ias-upsc-exams/":
                    result += date
                else:
                    result += date
    results = result.split("**********")
    today_date = datetime.datetime.now()
    file_path = '/home/er-ubuntu-1/webScrapping/currentAffairs/current_affairs_'+today_date.strftime("%Y-%m-%d")+'.txt'
    with open (file_path, 'w') as f:
        f.write(result)
    
    indices_to_delete = set()
    for i in range(0, len(results)):
        for j in range(i + 1, len(results)):
            paragraph1 = results[i]
            paragraph2 = results[j]
            if paragraph1 == "" or paragraph2 == "":
                continue

            embedding1 = model.encode(paragraph1, convert_to_tensor=True)
            embedding2 = model.encode(paragraph2, convert_to_tensor=True)

            # Calculate cosine similarity
            cosine_sim = util.pytorch_cos_sim(embedding1, embedding2).item()

            # Get the similarity percentage
            similarity_percentage = cosine_sim * 100

            if similarity_percentage > 80:
                indices_to_delete.add(j)

    for index in sorted(indices_to_delete, reverse=True):
        del results[index]

    # Set up logging
    
    

    random_paragraphs = random.sample(results, min(len(results), 12))
    res = ""
    test = {
        'questions':[]
    }
    for paragraph in random_paragraphs:
        if len(paragraph) > 10:
            prompt = "\n Paraphrase the information given, elaborate and explain with examples wherever required. Give all points in bullet format with proper heading across (add li tag to html of bullet points). Make sure you do not miss any topic . Make sure not more than 2 headings have a HTML tag H7 and not more than 4 Subheadings have an HTML tag H8 otherwise make the headings bold. Make sure everything is paraphrased and in detail and keep the language easy to understand. Give response as a teacher but do not mention it. Please Do not promote any website other than EduRev and do not give references. Your response should be in HTML only and do not change the images HTML in given in HTML above. Again, always remember to never skip any image in the HTML of your response. Also, table should always be returned as table. Please keep same the headings given under <H2> tag and <H3> tag and don't paraphrase them. Add Heading Exactly the same as input and also Dont miss any content.\n"
            paragraph += prompt
            logging.info("INFO : UserPrompt: " + paragraph)
            data , data_test = getGPTResponse(paragraph)
            # data  = getGPTResponse(paragraph)
            try:
                print("Type of data_test:", type(data_test))
                if type(data_test) == str:
                    data_test = json.loads(data_test)
                    print('converted to json')                    
                    

                print("Content of data_test:", data_test)
                if isinstance(data_test, dict) and 'questions' in data_test:
                    for question in data_test['questions']:
                        # print(question)
                        test['questions'].append(question)
                else:
                    print("data_test is not a dictionary or does not contain 'questions' key.")
            except Exception as e:
                print("Error:", str(e))
            
            res += data
            res += "\n" + "<hr>" + "\n"
            logging.info("INFO : Response: " + data)
            for question in test['questions']:
                
                option_number=0
                opt = ['A','B','C','D']
                for option in question['options']:
                    if "A." in option or "B." in option or "C." in option or "D." in option:
                        option.replace("A.","")
                        option.replace("B.","")
                        option.replace("C.","")
                        option.replace("D.","")
                    if question['answer'] in option:
                        question['answer'] = opt[option_number]
                        
                        break
                    option_number+=1
    # Log the result
    api_to_send_current_affairs = "https://p1.edurev.in/Tools/CreateCurrentAffairsDocument"
    result = {'result': res, 'test': test}
    send_current_affairs = requests.post(api_to_send_current_affairs, json=result)
    if send_current_affairs.status_code == 200:
        print("Current Affairs sent successfully!")
    # return jsonify(), 200

def sanitize_filename(filename):
    # Remove invalid characters
    return re.sub(r'[<>:"/\\|?*\n]', '', filename)

def download_images(query):
    # IMAGES FROM GOOGLE
    sanitized_query = sanitize_filename(query)
    image_links = []
    google_crawler = GoogleImageCrawler(storage={'root_dir': '/home/er-ubuntu-1/webScrapping/googleImagesDownload/'})
    google_crawler.crawl(keyword=sanitized_query, max_num=4)
    for filename in os.listdir('/home/er-ubuntu-1/webScrapping/googleImagesDownload/'):
        # if filename.endswith('.jpg'):
        image_name = str(uuid.uuid4()) + ".jpg"
        os.rename(f'/home/er-ubuntu-1/webScrapping/googleImagesDownload/{filename}', f'/var/www/html/images/{image_name}')
        image_path = f"{Public_IP}{image_name}"
        image_links.append(image_path)
    # # IMAGES FROM FREEPIK
    # url_to_register = "https://www.freepik.com/pikaso/api/text-to-image/create-request?lang=en&cacheBuster=2"

    # Cookie = ("XSRF-TOKEN=eyJpdiI6IndJZ0JsMm5FRlJuTFNEcmIrUUFIUmc9PSIsInZhbHVlIjoiL1BvYzBsOURuYkpWWnVpNWpmbzRrb3N5bFpieVRySi9zMFg0eXd0SVlFMFk3YXlQclhPUWJpREZXc0JDZTU3MGlZMVU5Wm1XL1hLSjRtMkZOdEpQWjM5OXg4Q0psTW5heTlOTG1tZ3Z5enJCa29CWCtsNjRZNHVNZTI5eXM0MXUiLCJtYWMiOiIzZjJjODY2OGMyZWFjNzhjMzlkODRkOTcyZGE4YzgyMTcwMTdkMGZiNWE3NjI1OWFjN2UzZmZiM2RiNmY5YzA5IiwidGFnIjoiIn0%3D; pikaso_session=eyJpdiI6ImEyL3NIYmtOZGJsNHVkbTlDU3A2Umc9PSIsInZhbHVlIjoibWEwdUJEaVRrRDE0eEZsQmc0cmUrWXFXeXQzRFJDRy9XTHFmbFQ1a1hqZkxwMjJXc2FzMUdBWnRkNFdKNlBIMks2eFNzYi9TMGhLaVVWR1d3aFd1V0c1TGphY3I1eGNzeXkycnlvVE9EWGFtenUxdEEyQnBKaG5GOHIxb0VYd3MiLCJtYWMiOiIxOTk0MThmZjgyZGYyMTQzMTMxMzlkMjgxMzFkMjI0ODcxYzk4NDFmYzcwOTM0YTQyZTVlZDZkZDQzYWY2MjkwIiwidGFnIjoiIn0%3D; _gcl_au=1.1.730307295.1718188112; ads-tag=b; _ga=GA1.1.687132118.1718188113; _cs_ex=1709818470; _cs_c=0; OptanonAlertBoxClosed=2024-06-12T10:28:33.670Z; GR_TOKEN=eyJhbGciOiJSUzI1NiIsImtpZCI6ImRmOGIxNTFiY2Q5MGQ1YjMwMjBlNTNhMzYyZTRiMzA3NTYzMzdhNjEiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSGFyZGlrIEppbmRhbCIsInBpY3R1cmUiOiJodHRwczovL2F2YXRhci5jZG5way5uZXQvNDk2MTY0MjItMjExMTI4MDgwMTAwLmpwZyIsImFjY291bnRzX3VzZXJfaWQiOjQ5NjE2NDIyLCJzY29wZXMiOiJmcmVlcGlrL2ltYWdlcyBmcmVlcGlrL3ZpZGVvcyBmbGF0aWNvbi9wbmcgZnJlZXBpay9pbWFnZXMvcHJlbWl1bSBmcmVlcGlrL3ZpZGVvcy9wcmVtaXVtIGZsYXRpY29uL3N2ZyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9mYy1wcm9maWxlLXByby1yZXYxIiwiYXVkIjoiZmMtcHJvZmlsZS1wcm8tcmV2MSIsImF1dGhfdGltZSI6MTcxODE4OTQzMCwidXNlcl9pZCI6Ijg1ZGI4Nzk1YWUyODRjZGI4MDM0MTJkZDdhN2ExODE1Iiwic3ViIjoiODVkYjg3OTVhZTI4NGNkYjgwMzQxMmRkN2E3YTE4MTUiLCJpYXQiOjE3MTgxODk0MzAsImV4cCI6MTcxODE5MzAzMCwiZW1haWwiOiJoYXJkaWtqaW5kYWxAZWR1cmV2LmluIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDc0Nzg1ODM5MjIxMTU5MzI2NDMiXSwiZW1haWwiOlsiaGFyZGlramluZGFsQGVkdXJldi5pbiJdfSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.WMCn_lXRzUYfrvZVasIvQxh8c75f9qu73qPcIYGcoEteVa0mOljTlmaJNIIqb8xUjv9lZmj-Lmhx03aaP5i3ejZgKPSEM-JySj8bWbgSboVJXzRLOr5FX-mhRaWxWujkVqnbLaukLjzOQ7fjzK2v6g2uxiaXvnsrEpaCGwRiZXqTj5gHxyAlmAlWyW73VZxOxOVljqVVEEsMMgl8IG6GaDLY02MktWbm81KzfDex2pWqG7cXBSPgQTRRdh6LnAob7qFPHdsi81LeDQ198FSjPs6qX3yVjO8FAsP2kV-pfES0CjOrcFthlRyaTi3PInaWb_CfDAS83g2wizzYgZdN1Q; GR_REFRESH=AMf-vBzyLZC1yAVp5vgCvG-W6Te7RdJdUukraJmXfhdud2VHg-kWqs-focaEeFKZJi-l1BCaMWCo2pDBu_iQAEnlXwv1gCZDtr6Xd86Y3OqBUf_CxXhLNy3kmaQzII8zIf-4ON1FreB-PQI4D93BkPKZxFJEvwUKzdAjAdLS5htmkqaeCxQAMFQBDaWEzlRaHCCzkLYAxZGt; _fc=FC.700669b7-addc-6731-f954-0499f36f49ee; _fcid=FC.700669b7-addc-6731-f954-0499f36f49ee; FP_MBL=1; GRID=49616422; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Jun+12+2024+16%3A21%3A57+GMT%2B0530+(India+Standard+Time)&version=202401.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CC0005%3A1&geolocation=IN%3BCH&AwaitingReconsent=false; ABTastySession=mrasn=&lp=https%253A%252F%252Fwww.freepik.com%252Fapi; ABTasty=uid=ww04er0x8zq86v80&fst=1718188112547&pst=-1&cst=1718188112547&ns=1&pvt=8&pvis=8&th=; csrf_freepik=b90d65d74b8ee8fb02b5ea92ed0d277c; _hjSessionUser_1331604=eyJpZCI6IjA4MWYyMGFkLTQ2MmQtNWUxZC04M2QwLTc4MzVlYTVkMTA5ZiIsImNyZWF0ZWQiOjE3MTgxODk1MTg1MzYsImV4aXN0aW5nIjpmYWxzZX0=; _hjSession_1331604=eyJpZCI6IjA4Yjk0YzMyLTRjYzMtNGY2ZC04NmRlLWQwM2E4OWViNTM2ZCIsImMiOjE3MTgxODk1MTg1MzgsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=; _hjHasCachedUserAttributes=true; __gads=ID=db56d1d0d311f2d1:T=1718189520:RT=1718189520:S=ALNI_MZDSV6XCBAfOLakpP2qMUdeIiNW0A; __gpi=UID=00000e48ac1ca705:T=1718189520:RT=1718189520:S=ALNI_MY7BoTr9OIVSJvYZANl7RQ2_PL-mQ; __eoi=ID=6fda754bad090ba2:T=1718189520:RT=1718189520:S=AA-AfjblwLbuydwQRMLRirVsVBXN; _cc_id=445b0078bf58440aa386dd6e44b74197; panoramaId_expiry=1718275921667; _au_1d=AU1D-0100-001718189523-JFUE3VRD-FISJ; cto_bundle=E3rCol91VUg1SHM3WFpYeGIxSm05Qnk1Vm1qZ3B4MDNWVHZUaUtvZHJ2Z2VRJTJGYXR2OEZBRHlZOHV3Tmk0RFA5bjVGbm9KSENCTlJDU0VjdE9kSmRkSiUyRkxqSWU0TkNSUjJBTlBCaEJmMXEyRlR2N2R3ZGJOZkJ3VEdhYXR0RnIlMkIlMkZ3MjBrcyUyRkt0WXp1RXZxeWZ6YTFWRDk1STFnanRIVUxRaHdkNGdFenMyYktKWlFBMFM2S3IzdXpTUGtTdzVKYzJtQVQ0c1JCMTkwaFpxU3FJS1o4QlZuUmJ0JTJGYXJvMHVnR2twY1FqaktvJTJCQnclMkZsNCUzRA; ab.storage.userId.35bcbbc0-d0b5-4e6c-9926-dfe1d0cd06ab=g%3A49616422%7Ce%3Aundefined%7Cc%3A1718189526058%7Cl%3A1718189526062; ab.storage.deviceId.35bcbbc0-d0b5-4e6c-9926-dfe1d0cd06ab=g%3A3a8f2c84-9038-32c2-7ad0-29a065430b1f%7Ce%3Aundefined%7Cc%3A1718189526063%7Cl%3A1718189526063; ab.storage.sessionId.35bcbbc0-d0b5-4e6c-9926-dfe1d0cd06ab=g%3Ab24e5449-4676-d581-b316-1c8ecbb7e67d%7Ce%3A1718225595036%7Cc%3A1718189526061%7Cl%3A1718189595036; _ga_18B6QPTJPC=GS1.1.1718189526.1.1.1718189595.58.0.0; ph_phc_Rc6y1yvZwwwR09Pl9NtKBo5gzpxr1Ei4Bdbg3kC1Ihz_posthog=%7B%22distinct_id%22%3A%22583477%22%2C%22%24sesid%22%3A%5B1718189604802%2C%2201900c13-894c-7a18-acf9-a28463a1e0c1%22%2C1718189525324%5D%2C%22%24epp%22%3Atrue%7D; _ga_QWX66025LC=GS1.1.1718188112.1.1.1718189604.49.0.0")
    # data = {
    #     "prompt": query,
    #     "layout_reference_image": None,
    #     "width": 1216,
    #     "height": 832
    # }
    # headers = {
    #     "Sec-Ch-Ua-Platform": "\"Windows\"",
    #     "Sec-Fetch-Dest": "empty",
    #     "Sec-Fetch-Mode": "cors",
    #     "Sec-Fetch-Site": "same-origin",
    #     "Cookie":Cookie,
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    #     "X-Xsrf-Token": "eyJpdiI6IjIzbGNOSVZpZElzUWp2UW5iTlBEOWc9PSIsInZhbHVlIjoiY3FZb1JvU0xDK2VmL1RYVmhYeWluTVdNRGpFY25GMk5zeEhURzF2Z0paNnZrdC8yMkwyU1lEL2RDMDZEYklEUWVDUGQwNkRYZjVZUnlKb0IwVjZhNGlsWS9DZHFxb291OE1Fbk5odWZyUmtNVUtHSnFKUmxXM1BSWVM1T3hCQzUiLCJtYWMiOiIyZjgzNzFmZjUxYmM2YjFjNzgyMjdhNjdkYTE2MDRiYzE1NWU4MTkwZTE1MmQzOGJkYzQ1MGE2MzhlZmFlN2JkIiwidGFnIjoiIn0="
    # }
    # response = requests.post(url_to_register, headers=headers, json = data)
    # # print(response)
    # id_ = 0
    # if response.status_code == 200:
    #     response_data = response.json()
    #     if "id" in response_data:
    #         id_ = response_data["id"]


    # url_to_fetch_images = "https://www.freepik.com/pikaso/api/render"
    # for i in range(1, 5):
    #     data = {
    #         "prompt": query,
    #         "permuted_prompt": query,
    #         "height": 832,
    #         "width": 1216,
    #         "num_inference_steps": 8,
    #         "guidance_scale": 1.5,
    #         "seed": 92845,
    #         "negative_prompt": "",
    #         "seed_image": "",
    #         "sequence": i,
    #         "image_request_id": id_,
    #         "should_save": True,
    #         "selected_styles": {},
    #         "aspect_ratio": "3:2",
    #         "tool": "text-to-image",
    #         "experiment": "8steps-lightning-cfg1-5",
    #         "mode": "realtime",
    #         "style_reference_image_strength": 1,
    #         "layout_reference_image_strength": 1,
    #         "user_id": 583477
    #     }
    #     response = requests.post(url_to_fetch_images, headers=headers, json=data)
    #     if response.status_code == 200:
    #         response_data = response.json()
    #         if "results" in response_data and "output_image" in response_data["results"]:
    #             base64_image = response_data["results"]["output_image"][0]
    #             # print("Base64 Image Data:", base64_image)
    #             image_data = base64.b64decode(base64_image)
    #             image_name = str(uuid.uuid4()) + ".jpg"
    #             with open(f'/var/www/html/images/{image_name}', 'wb') as f:
    #                 f.write(image_data)
    #             image_path = f"{Public_IP}{image_name}"
    #             image_links.append(image_path)
    #         else:
    #             print("Image data not found in the response.")
    #     else:
    #         print("Failed to fetch data. Status code:", response.status_code)
    # # UNSPLASH PICTURES
    # url = "https://unsplash.com/ngetty/v3/search/images/creative"

    # params = {
    #     "exclude_editorial_use_only": "true",
    #     "exclude_nudity": "true",
    #     "fields": "display_set,referral_destinations,title",
    #     "graphical_styles": "photography",
    #     "page_size": 28,
    #     "phrase": query,
    #     "sort_order": "best_match"
    # }

    # headers = {
    #     "Origin": "https://unsplash.com",
    #     "Referer": "https://unsplash.com/",
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    # }

    # response = requests.get(url, headers=headers, params=params)
    # if response.status_code == 200:
    #     response_data = response.json()
    #     i =0
    #     for image in response_data.get('images', []):
    #         if i == 4:
    #             break
    #         for size in image.get('display_sizes', []):
    #             if size['name'] == 'high_res_comp':
    #                 image_links.append(size['uri'])
    #                 break
            
    #         i += 1

    return image_links

@app.route('/download_images', methods=['POST'])
def download_images_endpoint():
    data = request.json
    query = data.get('query')
    image_links = []

    if query:
        image_links = download_images(query)

    return jsonify({'image_links': image_links}), 200

import schedule
import time
import subprocess


@app.route('/')
def hello_world():
    return 'Hello World'


if __name__ == '__main__':
    schedule.every().day.at("11:30").do(scrape_websites_current_affair)
    app.run(host="0.0.0.0", port=81)
