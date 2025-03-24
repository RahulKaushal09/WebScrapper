import base64
from calendar import c
import csv
from lib2to3.pytree import convert
from math import log
from unittest import result
from click import prompt
from exceptiongroup import catch
from flask import Flask, request, jsonify
from httpx import get
import pandas as pd
# from pydantic import SubclassError
import regex
import requests
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from sklearn import base
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, Comment
import re
import matplotlib.pyplot as plt
from handleLatex import convert_latex
from handleLatex import latex_to_image
from LatexToImage import mathTexToImgFun, replace_tables_with_images
from LatexToImage import excelRun, get_image
from urllib.parse import urljoin, urlparse
import html
from openai import OpenAI
from base64 import b64encode, b64decode


# try:
#     from HTMLParser import HTMLParser
# except ImportError:
#     from html.parser import HTMLParser

from removeWaterMark import HtmlToRemoveWaterMark, download_image, remove_background_and_convert_to_bw, RemoveWaterMarkWithAi
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
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_API_KEY"),
)

# chat_completion = client.chat.completions.create(
# openai.api_key = os.getenv("OPENAI_API_KEY")

# Rest of the code...
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from sentence_transformers import SentenceTransformer, util
import logging
import os
from dotenv import load_dotenv
os.remove(f'/root/webScrapping/Scrapper.log')
logging.basicConfig(filename='Scrapper.log', level=logging.INFO)

model = SentenceTransformer('all-MiniLM-L6-v2')

locations_of_images = "/var/www/html/images/"
Public_IP = "https://fc.edurev.in/images/"


from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# # Example usage
# process_image('D:\EduRev\embedding\watermark.png')

def decrypt_data(decr_data):
    # Remove the first 32 characters``
   
    decr_data = decr_data[32:]
    # Remove the last 32 characters
    decr_data = decr_data[:-32]
    # Decode base64
    decr_data = base64.b64decode(decr_data)
    # print(decr_data)
    # Unescape the URL encoded string
    try:
        decr_data = urllib.parse.unquote(decr_data.decode('utf-8'))
    except Exception as e:
        print(str(e))
    return decr_data
def convertRelativeURLToAbsoluteURL(inputHtml, baseURL):
    # print(inputHtml)
    soup = BeautifulSoup(inputHtml, 'html.parser')
    for img in soup.find_all('img'):
        img['src'] = baseURL + img['src']
    return str(soup)

def simplify_latex_limits(latex_code):
    # Replace the verbose limit syntax with the conventional syntax
    simplified_code = latex_code.replace(r"\mathop {\lim }\limits", r"\lim")
    # Additional cleanup if necessary, for example removing extra spaces or handling other cases
    return simplified_code
def clean_text_for_question(text):
    # Remove leading/trailing whitespace and replace multiple spaces with a single space
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text
@app.route('/scrapeTextToQues', methods=['POST'])
def scrapeQuesFromText():
    data = request.json
    text = data['text']
    quizId = data['quizId']
    quizGuid = data['quizGuid']
    marks = data['marks']
    negMarks = data['negMarks']
    logging.info("Scraping Questions from Text")
    logging.info("quizId : "+quizId + " quizGuid : "+quizGuid + " marks : "+marks + " negMarks : "+negMarks)
    soup = BeautifulSoup(text, 'html.parser')

    # Find all exam-panel class of div
    all_exam_panels = soup.find_all('div', class_='exam-panel')
    result = {
        "questions": []
    }
    
    # Loop through all exam panels
    for exam_panel in all_exam_panels:
        formatted_options = []
        processed_text = set()
        # Find all divs with class question
        question_div = exam_panel.find('div', style="float: none;width: 98%;")
        
        # Find the p tag which contains the question and the table containing the question
        question_content = ""
        if question_div:
            for child in question_div.children:
                if child.name == 'p' or child.name == "img":
                    if child.text in processed_text:
                        continue
                    if child.name == "img":
                        question_content += f"<img src='{child['src']}' alt='Image'>"
                    else:
                        question_content += clean_text_for_question(child.text) +"\n"
                    processed_text.add(child.text)
                elif child.name == 'table':
                    question_content += str(child) 

                else:
                    question_content += clean_text_for_question(child.text) +"\n"
                    processed_text.add(child.text)
        
        for question in exam_panel.find_all('tr', class_='text-info'):
            question.extract()
        
        
        all_tr = exam_panel.find_all('tr')
        # In the second tr we will find the options
        options_tr = all_tr[0]
        correct_option_tr = all_tr[2]
        correct_option = correct_option_tr.find("strong", class_='text-success').text
        options = options_tr.find_all("span", class_='lang-1')
        
        for option in options:
            formatted_options.append(clean_text_for_question(option.text.strip()))
        # clean \n and extra spaces from the options
        formatted_options = [option.replace('\n', '').strip() for option in formatted_options]
        # for question
        question_content = question_content.replace('\n', '').strip()
        # clean too much space from the question
        possible_options = ['A', 'B', 'C', 'D', 'E']
        for i, opt in enumerate(['Option1', 'Option2', 'Option3', 'Option4', 'Option5']):
            if opt == correct_option:
                correct_option = possible_options[i]
                break
        

        result["questions"].append({
            "question": question_content, 
            "options": formatted_options, 
            "answer": correct_option,
            "solution": ""
        })

    # Write the result to a JSON file
    with open('/root/webScrapping/api_result_json/agricraf.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    response = sendQuestionsToP1(quizId,quizGuid,result,marks,negMarks)  
    logging.info("agrriCraf Questions sending to P1")
    if response.status_code == 200:
        logging.info("agrriCraf Questions sent to P1")
        return "check the panel for add question"
    else:
        logging.error("agrriCraf Questions not sent to P1")
        return " some error happend contact the creator"
def scrape_text(text):
    # Setup Selenium WebDriver
    # latex to image 
    # html_text = excelRun(text)
    
    html_text = excelRun(str(text),True)
    # else:
    #     html_text = excelRun(str(html))
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
import urllib.parse
def convert_latex_to_image_for_quizeer(latex, image_path):
    latex = latex.replace(' ', '\ ')
    latex = latex.replace(r"$", " ")
    latex = latex.replace('<br>', r'\newline')
    latex = latex.replace(r'\n', r'\newline')
    # print(latex)
    # print(image_path)
    # encoded_latex = urllib.parse.quote(latex)
    url = 'http://latex.codecogs.com/png.latex?' + latex
    response = requests.get(url)
    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            f.write(response.content)
        return True
    else:
        return False
import requests
from lxml.html import fromstring
from itertools import cycle
def convert_special_characters_to_html(text):
    # Unescape special characters
    unescaped_text = html.unescape(text)
    # Replace escaped characters with HTML code
    html_code = unescaped_text.replace('&amp;', '&') 
    html_code = html_code.replace('&lt;', '<') 
    html_code = html_code.replace('&gt;', '>')
    html_code = html_code.replace('&quot;', '"')
    html_code = html_code.replace('&nbsp;', ' ')
    return html_code
def contains_latex_symbol(text):
    latex_delimiters = ["\\(", "\\)", "\\[", "\\]", "$",r"mathrm{",r"frac{"]
    return any(delimiter in text for delimiter in latex_delimiters)
def clean_latex_code(expression):
    expression = re.sub(r'\$(.*?)\$', r'\\(\1\\)', expression)
    
    # Replace double backslashes \\ with a single backslash \
    # expression = expression.replace(r"\\", r"\")
    
    expression = expression.replace(r"\\mathrm", r"\mathrm")
    expression = expression.replace(r"\\frac", r"\frac")
    expression = expression.replace(r"\\text", r"\text")
    expression = expression.replace(r"\\times", r"\times")
    expression = expression.replace(r"\\sin", r"\sin")
    expression = expression.replace(r"\\cos", r"\cos")
    expression = expression.replace(r"\\tan", r"\tan")
    expression = expression.replace(r"\\int", r"\int")
    expression = expression.replace(r"\\sum", r"\sum")
    expression = expression.replace(r"\\rightarrow", r"\rightarrow")
    expression = expression.replace(r"\\overrightarrow", r"\overrightarrow")
    expression = expression.replace(r"\\overleftarrow", r"\overleftarrow")
    expression = expression.replace(r"\\leftarrow", r"\leftarrow")
    expression = expression.replace(r"\\therefore", r"\therefore")
    expression = expression.replace(r"\\left", r"\left")
    expression = expression.replace(r"\\right", r"\right")
    expression = expression.replace(r"\\alpha", r"\alpha")
    expression = expression.replace(r"\\beta", r"\beta")
    expression = expression.replace(r"\\gamma", r"\gamma")
    expression = expression.replace(r"\\Delta", r"\Delta")
    expression = expression.replace(r"\\delta", r"\delta")
    expression = expression.replace(r"\\epsilon", r"\epsilon")
    expression = expression.replace(r"\\varepsilon", r"\varepsilon")
    expression = expression.replace(r"\\zeta", r"\zeta")
    expression = expression.replace(r"\\eta", r"\eta")
    expression = expression.replace(r"\\theta", r"\theta")
    expression = expression.replace(r"\\vartheta", r"\vartheta")
    expression = expression.replace(r"\\iota", r"\iota")
    expression = expression.replace(r"\\kappa", r"\kappa")
    expression = expression.replace(r"\\lambda", r"\lambda")
    expression = expression.replace(r"\\mu", r"\mu")
    expression = expression.replace(r"\\nu", r"\nu")
    expression = expression.replace(r"\\xi", r"\xi")
    expression = expression.replace(r"\\pi", r"\pi")
    expression = expression.replace(r"\\varpi", r"\varpi")
    expression = expression.replace(r"\\rho", r"\rho")
    expression = expression.replace(r"\\varrho", r"\varrho")
    expression = expression.replace(r"\\sigma", r"\sigma")
    expression = expression.replace(r"\\varsigma", r"\varsigma")
    expression = expression.replace(r"\\tau", r"\tau")
    expression = expression.replace(r"\\upsilon", r"\upsilon")
    expression = expression.replace(r"\\phi", r"\phi")
    expression = expression.replace(r"\\varphi", r"\varphi")
    expression = expression.replace(r"\\chi", r"\chi")
    expression = expression.replace(r"\\psi", r"\psi")
    expression = expression.replace(r"\\omega", r"\omega")
    expression = expression.replace(r"\\Gamma", r"\Gamma")
    expression = expression.replace(r"\\Lambda", r"\Lambda")
    expression = expression.replace(r"\\Omega", r"\Omega")
    expression = expression.replace(r"\\Phi", r"\Phi")
    expression = expression.replace(r"\\Psi", r"\Psi")
    expression = expression.replace(r"\\Sigma", r"\Sigma")
    expression = expression.replace(r"\\Theta", r"\Theta")
    expression = expression.replace(r"\\Upsilon", r"\Upsilon")
    expression = expression.replace(r"\\Xi", r"\Xi")
    expression = expression.replace(r"\\Pi", r"\Pi")
    expression = expression.replace(r"\\left|", r"\left|")
    expression = expression.replace(r"\\right|", r"\right|")
    expression = expression.replace(r"\\sqrt", r"\sqrt")
    expression = expression.replace(r"\\cdot", r"\cdot")
    expression = expression.replace(r"\\cdot", r"\cdot")
    expression = expression.replace(r"\\neq", r"\neq")
    expression = expression.replace(r"\\geq", r"\geq")
    expression = expression.replace(r"\\leq", r"\leq")
    expression = expression.replace(r"\\approx", r"\approx")
    expression = expression.replace(r"\\infty", r"\infty")
    expression = expression.replace(r"\\pm", r"\pm")
    expression = expression.replace(r"\\div", r"\div")
    expression = expression.replace(r"\\langle", r"\langle")
    expression = expression.replace(r"\\rangle", r"\rangle")
    expression = expression.replace(r"\\times", r"\times")
    expression = expression.replace(r"\\geqslant", r"\geqslant")
    expression = expression.replace(r"\\leqslant", r"\leqslant")
    expression = expression.replace(r"\\subseteq", r"\subseteq")
    expression = expression.replace(r"\\supseteq", r"\supseteq")
    expression = expression.replace(r"\\subset", r"\subset")
    expression = expression.replace(r"\\supset", r"\supset")
    expression = expression.replace(r"\\not\\subseteq", r"\not\subseteq")
    expression = expression.replace(r"\\not\\supseteq", r"\not\supseteq")
    expression = expression.replace(r"\\not\\subset", r"\not\subset")
    expression = expression.replace(r"\\not\\supset", r"\not\supset")
    expression = expression.replace(r"\\not\\in", r"\not\in")
    expression = expression.replace(r"\\nsubseteq", r"\nsubseteq")
    expression = expression.replace(r"\\nsupseteq", r"\nsupseteq")
    expression = expression.replace(r"\\nsubset", r"\nsubset")
    expression = expression.replace(r"\\nsupset", r"\nsupset")
    expression = expression.replace(r"\\nsubseteq", r"\nsubseteq")
    expression = expression.replace(r"\\nsupseteq", r"\nsupseteq")
    expression = expression.replace(r"\\forall", r"\forall")
    expression = expression.replace(r"\\exists", r"\exists")
    expression = expression.replace(r"\\propto", r"\propto")
    expression = expression.replace(r"\\emptyset", r"\emptyset")
    expression = expression.replace(r"\\because", r"\because")
    expression = expression.replace(r"\\simeq", r"\simeq")
    expression = expression.replace(r"\\Rightarrow", r"\Rightarrow")
    expression = expression.replace(r"\\Leftarrow", r"\Leftarrow")
    expression = expression.replace(r"\\rightarrow", r"\rightarrow")
    expression = expression.replace(r"\\leftarrow", r"\leftarrow")
    expression = expression.replace(r"\\uparrow", r"\uparrow")
    expression = expression.replace(r"\\downarrow", r"\downarrow")
    expression = expression.replace(r"\\leftrightarrow", r"\leftrightarrow")
    expression = expression.replace(r"\\Leftrightarrow", r"\Leftrightarrow")
    expression = expression.replace(r"\\longrightarrow", r"\longrightarrow")
    expression = expression.replace(r"\\longleftarrow", r"\longleftarrow")
    expression = expression.replace(r"\\underset", r"\underset")
    expression = expression.replace(r"\r\n", "&nbsp<br> ")
    # expression = expression.replace(r"\\%", r"\%")
    # expression = expression.replace(r'\(', '')
    # expression = expression.replace(r'\)', '')
    expression = expression.replace(r'<br>', r' \\ ')
    # expression = expression.replace(r'&nbsp', r' \\ ')

    return expression
def format_mathjax_html(mathjax_str):
        # Remove unnecessary <br> tags
    mathjax_str = mathjax_str.replace(r'<br>', r' \\ ')

    # Format the LaTeX delimiters properly
    mathjax_str = mathjax_str.replace(r'\$', '$')
    mathjax_str = mathjax_str.replace(r'$', '')
    # mathjax_str = mathjax_str.replace(r' ', r'\ ')

    # Wrap in MathJax inline math delimiters
    mathjax_str = f'${mathjax_str}$'
    mathjax_str = clean_latex_code(mathjax_str)
    return mathjax_str
def getScrollerTest(url,language="en",startRange= 0,endRange= 0,testName="",testCat = ""):
    # service = Service(ChromeDriverManager().install())
    try:
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
    except Exception as e:
        print(str(e))
    formatted_questions = {"questions":[]}
    
    if 'https://u1.oliveboard.in/' in url:
        print(url)
        cookies = "_gcl_au=1.1.1410901082.1727696015; _ga=GA1.1.2069186666.1727696016; _fbp=fb.1.1727696015567.848452319157235268; susmid=224c983eNjk2NjAzOF5ea2RzMTY2OTleXmprc3NiY3ZeXmlyZGFp7d0b1deb; obem=kds16699%40gmail.com; uauth=224c983e86747930ebdd44d37d0b1deb; luauth=224c983e86747930ebdd44d37d0b1deb; obctapinfo2=1; obwb=2000; obctapinfo3=1; WZRK_G=548f09bbe7af4c42a53ec35e6a3b90b5; __utmz=94392130.1729159943.4.2.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utma=94392130.1469898232.1727696015.1729159943.1729577777.5; __utmc=94392130; obtredgt=d18327a096f0974d275096454a1d2f13; offerimg=1; obph=7717270389%2C+Regd+1237+days+ago%2C+Prem%3A+jkssbcv%2Cirdai; session=2K152493b7669dee5ae2492f56e4b176eb2e; obsession=BSDRGZ9XOTQ2OTY2MDM49VI5W8MS; lcatv=ssc; oblpv=https%253A%252F%252Fu1.oliveboard.in%252Fexams%252F%253Fc%253Dntpc1%2526i%253Dssc; __utmb=94392130.11.10.1729577777; pupnt=0; WZRK_S_65R-6K5-785Z=%7B%22p%22%3A1%2C%22s%22%3A1729580280%2C%22t%22%3A1729580280%7D; _ga_M8DH7WJ9QL=GS1.1.1729576869.7.1.1729580335.0.0.0"
        # hit url with this api to get result
        response = requests.get(url, headers={'Cookie': cookies})
        soup = BeautifulSoup(response.text, 'html.parser')
        i = 0 
        sections = []
        questionsInSections = []

        while (True):
            try:
                # print("sec-"+str(i)+" box")
                section = soup.find(class_= "sec-"+str(i)+" box")
                section_name = section.find("p").text
                questions = section.find_all("span",class_="map-qno")
                sections.append(section_name)
                questionsInSections.append(len(questions))
                # print(section)
                if(section is None):
                    break
                i+=1;
            except:
                break

        totalquestions = 0
        for i in questionsInSections:
            totalquestions += i
        i =0
        question_box_name = "qosblock"
        question_boxs = soup.find_all(class_=question_box_name)
        logging.info("Total Questions : "+str(question_boxs))
        opts = ["0","1","2","3","4"]
        # answer_values = ["A","B","C","D","E"]
        formatted_questions = {"questions":[]}
        for i in range(0,totalquestions):
            question_name = "qblock-"+str(i)
            Comprehension_class_name = "paneqcol panetxt"
            Comprehension =""
            if(question_boxs[i].find(class_=Comprehension_class_name)):
                Comprehension = question_boxs[i].find(class_=Comprehension_class_name).text.strip()
                Comprehension = decrypt_data(Comprehension)
                Comprehension = convertRelativeURLToAbsoluteURL(Comprehension, "https://u1.oliveboard.in/exams/solution/")
                Comprehension = convert_special_characters_to_html(Comprehension)
                Comprehension = scrapeExcel(Comprehension)
            options_scrape = []
            options = ["opt-"+str(i)+"-"+opts[j] for j in range(0,5)]
            question = question_boxs[i].find(id=question_name).text.strip()
            decrypted_question = decrypt_data(question)
            decrypted_question = convertRelativeURLToAbsoluteURL(decrypted_question, "https://u1.oliveboard.in/exams/solution/")
            answer_for_q = -1
            gotAnswere = False
            for j in range(0,5):
                option = question_boxs[i].find(id=options[j])
                if option is None:
                    continue
                option = option.find("div",class_="rightopt").text.strip()
                decrypted_option = decrypt_data(option)
                decrypted_option = convertRelativeURLToAbsoluteURL(decrypted_option, "https://u1.oliveboard.in/exams/solution/")
                decrypted_option = convert_special_characters_to_html(decrypted_option)
                decrypted_option = scrapeExcel(decrypted_option)

                if(gotAnswere != True):
                    onclick_attr = question_boxs[i].find(id=options[j]).get("onclick")
                    match = re.search(r'attemptAgain\((\d+),', onclick_attr)
                    if match:
                        first_argument = match.group(1)
                        answer_for_q = int(first_argument)
                        gotAnswere = True
                if(option != None):
                    options_scrape.append(decrypted_option)
            solution_name = "soltxt-"+str(i)
            solution = question_boxs[i].find(id=solution_name).text.strip()
            decrypted_solution = decrypt_data(solution)
            decrypted_solution = convertRelativeURLToAbsoluteURL(decrypted_solution, "https://u1.oliveboard.in/exams/solution/")
            decrypted_solution = convert_special_characters_to_html(decrypted_solution)
            decrypted_question = convert_special_characters_to_html(decrypted_question)
            decrypted_question = scrapeExcel(decrypted_question)
            decrypted_solution = scrapeExcel(decrypted_solution)
            answer = options_scrape[answer_for_q]
            if(len(Comprehension)>0):
                decrypted_question = Comprehension + "<br>" + decrypted_question
            for k in range(0,len(questionsInSections)):
                if(i<sum(questionsInSections[:k+1])):
                    formatted_questions["questions"].append({"question":decrypted_question,"options":options_scrape,"answer":answer,"solution":decrypted_solution,"section_name":sections[k]})
                    break
            # formatted_questions["questions"].append({"question":decrypted_question,"options":options_scrape,"answer":answer_for_q,"solution":decrypted_solution})



        with open("api_result_json/oliveboard.json", "w") as f:
            json.dump(formatted_questions, f, indent=4)
        return formatted_questions    
    if 'www.mockers.in/' in url:
        print(url)
        question_div = soup.find('ul', class_='ques-list')
        questions = question_div.find_all('li')
        # print(len(questions))
        for question in questions:
            
            question_text = question.find('div', class_='qsn-here')
            for child in question.find('div', class_='qsn-here').children:
                if child.name == 'img':
                    image_url = child['src']
                    # image_url = urljoin(url, image_url)
                    new_img_tag = f'<img src="{image_url}" alt="Question Image">'
                    question_text += new_img_tag

            options = question.find_all('div', class_='form-group')
            option_texts = [opt.find('h6') for opt in options]

            correct_option = question.find('label', class_='thisIsCorrect').find('span',class_="optionIndex").text.strip()
            # answer = f'Option {correct_option}: {option_texts[ord(correct_option) - ord("A")]}'
            answer = f'Option {correct_option}'
            # answer = f' {option_texts[ord(correct_option) - ord("A")]}'

            solution_text = question.find('div', class_='qn-solution')
            if solution_text is None:
                solution_text = ""
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
            print(formatted_question)
            # formatted_output = formatted_question + formatted_options + formatted_answer + formatted_solution
            # formatted_questions.append(formatted_output)
        # for i, formatted_question in enumerate(formatted_questions, start=1):
        #     print(f"Question {i}:\n{formatted_question}\n")\

        with open('/root/webScrapping/api_result_json/mockers.json', 'w') as f:
            json.dump(formatted_questions, f)
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
    elif "app.quizrr.in" in url:
        print(url)
        # https://app.quizrr.in/6605332e66c213425b947e71/66053524c0857387255f7d67/solutions
        packId = url.split('/')[-3]
        testId = url.split('/')[-2]
        formatted_questions = {
        'questions':[]
        }
        raw_formatted_questions = {
        'questions':[]
        }
        processing_formatted_question = {
        'questions':[]
        }
        # https://api.quizrr.in/api/test/solution/testDetails/66053524c0857387255f7d67?packId=6605332e66c213425b947e71
        url_to_fetch_section_question = f"https://api.quizrr.in/api/test/solution/testDetails/{testId}?packId={packId}"
        auth_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2Njc1NDc2OGJkMTE2MGU2NTEzMTYwMTYiLCJuYW1lIjoiQWFoYW4gTWlzaHJhIiwiZW1haWwiOiJtaXNocmFhc2h3YW5pMDczQGdtYWlsLmNvbSIsInVzZXJUeXBlIjoic3R1ZGVudCIsImlhdCI6MTc0MDcyMjU1MiwiZXhwIjoxNzQzMzE0NTUyfQ.xXxeU33UWxZxigF-BozhbfVU2mdh8ZZhULrDfptP65M"
        headers = {
            'Authorization': auth_token
        }
        response = requests.get(url_to_fetch_section_question, headers=headers)
        logging.info(response)
        response = response.json()
        sections_and_name = {}
        for section in response['data']['sections']:
            sectionId = section['sectionId']["_id"]
            sectionName = section['sectionId']["title"]
            sections_and_name[sectionId] = sectionName
        previous_question_length = 0
        for question_section in response['analysis']['sections']:
            sectionId = question_section['sectionId']
            question_len = len(question_section['questions'])
            for i in range(0,question_len):
                offset = previous_question_length + i
                url_to_fetch_question = f"https://api.quizrr.in/api/test/solution/{testId}?&limit=1&offset={offset}&pack={packId}"
                print(url_to_fetch_question)
                question_response = requests.get(url_to_fetch_question, headers=headers)
                question_response = question_response.json()
                for question_data in question_response['data']:
                    formatted_options = []
                    if sections_and_name[sectionId] == "Physics Numerical":
                        question = question_data['questionId']['question']['text']
                        solution = question_data['questionId']['solution']['text']
                        for option in question_data['questionId']['options']:
                            option = option['text']
                            # option = convert_special_characters_to_html(option)
                            # option = BeautifulSoup(option, 'html.parser')
                            formatted_options.append(str(option))
                        answer = question_data['questionId']['correctValue']
                    else:
                        question = question_data['questionId']['question']['text']
                        solution = question_data['questionId']['solution']['text']
                        formatted_options = []
                        answer = ""
                        options_ = ['A','B','C','D']
                        i = 0
                        for option in question_data['questionId']['options']:
                            if option['isCorrect']:
                                answer = options_[i]
                            option = option['text']
                            # option = convert_special_characters_to_html(option)
                            # option = BeautifulSoup(option, 'html.parser')
                            formatted_options.append(str(option))
                            # formatted_options.append(option['text'])
                            i += 1
                # question = convert_special_characters_to_html(question)
                # answer = convert_special_characters_to_html(answer)
                # solution = convert_special_characters_to_html(solution)
                
                question = scrapeExcel(question)
                answer = scrapeExcel(answer)
                solution = scrapeExcel(solution)
                for i in range(len(formatted_options)):
                    formatted_options[i] = scrapeExcel(formatted_options[i])
               
                ques_uuid = str(uuid.uuid4())
                ans_uuid = str(uuid.uuid4())
                sol_uuid = str(uuid.uuid4())
                ques_img_path = f"/var/www/html/images/{ques_uuid}.png"
                ans_img_path = f"/var/www/html/images/{ans_uuid}.png"
                sol_img_path = f"/var/www/html/images/{sol_uuid}.png"
                
                raw_formatted_questions['questions'].append({
                    'question':question,
                    'options':formatted_options,
                    'answer':answer,
                    'solution':solution,
                    'section_name':sections_and_name[sectionId]
                    })
                
                # HANDLING OF LATEXT AND IMAGE
                
                question = question.replace("br/","br")
                if "$" in question:
                    question = question.replace("$","")
                question_ = format_mathjax_html(question)
                question_ = format_mathjax_html(question_)
                # answer = format_mathjax_html(answer)
                solution_ = format_mathjax_html(solution)
                solution_ = format_mathjax_html(solution_)
                processing_for_option = []
                for i in range(len(formatted_options)):
                    processing_for_option.append(format_mathjax_html(formatted_options[i]))
                with open("/root/webScrapping/bytxt.txt", "w") as f:
                    f.write(solution_)
                processing_formatted_question['questions'].append({
                    'question':question_,
                    'options':processing_for_option,
                    'answer':answer,
                    'solution':solution_,
                    'section_name':sections_and_name[sectionId]
                })
                
                if get_image("quizrr",question_, ques_img_path):
                        question_ = f'<img src="https://fc.edurev.in/images/{ques_uuid}.png" alt="Question Image">'
                
                solution_ = solution_.replace("br/","br")
                if "br" in solution_:
                    with open('/root/webScrapping/bytxt.txt', 'w') as f:
                        # reading the content then appedn in it 
                        f.write(solution_)

                if "$" in solution_:
                    solution_ = solution_.replace("$","")
                if get_image("quizrr",solution_, sol_img_path):
                        solution_ = f'<img src="https://fc.edurev.in/images/{sol_uuid}.png" alt="Solution Image">'
                
                print(solution_)
                result_option_formatted = []
                for i in range(len(formatted_options)):
                    option_uuid = str(uuid.uuid4())
                    option_img_path = f"/var/www/html/images/{option_uuid}.png"
                    option = formatted_options[i]
                    
                    option = option.replace("br/","br")
                    if "$" in formatted_options[i]:
                        option = formatted_options[i].replace("$","").replace("\\(\\(","").replace("\(\(","")
                    option_ = format_mathjax_html(option)
                    # formatted_options[i] = formatted_options[i].replace("br/","br")
                    if get_image("quizrr",option_, option_img_path) and len(option) != 0:
                        formatted_options[i] = f'<img src="https://fc.edurev.in/images/{option_uuid}.png" alt="Option Image">'
                formatted_questions['questions'].append({
                        'question':question_.replace("\\(\\(","").replace("\(\(",""),
                        'options':formatted_options,
                        'answer':answer.replace("\\(\\(","").replace("\(\(",""),
                        'solution':solution_.replace("\\(\\(","").replace("\(\(",""),
                        'section_name':sections_and_name[sectionId]
                    })
                # if(offset == 5):
                #     with open('/root/webScrapping/api_result_json/processing_quizerr_testing.json', 'w') as f:
                #         json.dump(formatted_questions, f)
                #     break
                # print(formatted_questions)
            previous_question_length += question_len 
        with open('/root/webScrapping/api_result_json/quizerr.json', 'w') as f:
            json.dump(formatted_questions, f)
        with open('/root/webScrapping/api_result_json/processing_quizerr.json', 'w') as f:
            json.dump(processing_formatted_question, f)
        with open('/root/webScrapping/api_result_json/raw_quizerr.json', 'w') as f:
            json.dump(raw_formatted_questions, f)
    elif "sstar.com" in url :
        cookies=["_gcl_au=1.1.1351298700.1719813792; _clck=uw7cw9%7C2%7Cfn3%7C0%7C1643; _ga=GA1.2.9252008.1719813793; _gid=GA1.2.1905579535.1719813793; _fbp=fb.1.1719813793042.307039025621393064; gclid=undefined; moe_uuid=9267225b-3920-4178-8d29-7602a9cf25e0; USER_DATA=%7B%22attributes%22%3A%5B%5D%2C%22subscribedToOldSdk%22%3Afalse%2C%22deviceUuid%22%3A%229267225b-3920-4178-8d29-7602a9cf25e0%22%2C%22deviceAdded%22%3Atrue%7D; SOFT_ASK_STATUS=%7B%22actualValue%22%3A%22not%20shown%22%2C%22MOE_DATA_TYPE%22%3A%22string%22%7D; OPT_IN_SHOWN_TIME=1719813795386; PUSH_TOKEN=%7B%22actualValue%22%3A%22cWGzHo9Iel0%3AAPA91bGIQsM1AAVv48GTJrEAKJyXjwVgyT_XZrCE4Pk54ZA15XelUvNbhF5M1_537qD-8ioFssI6yRpFAMXi9uyvVlL1YUXNsKaPh6dLjwrYsctCSE_2txJ4eCRlq_1Wr17lR3xnfhal%22%2C%22MOE_DATA_TYPE%22%3A%22string%22%7D; mp_6193c44f66c36c190cc1_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A1906ce3e18a1ea6-001ed209637604-26001f51-e1000-1906ce3e18b1ea6%22%2C%22%24device_id%22%3A%20%221906ce3e18a1ea6-001ed209637604-26001f51-e1000-1906ce3e18b1ea6%22%2C%22%24search_engine%22%3A%20%22google%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_7M6YSLDGB0=GS1.2.1719826378.2.1.1719826915.0.0.0; _clsk=19pvrro%7C1719826915979%7C20%7C1%7Ct.clarity.ms%2Fcollect; _clsk=19pvrro%7C1719826915979%7C20%7C1%7Ct.clarity.ms%2Fcollect; SESSION=%7B%22sessionKey%22%3A%22c6f7e4b3-e89c-44ff-9257-f73d2d434788%22%2C%22sessionStartTime%22%3A%222024-07-01T09%3A33%3A00.201Z%22%2C%22sessionMaxTime%22%3A1800%2C%22customIdentifiersToTrack%22%3A%5B%5D%2C%22sessionExpiryTime%22%3A1719828717282%2C%22numberOfSessions%22%3A2%7D; HARD_ASK_STATUS=%7B%22actualValue%22%3A%22granted%22%2C%22MOE_DATA_TYPE%22%3A%22string%22%7D; SUBSCRIPTION_DETAILS=%7B%22domain%22%3A%22https%3A%2F%2Fatpstar.com%22%2C%22token%22%3A%22cWGzHo9Iel0%3AAPA91bGIQsM1AAVv48GTJrEAKJyXjwVgyT_XZrCE4Pk54ZA15XelUvNbhF5M1_537qD-8ioFssI6yRpFAMXi9uyvVlL1YUXNsKaPh6dLjwrYsctCSE_2txJ4eCRlq_1Wr17lR3xnfhal%22%2C%22endpoint%22%3A%22https%3A%2F%2Ffcm.googleapis.com%2Ffcm%2Fsend%2F%22%2C%22keys%22%3A%7B%22p256dh%22%3A%22BN5a-tP4ExScpQNXPJhbv3Cw8Xyg9UvP2slXuZHZi-gwMcJFYU9hoARh4PJZT6XmSgzSEn0HdeDbiZkuja4ST20%22%2C%22auth%22%3A%22a1dRNOA3pfax4zeF6bl6yA%22%7D%7D; ci_sessions=87aad13d4146e1a4d48a8f0487dc7dd2a86ce329",
                 "gclid=undefined; _ga=GA1.2.544895185.1719820975; _gid=GA1.2.1606946289.1719820975; _clck=1bh6py8%7C2%7Cfn3%7C0%7C1643; _fbp=fb.1.1719820975356.212533506981775731; moe_uuid=7307412a-81c4-4750-8fe0-505506d43422; USER_DATA=%7B%22attributes%22%3A%5B%5D%2C%22subscribedToOldSdk%22%3Afalse%2C%22deviceUuid%22%3A%227307412a-81c4-4750-8fe0-505506d43422%22%2C%22deviceAdded%22%3Atrue%7D; SOFT_ASK_STATUS=%7B%22actualValue%22%3A%22not%20shown%22%2C%22MOE_DATA_TYPE%22%3A%22string%22%7D; OPT_IN_SHOWN_TIME=1719820996139; _gcl_au=1.1.318896109.1719820974.1058781519.1719821062.1719821061; PUSH_TOKEN=%7B%22actualValue%22%3A%22cFiftb2hS50%3AAPA91bFE26yD3-vyx2lCYTO8eoPw-MSiuwwQrG8ix0U07q81GPGOrYbRmBBFcu1xKFfYn1ITShBGMIySNvCSnBV9YFuMqTBpgBLxB9m6ZLWDDJM7x0NUVu6Ny4JU0db0YrjVU7zw7KI2%22%2C%22MOE_DATA_TYPE%22%3A%22string%22%7D; ci_sessions=1ea1f9a7b3709a89faa3a770f90529f4c947ded1; _gat_UA-164057240-1=1; mp_6193c44f66c36c190cc1_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A1906d5179172634-031cac949c729a-26001f51-100200-1906d5179182635%22%2C%22%24device_id%22%3A%20%221906d5179172634-031cac949c729a-26001f51-100200-1906d5179182635%22%2C%22%24search_engine%22%3A%20%22google%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_7M6YSLDGB0=GS1.2.1719820975.1.1.1719821937.0.0.0; _clsk=1wfnt6f%7C1719821937690%7C19%7C1%7Cq.clarity.ms%2Fcollect; SESSION=%7B%22sessionKey%22%3A%22f8defe1b-6b38-4bc3-a59b-780df8b40e85%22%2C%22sessionStartTime%22%3A%222024-07-01T08%3A02%3A58.051Z%22%2C%22sessionMaxTime%22%3A1800%2C%22customIdentifiersToTrack%22%3A%5B%5D%2C%22sessionExpiryTime%22%3A1719823738898%2C%22numberOfSessions%22%3A1%7D; HARD_ASK_STATUS=%7B%22actualValue%22%3A%22granted%22%2C%22MOE_DATA_TYPE%22%3A%22string%22%7D; SUBSCRIPTION_DETAILS=%7B%22domain%22%3A%22https%3A%2F%2Fatpstar.com%22%2C%22token%22%3A%22cFiftb2hS50%3AAPA91bFE26yD3-vyx2lCYTO8eoPw-MSiuwwQrG8ix0U07q81GPGOrYbRmBBFcu1xKFfYn1ITShBGMIySNvCSnBV9YFuMqTBpgBLxB9m6ZLWDDJM7x0NUVu6Ny4JU0db0YrjVU7zw7KI2%22%2C%22endpoint%22%3A%22https%3A%2F%2Ffcm.googleapis.com%2Ffcm%2Fsend%2F%22%2C%22keys%22%3A%7B%22p256dh%22%3A%22BKyFYPlz_f_w91qbm7p8_HJ6L3Qki_nzhGl_Ajsr7TktJahATaVuriILvnFOWix0DR8R7TT6z9zvTybKq-6ksyk%22%2C%22auth%22%3A%22C0t4XtkreHCnEtz5QZR_vg%22%7D%7D"
                 ]
        for cookie in cookies:
            try:
                logging.info("Getting data from atpstar.com with cookie: "+cookie)
                header = {
                    'Cookie': cookie,
                }
                response = requests.get(url , headers=header)
                # getting dbdata variable from a script in response 
                html_content = response.text 
                soup = BeautifulSoup(html_content, 'html.parser') 
                script_tags = soup.find_all('script') 

                # print(script_tags)
                input_data = {}
                found = False
                for script_tag in script_tags: 
                    # print(script_tag.string)
                    if script_tag.string: 
                        script_content = script_tag.string 
                        if "dbdata" in script_content:
                            found = True
                            # print(script_content)
                            question_array = script_content.split("var dbdata = ")[1]
                            input_data['questions']  = json.loads(question_array)   
                if found == False:
                    break
                formatted_questions = {
                    'questions':[]
                }
                for question_json in input_data['questions']:
                
                    question = question_json.get('qm_question', '').replace('&#39;', "'").replace('\\/', '/')
                    # Extract options
                    options = question_json.get('get_question_options', [])
                    options_symbol = ['A', 'B', 'C', 'D']
                    answer = ""
                    i = 0
                    formatted_options = []
                    for option in options:
                        if option.get('qo_correct') == "Yes":
                            answer += options_symbol[i] + " "
                        option_text = option.get('qo_option', '').replace('&#39;', "'").replace('\\/', '/')
                        i += 1
                        # print(option_text)
                        formatted_options.append(option_text)
                    

                    # Extract solution
                    solution = question_json.get('qm_solution', '').replace('\\/', '/')  
                    formatted_questions['questions'].append( {
                        'question': question,
                        'options': formatted_options,
                        'solution': solution,
                        'answer': answer,
                        'type':question_json.get('qm_answer_type', '')
                    } 
                    )
                with open('/root/webScrapping/api_result_json/atpstar.json', 'w') as f:
                    json.dump(formatted_questions, f)
                break
            except Exception as e:
                print(str(e))
                logging.info("Error in getting data from atpstar.com with cookie: "+str(e))
    elif "www.smartkeeda.com" in url:
        try:
            urlToGetQuestions = "https://www.smartkeeda.com/api/GetQuizData"
            startRange = int(startRange)
            endRange = int(endRange)
            logging.info("TEST NAME SMART KEEDA : '"+str(testName) +"'")
            logging.info("TEST CAT SMART KEEDA : '"+str(testCat) +"'")
            for i in range(startRange,endRange+1):
                try:
                    logging.info("Working on smart Keeda Test Number :" + str(i))
                    payload = {"excersice":testCat ,"testname":f"{testName} "+str(i)}
                    response = requests.post(urlToGetQuestions,json=payload)
                    response = response.json()

                    data = response['data']

                    # data = data.json()
                    questions = data['questions']
                    directionsEnglish = ""
                    directionsHindi = ""
                    if 'quizData' in data:
                        quizData = data['quizData']
                        if 'sumEng' in data['quizData']:
                            directionsEnglish =  data['quizData']['sumEng']
                        if 'sumHin'  in data['quizData']:
                            directionsHindi =  data['quizData']['sumHin']

                    for ques in questions:
                        question = ""
                        formatted_options = []
                        answer = ""
                        solution = ""
                        if(language == "en"):
                            question = ques['q']
                            # question = directionsEnglish + "<br>"+question
                            formatted_options.append(str(ques['oa']).replace("\n","").replace("\r","").replace("\t",""))
                            formatted_options.append(str(ques['ob']).replace("\n","").replace("\r","").replace("\t",""))
                            formatted_options.append(str(ques['oc']).replace("\n","").replace("\r","").replace("\t",""))
                            formatted_options.append(str(ques['od']).replace("\n","").replace("\r","").replace("\t",""))
                            if 'oe' in ques:
                                formatted_options.append(str(ques['oe']).replace("\n","").replace("\r","").replace("\t",""))
                            answer = ques['correct']; 
                            solution = ques['explanation']
                        else:  # For Hindi or other language support
                            question = ques['qHin']  # Hindi question
                            # question = directionsHindi + "<br>"+question
                            formatted_options = []
                            formatted_options.append(str(ques['oaHin']).replace("\n","").replace("\r","").replace("\t",""))
                            formatted_options.append(str(ques['obHin']).replace("\n","").replace("\r","").replace("\t",""))
                            formatted_options.append(str(ques['ocHin']).replace("\n","").replace("\r","").replace("\t",""))
                            formatted_options.append(str(ques['odHin']).replace("\n","").replace("\r","").replace("\t",""))
                            if 'oeHin' in ques:  # Check if the "oeHin" option exists
                                formatted_options.append(str(ques['oeHin']).replace("\n","").replace("\r","").replace("\t",""))
                            answer = ques['correct']
                            solution = ques['explanation']
                        
                        question = scrapeExcel(question)
                        # question = HtmlToRemoveWaterMark(question)
                        
                        answer = scrapeExcel(answer)
                        # answer = HtmlToRemoveWaterMark(answer)
                        solution = scrapeExcel(solution)
                        # solution = HtmlToRemoveWaterMark(solution)
                        for i in range(len(formatted_options)):
                            formatted_options[i] = scrapeExcel(formatted_options[i])
                            # formatted_options[i] = HtmlToRemoveWaterMark(formatted_options[i])
                        # remove math tex elment
                        question = convert_special_characters_to_html(question)
                        answer = convert_special_characters_to_html(answer)
                        solution = convert_special_characters_to_html(solution)
                        question = mathTexToImg(question)
                        answer = mathTexToImg(answer)
                        solution = mathTexToImg(solution)
                        solution = solution.replace("<br/>\n<br/>","<br>").replace("\r\n<div>\r\n\t&nbsp;</div>\r\n","").replace("\n<div>\r\n\t </div>","").replace("\r\n\t","").replace("\n","").replace("<div style=\"font-size: 13px;\"> </div>","").replace("<br/>","")
                        answer = answer.replace("<br/>\n<br/>","<br/>\n")
                        question = question.replace("<br/>\n<br/>","<br/>\n")
                        question = question.replace("<br/>","")
                        for i in range(len(formatted_options)):
                            formatted_options[i] = mathTexToImg(formatted_options[i])
                            formatted_options[i] = formatted_options[i].replace("<br/>\n<br/>","<br/>\n")
                        if(language == "en"):
                            formatted_questions['questions'].append({
                                'question':question,
                                'options':formatted_options,
                                'answer':answer,
                                'solution':solution,
                                'ques_parag':directionsEnglish.replace("text-align: justify;","").replace("text-align: center;","")
                                
                            })
                            # question = directionsEnglish.replace("text-align: justify;","").replace("text-align: center;","") + "<br><div>"+question+ "</div>"
                        else: 
                            formatted_questions['questions'].append({
                                'question':question,
                                'options':formatted_options,
                                'answer':answer,
                                'solution':solution,
                                'ques_parag':directionsHindi.replace("text-align: justify;","").replace("text-align: center;","")
                                
                            })
                            # question = directionsHindi.replace("text-align: justify;","").replace("text-align: center;","") + "<br><div>"+question+ "</div>"
                        # formatted_questions['questions'].append({
                        #     'question':question,
                        #     'options':formatted_options,
                        #     'answer':answer,
                        #     'solution':solution,
                            
                        # })
                except Exception as e:
                    print(e)
                    logging.info(str(e))
        except Exception as e:
                print(e)
                logging.info(str(e))
    elif "https://testbook.com/" in url:
        try:
            test_id = url.split('?')[0].split('/')[-1]
            # ashwini code,sushil code,veenu , rajat,SATISH, KhushDeep,anjali --> last updated
            auth_codes = [
                'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjY1Nzk5NTRmODBiN2U5MGU2NDhkN2VjZCIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNS0wMy0xOVQwNzowNjo1MC40ODkwNjg2NTJaIiwiaWF0IjoiMjAyNS0wMi0xN1QwNzowNjo1MC40ODkwNjg2NTJaIiwibmFtZSI6IkFzaHdhbmkiLCJlbWFpbCI6Im1pc2hyYWFzaHdhbmkwNzNAZ21haWwuY29tIiwib3JnSWQiOiIiLCJpc0xNU1VzZXIiOmZhbHNlLCJyb2xlcyI6InN0dWRlbnQifQ.baPLrphi7Humc7O5RE9IcH7tgh1aPF25jgqSB7R3pa7vSGrTZzKfWwrnz2P2WD5CGhp_QLQlM8Eo9w1sIRpCIN7h6GDrKAsqW5JAi1mA0r4xTqmfkMwA-vaEhTS7TwkAEfphqasrgNgE1UvjcQvt79Sx3U28SvSoCvk6UGhhT3M',
                'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjViZWE2NTlkNmZmNmZlMjFhNDczZmNkMiIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNS0wNC0xNFQwOTozMToxMC4wODQ1MTAwOTdaIiwiaWF0IjoiMjAyNS0wMy0xNVQwOTozMToxMC4wODQ1MTAwOTdaIiwibmFtZSI6Imx1Y2t5IiwiZW1haWwiOiJsdWNreXRhbmVqYTk5OUBnbWFpbC5jb20iLCJvcmdJZCI6IiIsImlzTE1TVXNlciI6ZmFsc2UsInJvbGVzIjoic3R1ZGVudCJ9.gtICj_P-4oIzj0Lk4Vt0hbbBCoc7ZWh4NWMIFQgsU_-F_--mQIch0lBaIMhUsQtZqn9udE7TGnqiKKHtA_Fe3GC8AiK2sIrxHwD38i3GT8q0ijUWDjbWtm2iKWz-kEQ4AocR6_p1yLXvrENk7Ml52k5dLvUcE45UuHFBviw9-tA',
                'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjY2NmJmMmM5OTlhNzhiNTgxMjlmYzdlNiIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNS0wMy0yOVQxMTozMDozOC4zMjU4Mzk4N1oiLCJpYXQiOiIyMDI1LTAyLTI3VDExOjMwOjM4LjMyNTgzOTg3WiIsIm5hbWUiOiJWRyIsImVtYWlsIjoic2Fpbmlwcml5YW5rYTY1NjE0QGdtYWlsLmNvbSIsIm9yZ0lkIjoiIiwiaXNMTVNVc2VyIjpmYWxzZSwicm9sZXMiOiJzdHVkZW50In0.Wn9bPwqR0vvgaXsEz2WpnVKlZPjtAReca5zWLDHw1LrLt7DbgqDwUeQsqLdEBTMV6lsMliERRxFQBdonyu0N6WaFXEusEC_z_CqL5yJPkqJ4hoJUSeuYiQ6RerIySFm3F_BIAQ0W3Uthsfci-YS_F80lHOikum4lwn-TczIKvgw',
                'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjYzNWJiMzE3N2NjOTJjN2Y3OTNhNGI5MCIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNS0wMy0yMFQwNTo1MTozMS4zMzkyNjUwOTNaIiwiaWF0IjoiMjAyNS0wMi0xOFQwNTo1MTozMS4zMzkyNjUwOTNaIiwib3JnSWQiOiIiLCJpc0xNU1VzZXIiOmZhbHNlLCJyb2xlcyI6InN0dWRlbnQifQ.wEwHinWh3XVo50KkLr6p3zVUyBrjQhxhmL8IipEz1fbG0YyYGaH5lvhriS7XXiLYYQiBeMIN6dDq8ZPDCYBQ4Wktrm-V89diR6X9NuklcKr9x4tAfzTt5QEU6bwbHJQBqH1XTIWA3nK3OlxYBe3eaSy4M0hLyp2nXnzsaiA6eeY',
                'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjYzYmQzMmRlNDI4NmZlMmM0NmI3OGMyOSIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNS0wMy0xOVQxMDoxNToyNy4wODQxNTE4NzJaIiwiaWF0IjoiMjAyNS0wMi0xN1QxMDoxNToyNy4wODQxNTE4NzJaIiwib3JnSWQiOiIiLCJpc0xNU1VzZXIiOmZhbHNlLCJyb2xlcyI6InN0dWRlbnQifQ.IL81n01VIWgrvyVp92PyIAukmaxSqkUN08o1RwqyYf7yn1FRYUD6wQx1haxzb6XntesLtLCYkQbWmR07nkLy0y1rkdmQTx7cG7oJFG9VImKXh-eGgCcr2Qo2_6NUZFIhYirN43x9em5w1_oGcQWB_RqniHutn4bYi763HC9OYBU',
                        'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjYyZjg4NDBmODFmNjJmZDc2ZmE0ZTFjZSIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNS0wNC0wNlQwMzo1MjowMS4zNzU5MTEwMjJaIiwiaWF0IjoiMjAyNS0wMy0wN1QwMzo1MjowMS4zNzU5MTEwMjJaIiwibmFtZSI6IktodXNoZGVlZXAiLCJlbWFpbCI6InlvcmFiaWg3NTBAc2ZwaXhlbC5jb20iLCJvcmdJZCI6IiIsImlzTE1TVXNlciI6ZmFsc2UsInJvbGVzIjoic3R1ZGVudCJ9.lW-oiFbe5SWWjBOfejSQcFMaAXYsNLSiMpEPPFK9Ugr9NdknfI8CWQ-JxqCtPJG9K-KxSl3rnAI046hWFHOzvO5DlUyONc8Rdd3fhZsFWErRHFq2C-CxFAgECxJbOoO4Qd1gZdzehg9XOm0YHCsxNwhsMdFajDcMdV9F-TdZn48',
                                'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjY3Nzc4MDdlY2RmMDZiMzAyZjA0Y2MzMiIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNS0wNC0xMFQwMzo0MDozNy40OTM3MDQ1MzNaIiwiaWF0IjoiMjAyNS0wMy0xMVQwMzo0MDozNy40OTM3MDQ1MzNaIiwibmFtZSI6Ik5pbmRpeWEgU2hhcm1hIiwiZW1haWwiOiJuaW5kaXlhc2hhcm1hOVFAZ21haWwuY29tIiwib3JnSWQiOiIiLCJpc0xNU1VzZXIiOmZhbHNlLCJyb2xlcyI6InN0dWRlbnQifQ.Afbi3BYENaUlQQ_32cZUveeN-bquusT1Ke5RjfVWyrd6ghhZSkDXum7OguV9QJSNmJ8rHUQH4_fSwbhWMAKKj6veMxi23qewkhEI6kXw8-nZT2g_yCAPK6s5CFGBBI1Vu_7Q5emLEaV5G0o1HELtZUM8BC5bxTxJxZpFk7OjKOw'        ]
            
            # params = {
            #     'auth_code':"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjViZWE2NTlkNmZmNmZlMjFhNDczZmNkMiIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNC0wNy0wM1QwNDoxMzoyOC41NjkyODE5ODJaIiwiaWF0IjoiMjAyNC0wNi0wM1QwNDoxMzoyOC41NjkyODE5ODJaIiwibmFtZSI6Imx1Y2t5IiwiZW1haWwiOiJsdWNreXRhbmVqYTk5OUBnbWFpbC5jb20iLCJvcmdJZCI6IiIsImlzTE1TVXNlciI6ZmFsc2UsInJvbGVzIjoic3R1ZGVudCJ9.iCEKSYJmciL8Znd4XaEtU5Wna0v07Y9n1jMxmPKsS7ELtGqfxQhuw196hM_E4blvzoFRMoOcvgO2ZgEXWygHysFP-RJMWGN18Yhzc9g6xQtpZiI6912kgMDU5mnnzm6u31hno5J66rXukLc3bkiyDLQLnXVx8H1-4-Z9LYre0k0"
            # }
            for auth in auth_codes:
                try:
                    # print(auth)
                    params = {
                        'auth_code':auth
                    }
                    get_answere_url = f"https://api.testbook.com/api/v2/tests/{test_id}/answers".format(test_id)    
                    get_questions_url = f"https://api.testbook.com/api/v2/tests/{test_id}".format(test_id)
                    formatted_questions = {
                    'questions':[]
                    }
                    response = requests.get(get_questions_url, params=params)
                    # print(response)
                    # if test is not attempted
                    #         {
                    #     "success": false,
                    #     "message": "You have not completed the test, can not serve solutions.",
                    #     "curTime": "2024-06-05T11:38:08.758Z"
                    # }
                    answers = requests.get(get_answere_url, params=params)
                    # h = HTMLParser()
                    abcd = []
                    questions = response.json()['data']['sections']
                    for section in questions:
                        if section['questions'] :
                            section_name = ""
                            if 'title' in section:
                                section_name = section['title']
                            
                            for question in section['questions']:
                                formatted_options = []
                                question_data = question[language]['value']
                                if 'comp' in question[language]:
                                    question_data = question[language]['comp'] + " \n" +question_data
                                
                                # print(question_data)
                                question_id = question['_id']
                                if("options" in  question[language]):
                                    for option in question[language]['options']:
                                        # option = html.unescape(option)
                                        option = option['value']
                                        option = convert_special_characters_to_html(option)
                                        option = BeautifulSoup(option, 'html.parser')
                                        formatted_options.append(str(option))
                                else:
                                    logging.info("question not worked in finding options: "+ str(question[language]['options']))
                                    continue
                                if 'data' in answers.json() and 'correctOption' in answers.json()['data'][question_id]:
                                    answer = answers.json()['data'][question_id]['correctOption']
                                else:
                                    logging.info("question not worked in finding data in answer: "+ str(answers.json()['data'][question_id]))
                                    continue
                                question = convert_special_characters_to_html(question_data)
                                answer = convert_special_characters_to_html(answer)
                                if 'data' in answers.json() and 'sol' in answers.json()['data'][question_id]:
                                    solution = answers.json()['data'][question_id]['sol'][language]['value']
                                else:
                                    logging.info("question not worked in sol: " + str(answers.json()['data'][question_id]))
                                    continue
                                solution = convert_special_characters_to_html(solution)
                                question = BeautifulSoup(question, 'html.parser')
                                answer = BeautifulSoup(answer, 'html.parser')
                                solution = BeautifulSoup(solution, 'html.parser')
                                answer = str(answer)
                                question = str(question)
                                solution = str(solution)
                                  
                                solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/in_news.png\" width=\"26px\"/>','')
                                solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/hinglish-image.png\" width=\"26px\"/>','')
                                solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/alternate-methord-image.png\" width=\"26px\"/>','')
                                solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/shortcut-trick-image.png\" width=\"26px\"/>','')
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
                                
                                solution = solution.replace('<span style=\"display: flex;gap: 6px;align-items: center;\"><u style=\"font-size: 21px; font-weight: bolder; font-family: var(--bs-body-font-family); text-align: var(--bs-body-text-align);\">Key Points</u></span>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Explanation</span></strong>')
                                solution = solution.replace('<strong><span style=\"vertical-align: middle; font-size: 21px;\"><u>Key Points</u></span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Explanation</span></strong>')
                                solution = solution.replace('<strong><span style=\"vertical-align: middle;font-size: 21px;\"><u>Key Points</u></span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Explanation</span></strong>')
                                solution = solution.replace('<strong><span font-size:=\"\" style=\"\" vertical-align:=\"\"><u>Key Points</u></span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Explanation</span></strong>')
                                solution = solution.replace('<strong><span style=\"vertical-align: middle;font-size: 21px;\"><u>Additional Information</u></span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Other Related Points</span></strong>')
                                solution = solution.replace('<strong><span font-size:=\"\" style=\"\" vertical-align:=\"\"><u>Additional Information</u></span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Other Related Points</span></strong>')
                                solution = solution.replace('<strong><span style=\"\">Additional Information:</span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Other Related Points</span></strong>')
                                
                                solution = solution.replace('<strong><span style=\"vertical-align: middle;font-size: 21px;\"><u>Important Points</u></span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Important Points</span></strong>')
                                solution = solution.replace('<strong><span font-size:=\"\" style=\"\" vertical-align:=\"\"><u>Important Points</u></span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Important Points</span></strong>')
                                solution = solution.replace('<strong><span font-size:=\"\" style=\"\" vertical-align:=\"\"><u>Important Points</u></span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Important Points</span></strong>')
                                solution = solution.replace('<strong><span style=\"display: flex;gap: 6px;align-items: center;\"><u style=\"font-size: 21px;\">Important Points</u></span></strong>','<strong><span style=\"vertical-align: middle;font-size: 18px;\">Important Points</span></strong>')
                                
                                abcd.append({
                                    'question':question,
                                    'options':formatted_options,
                                    'answer':answer,
                                    'solution':solution,
                                    'section':section_name
                                })
                                with open('/root/webScrapping/api_result_json/testbook_new.json', 'w') as f:
                                    # append new json
                                    json.dump(abcd, f)
                                  
                                # Remove mjx container 
                                question = scrapeExcel(question)
                                # question = HtmlToRemoveWaterMark(question)
                                
                                answer = scrapeExcel(answer)
                                # answer = HtmlToRemoveWaterMark(answer)
                                solution = scrapeExcel(solution)
                                # solution = HtmlToRemoveWaterMark(solution)
                                for i in range(len(formatted_options)):
                                    formatted_options[i] = scrapeExcel(formatted_options[i])
                                    # formatted_options[i] = HtmlToRemoveWaterMark(formatted_options[i])
                                # remove math tex elment
                                question = convert_special_characters_to_html(question)
                                answer = convert_special_characters_to_html(answer)
                                solution = convert_special_characters_to_html(solution)
                                question = mathTexToImg(question)
                                answer = mathTexToImg(answer)
                                solution = mathTexToImg(solution)
                                for i in range(len(formatted_options)):
                                    formatted_options[i] = mathTexToImg(formatted_options[i])
                                formatted_questions['questions'].append({
                                    'question':question,
                                    'options':formatted_options,
                                    'answer':answer,
                                    'solution':solution,
                                    'section_name':section_name
                                })
                                print(formatted_questions)
                    break
                except Exception as e:
                    print("error while testbook run :" + str(e))
                    logging.info("auth code not working where auth code is : "+ str(auth)) 
                    logging.error(str(e))
            with open ('/root/webScrapping/api_result_json/testbook.json','w') as f:
                json.dump(formatted_questions,f) 
        except Exception as e:
            print(e)
            logging.info("Error in getting data from testbook.com with cookie: "+str(e))
        
    # elif "https://www.dhyeyaias.com" in url:
    #     html_content = requests.get(url).text
    #     soup = BeautifulSoup(html_content, 'html.parser')
    #     question_box_div =  soup.find_all('div', class_='card-body d-inline_children')
    #     for question_box in question_box_div:
    #         question = question_box.find('div', class_='question').text
    #         options = question_box.find_all('div', class_='option')
    #         formatted_options = []
    #         for option in options:
    #             formatted_options.append(option.text)
    #         answer = question_box.find('div', class_='answer').text
    #         solution = question_box.find('div', class_='solution').text
    #         formatted_questions['questions'].append({
    #             'question':question,
    #             'options':formatted_options,
    #             'answer':answer,
    #             'solution':solution
    #         })
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
def getHTMLfromURL(url):
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

    
    logging.info("1")
   
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    
    driver.implicitly_wait(10)
    html = driver.execute_script("return document.documentElement.outerHTML")
    logging.info("2")


    # Get page source after JavaScript execution
    driver.quit()  # Close the browser
    return html


def scrape_website(url,website):
    # Setup Selenium WebDriver

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
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
    options.add_argument('--disable-extensions')  # Disable extensions 

    
    logging.info("1")
   
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    
    driver.implicitly_wait(10)
    html = driver.execute_script("return document.documentElement.outerHTML")
    logging.info("2")

    # print(html)
    # Get page source after JavaScript execution
    driver.quit()  # Close the browser
    if "https://99notes.in/" not in url:
        if "testbook.com" in url:
            html_text = excelRun(str(html),True)
        else:
            html_text = excelRun(str(html))
    else:
        html_text = str(html)
    # html_test = convert_latex(str(html))
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
    logging.info(website)

    if website == "dataCollection":
        specific_string_to_remove = "Practice Now"
        html_text = html_text.replace(specific_string_to_remove, "")
        specific_string_to_remove = "Download as PDF"
        html_text = html_text.replace(specific_string_to_remove, "")
        # Parse the HTML content
        soup = BeautifulSoup(html_text, 'html.parser')
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()
        for style in soup.find_all('style'):
            style.extract()
        for nav in soup.find_all('nav'):
            nav.extract()
        # cleaned_text = ' '.join(soup.stripped_strings)
        # soup = BeautifulSoup(str(cleaned_html), 'html.parser')
        # Find the div with itemprop="articleSection"
        article_section = soup.find('div', itemprop='articleSection')
        
        # Check if the div exists
        if article_section:
            # Remove all script and style tags
            for script_or_style in article_section(['script', 'style']):
                script_or_style.decompose()
            for div in article_section.find_all('div', id ="content_questions"):
                div.decompose()
            for div in article_section.find_all('img'):
                div.decompose()
            for span in article_section.find_all('span', attrs={'fr-original-class': 'fr-inner'}):
                span.decompose()
            # Loop through all elements and remove their attributes
            for tag in article_section.find_all(True):  # True finds all tags
                tag.attrs = {}  # Remove all attributes
            
            # Get the cleaned HTML content as text
            # Remove empty tags
            for tag in article_section.find_all():
                # Strip tag's contents and check if empty
                if not tag.text.strip():
                    tag.decompose()
            clean_content = article_section.prettify()
            logging.info(clean_content)
            return clean_content
        else:
            print("No <div itemprop='articleSection'> found on the page.")
        return ""
    if  website == "edurev":
        try:
            # print(soup)
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
            for parent_span in soup.find_all('span', attrs={"fr-original-class": "fr-img-wrap"}):
                spans = parent_span.find('span', attrs={"fr-original-class": "fr-inner"})
                if spans:
                    spans.decompose()  # Remove the nested span from the HTML
            for parent_div in soup.find_all('div', class_="clearalldoubts"):
                parent_div.decompose()
            
            
            # ads = soup.find_all('div', class_='ER_Model_dnwldapp')
            # for ad in ads:
            #     ad.extract()

            body_content = soup.find('div', class_='contenttextdiv')
            # print(body_content)
            html = str(body_content)
            # Use BeautifulSoup to parse the HTML content
            # print(html)
            return createSeperatorUsingHtml(html)
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
                if tag.name in ['p','img', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6']:
                    # print(tag)
                    if tag.name == 'img' :
                        # print("IMAGE TAGS ",tag)
                        # get data-src attribute in tag if present and then put it in src attribute 
                        if tag.get('data-src'):
                            tag['src'] = tag['data-src']
                            

                        text = str(tag)
                        text_list.append(text)
                    else:
                        text = tag.get_text()
                        
                        if text and text not in processed_texts:
                            # Remove extra spaces using regex
                            text = re.sub(r'\s+', ' ', text)
                            processed_texts.add(text)
                            text = "<"+tag.name+">"+text+"</"+tag.name+">"
                            if tag.name == 'p':
                                # Check if the <p> tag contains only a <strong> tag
                                if len(tag.contents) == 1 and tag.contents[0].name == 'strong':
                                    # Append the strong text as it is
                                    text = str(tag)
                                
                            previous_content_length+=len(text)
                            if (tag.name == 'h2' and previous_content_length > 700):
                                text = "\n ********** \n"+text
                                previous_content_length = 0 
                           
                            elif(tag.name == 'h3' and previous_content_length >1500):
                                text = "\n ********** \n" + text
                                previous_content_length =0 
                                first = False
                            elif(tag.name == 'p' and previous_content_length >2500):
                                text = text+"\n ********** \n"
                                previous_content_length =0 
                                first = False
                            
                            text_list.append(text)
                            if (tag.name == 'h2'):
                                text_list.append("\n ")
                elif tag.name == 'ul' and id(tag) not in processed_uls:
                    # Track the processed <ul> to avoid duplicates
                    processed_uls.add(id(tag))
                    ul_content = []
                    for li in tag.find_all('li'):
                        li_text = li.get_text(strip=True)
                        if li_text not in processed_texts:
                            processed_texts.add(li_text)
                            if 'style' in li.attrs:
                                del li.attrs['style']  # Remove inline styles
                            ul_content.append(str(li))
                    if ul_content:  # Add the <ul> only if it has content
                        ul_html = f"<ul>{''.join(ul_content)}</ul>"
                        if ul_html not in processed_texts:  # Avoid duplicates
                            processed_texts.add(ul_html)
                            previous_content_length += len(ul_html)
                            if previous_content_length > 1500:
                                ul_html = ul_html+"\n ********** \n"
                                previous_content_length = 0
                                first = False
                            text_list.append(ul_html)
                    
                elif tag.name == 'ol' and id(tag) not in processed_uls:
                    # Process <ol> tags similarly to <ul>
                    processed_uls.add(id(tag))
                    ol_content = []
                    for li in tag.find_all('li'):
                        li_text = li.get_text(strip=True)
                        if li_text not in processed_texts:
                            processed_texts.add(li_text)
                            if 'style' in li.attrs:
                                del li.attrs['style']  # Remove inline styles
                            ol_content.append(str(li))
                    if ol_content:  # Add the <ol> only if it has content
                        ol_html = f"<ol>{''.join(ol_content)}</ol>"
                        if ol_html not in processed_texts:  # Avoid duplicates
                            processed_texts.add(ol_html)
                            previous_content_length += len(ol_html)
                            if previous_content_length > 1500:
                                ol_html = ol_html+"\n ********** \n"
                                previous_content_length = 0
                                first = False
                            text_list.append(ol_html)
                    
                # elif tag.name == 'ul':
                #     ul_content = []
                #     for li in tag.find_all('li'):
                #         li_text = li.get_text(strip=True)
                #         if li_text not in processed_texts:
                #             processed_texts.add(li_text)
                #             # remove all inline style from li tag 
                #             if 'style' in li.attrs:
                #                 del li.attrs['style']
                #             ul_content.append(str(li))
                #     if ul_content:  # Only add non-empty <ul>
                #         ul_html = f"<ul>{''.join(ul_content)}</ul>"
                #         previous_content_length += len(ul_html)
                #     if previous_content_length > 1500:
                #         ul_html = ul_html+"\n ********** \n"
                #         previous_content_length = 0
                #         first = False
                #     text_list.append(ul_html)
                # elif tag.name == 'ol':
                #     ul_content = []
                #     for li in tag.find_all('li'):
                #         li_text = li.get_text(strip=True)
                #         if li_text not in processed_texts:
                #             processed_texts.add(li_text)
                #             if 'style' in li.attrs:
                #                 del li.attrs['style']
                #             ul_content.append(str(li))
                #     if ul_content:  # Only add non-empty <ul>
                #         ul_html = f"<ol>{''.join(ul_content)}</ol>"
                #         previous_content_length += len(ul_html)
                #     if previous_content_length > 1500:
                #         ul_html = ul_html+"\n ********** \n"
                #         previous_content_length = 0
                #         first = False
                #     text_list.append(ul_html)
                
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
    elif 'https://99notes.in/' in url :
        output = ""
        
        soup = soup.find('div', class_='entry-content single-content')
        for tag in soup.descendants:
            if tag.name in ['p','ul','img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6','figure']:
                text = tag.get_text()
                if tag.name == 'figure':
                    for child in tag.find_all(True):
                        child.attrs = {}
                    text = str(tag)
                else:
                    text = str(tag)
                output+=text
        
        outputSepJSON = createSepLocal(output)
        # outputSepJSON = json.loads(outputSepJSON)
        res = outputSepJSON['data']
        # outputs = output.split('**********')
        # res =""
        # for out in outputs:
        #     res += getGPTResponse(out,1,1,False)
        return res
    elif "www.drishtiias.com" in url:
            # decompose all fa-star span
            span_elements = soup.find_all('span', class_="fa-star")
            for span in span_elements:
                span.decompose()
            tags_new = soup.find_all('div', class_="tags-new")
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('div', class_ ="border-bg")
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('div', class_ ="social-shares02")
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('div', class_ ="next-post")
            for tag in tags_new:
                tag.decompose()
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            tags_new = soup.find_all('style')
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('ul', class_="actions")
            for tag in tags_new:
                tag.decompose()
            main_content = soup.find('div', class_="article-detail")
            result = ""
            # processed_texts = set()
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            
            return result
    elif "https://www.legacyias.com/" in url:
           
            main_content = soup.find(attrs={"data-elementor-type": "wp-post"})
            processed_texts = set()
            processed_uls = set()  # Track processed 'ul' elements

            first = True
            h2_tags = 0
            count_p = 0
            previous_content_length = 0
            for tag in main_content.descendants:
                if tag.name in ['h2']:
                    h2_tags += 1
            result = ""
            
            for tag in main_content.descendants:
                if tag.name == "img":
                    result += str(tag) + "\n"
                if tag.name in ['p','ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6','figure']:
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
                        elif(tag.name == 'p' and previous_content_length >2500):
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
                        text = "<ul>"+text+"</ul>"
                        processed_uls.add(id(tag))  # Track that this 'ul' has been processed
                        if(tag.name == 'ul' and previous_content_length >1500):
                                text = text+"\n ********** \n"
                                previous_content_length =0 
                                first = False
                        text_list.append(f"{text}")
                elif tag.name == 'li':
                    # Only process 'li' elements if their parent 'ul' hasn't been processed
                    if id(tag.find_parent('ul')) not in processed_uls:
                        text = tag.get_text()
                        if text and text not in processed_texts:
                            text = re.sub(r'\s+', ' ', text)
                            # processed_texts.add(text)
                            previous_content_length+=len(text)
                            processed_uls.add(id(tag))  # Track that this 'ul' has been processed
                            
                            text_list.append(f"<li>{text}</li>")
                # if child.string and child.string.strip() and child.string.strip() not in result:
                #     result += child.string.strip() + "\n"
            
            # return result
                                     
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
            'footerexamswrap',
            'jss3'

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
        return createSeperatorUsingHtml(html)
        # "herechange"
        # Use BeautifulSoup to parse the HTML content
        # with open('/root/webScrapping/test.html', 'w') as file:
        #     file.write(html)
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
            if tag.name in ['p','img','strong', 'h1', 'h2', 'h3', 'span','tr', 'td', 'h4', 'h5', 'h6',  'ul', 'li','ol']:
                if tag.name == 'img' and 'src' in tag.attrs:
                    image_url = tag['src']
                    
                    text = str(tag)
                    # text_list.append(text)
                    text_list.append(text)
                else:
                    text = tag.get_text()
                    # if tag.name == "h4":
                    #     logging.info("H4 TAGS : "+text)
                    #     print("IsProcessed : ",text in processed_texts)
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
    try:

        for text in text_list:
            soup = BeautifulSoup(text, "html.parser")
        
            # Iterate through all tags in the parsed HTML
            for tag in soup.find_all(True):  # `True` finds all tags
                if (tag.name == 'li' or tag.name == 'strong' or tag.name == 'ul' or tag.name == 'ol')  and 'style' in tag.attrs:
                    del tag.attrs['style']  # Remove style attribute for non-span tags
            result += str(soup)
    except Exception as e:
        print(str(e))
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
    # logging.info("Sending /Scrape Response : ======> "+output)
    return output
    
    # except Exception as e:
    #     print(e)
def createSeperatorUsingHtml(data):
    data = data.replace('+', '__PLUS__')
    data = data.replace("<h7", "<h2")
    data = data.replace("</h7", "</h2")
    data = data.replace("<h8", "<h3")
    data = data.replace("</h8", "</h3")
    soup = BeautifulSoup(data, 'html.parser')
    startingText = []
    endingText = []
    allBrTags = soup.find_all('br')
    for brTag in allBrTags:
        brTag.replace_with(" ")
    for tag in soup.find_all(True):  # True fetches all tags
        if 'style' in tag.attrs:  # Check if the tag has a 'style' attribute
            if tag.name not in ['span', 'img']:  # Exclude 'span' and 'img' tags
                del tag.attrs['style']  # Remove the 'style' attribute
    for tag in soup.find_all(class_ ="span"):  # True fetches all tags
        if(tag.get('class') and 'fr-inner' in tag.get('class')):
            continue
        #if tag class is fr-new then add as it is 
        if tag.get('class') and ('fr-img-caption' in tag.get('class') or 'fr-video' in tag.get('class')):
            if 'style' in tag.attrs:  # Check if the tag has a 'style' attribute
                style_content = tag['style']
                # Split the style into individual properties
                style_properties = [prop.strip() for prop in style_content.split(';') if prop.strip()]
                
                # Filter the properties to keep only display and cursor
                filtered_styles = [
                    prop for prop in style_properties 
                    if prop.startswith('display:') or prop.startswith('cursor:') or  prop.startswith('line-height') or prop.startswith('font-size') or prop.startswith('color') or prop.startswith('text-align') or prop.startswith('margin') or  # Matches margin, margin-right, etc.
                    prop.startswith('padding') or  # Matches padding, padding-top, etc.
                    prop.startswith('height:') or
                    prop.startswith('width:')
                ]
                
                # Reassemble the style string and set it back
                if filtered_styles:
                    tag['style'] = '; '.join(filtered_styles)
                else:
                    del tag['style']  # Remove style if nothing remains
                
    endingText =[]
    startingText = []
    processed_texts = set()
    previous_content_length = 0
    first = True
    output = ""
    startingTag = True
    endingTag = False
    
    processed_uls = set()  
    ul_content= []
    text_list = []
    processed_img_urls = set()
    rawText = ""
    processed_texts = set()
    processed_uls = set()  # Track processed 'ul' elements

    first = True
    h2_tags = 0
    count_p = 0
    previous_content_length = 0
    for tag in soup.descendants:
        if tag.name in ['h2']:
            h2_tags += 1
    try:

        if soup.find_all('div') or soup.find_all("p"):
            for tag in soup.descendants:
                if tag.name in ['p', 'img','strong', 'span', 'h1', 'h2', 'h3','table', 'h4', 'h5', 'h6','h7','h8']:
                    
                    if tag.name == 'table':
                    # Remove inline CSS and attributes from the table and its descendants
                        tag.attrs = {}
                        for element in tag.find_all(True):  # True fetches all child tags
                            if 'style' in element.attrs:
                                del element.attrs['style']  # Remove inline CSS
                            # Optionally remove other attributes if needed
                            element.attrs = {key: value for key, value in element.attrs.items() if key != 'style'}
                        
                        # Get the updated full HTML of the table
                        table_html = str(tag)
                        previous_content_length += len(table_html)
                        text_list.append(table_html)  # Add the cleaned table HTML to the text list
                        processed_texts.add(table_html)
                        # Skip processing further descendants of this table
                        continue
                    if tag.name == 'p' :
                        # Check if the <p> tag contains only a <strong> tag
                        text = str(tag)
                        if '<h2' in text or '<h3' in text or '<h7' in text or '<h8' in text:
                            continue
                        if 'fr-img-caption' in text or 'fr-video' in text:
                            continue
                        span_elements = tag.find_all('span', recursive=False)
                        
                        # Check if there is exactly one <span> inside the <p> tag
                        if len(span_elements) == 1:
                            span = span_elements[0]
                            
                            # Check if the <span> contains an <img> tag
                            if span.find('img') and 'edurev.gumlet.io/ApplicationImages/Temp' in span.find('img').get('src'):
                                continue

                        
                    if tag.name == 'span':
                        if(tag.get('class') and 'fr-inner' in tag.get('class')):
                            continue
                        #if tag class is fr-new then add as it is 
                        if tag.get('class') and ('fr-img-caption' in tag.get('class') or 'fr-video' in tag.get('class')):
                            text = str(tag)
                            text_list.append(text)
                            previous_content_length += len(text)
                            processed_texts.add(text)
                            for img_tag in tag.find_all('img'):
                                img_text = str(img_tag)
                                processed_texts.add(img_text)
                                processed_img_urls.add(img_tag['src'])
                            # tag.extract()
                            continue
                        else:
                            img = tag.find('img')
                            img_url = img.get('src') if img else None
                            if img and img_url not in processed_img_urls:
                                if 'edurev.gumlet.io/ApplicationImages/Temp' in img['src']:
                                    text = str(tag)
                                    text_list.append(text)
                                    previous_content_length += len(text)
                                    processed_texts.add(text)
                                    for img_tag in tag.find_all('img'):
                                        img_text = str(img_tag)
                                        processed_texts.add(img_text)
                                        processed_img_urls.add(img_tag['src'])
                                    # tag.extract()
                                    continue
                        
                    elif tag.name == 'img':
                        if str(tag) not in processed_texts:
                            text = str(tag)
                            processed_texts.add(text)
                            text_list.append(text)

                    else:
                        if tag.name == 'p':
                            strong_tags = tag.find_all('strong')
                            if len(strong_tags) == 1 and tag.get_text(strip=True) == strong_tags[0].get_text(strip=True):
                                text = str(tag)
                                # tag.extract()
                            else:
                                text = tag.get_text()
                        else:
                            text = tag.get_text()
                        if text and (checkExisting(text, processed_texts) or  text == 'Ans.' ) == False:
                            text = re.sub(r'\s+', ' ', text)  # Clean up extra spaces
                            processed_texts.add(text)
                            rawText = text  # Save the raw text before HTML wrapping
                            text = "<" + tag.name + ">" + text + "</" + tag.name + ">"  # Wrap in HTML tag

                            # Update content length tracker
                            previous_content_length += len(text)

                            # Insert `**********` based on content length and tag type
                            if (tag.name == 'h2' or tag.name == "h3" or tag.name == 'h7' or tag.name == 'h8' ) and previous_content_length > 500:
                                text = str(tag)
                                if endingTag:  # If endingTag is True, store in endingText
                                    endingText.append(rawText)
                                startingTag = True
                                endingTag = False  # This block marks the transition
                                next_tag = tag.find_next()  # Find the next sibling
                                if next_tag and next_tag.name == 'p':
                                    span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                    if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                        question_text = next_tag.get_text(strip=True)
                                        text += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                        processed_texts.add(question_text)
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                text = "\n ********** \n" + text
                                previous_content_length = 0

                            elif tag.name == 'p' and previous_content_length > 5000:
                                if endingTag:  # If endingTag is True, store in endingText
                                    endingText.append(rawText)
                                startingTag = True
                                endingTag = False  # This block marks the transition
                                next_tag = tag.find_next()  # Find the next sibling
                                while next_tag:
                                    if next_tag.name == 'strong':  # If the next tag is <strong>, check the next sibling
                                        next_tag_ = next_tag.find_next()
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                        next_tag = next_tag_
                                    elif next_tag.name == 'p':  # If the next tag is <p>, check for the question text
                                        span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                        if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                            question_text = next_tag.get_text(strip=True)
                                            text += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                            processed_texts.add(question_text)
                                            next_tag.extract()  # Remove the <p> tag from the soup
                                            break
                                        else:
                                            next_tag = next_tag.find_next()
                                    else:
                                        break
                                        # next_tag = next_tag.find_next()
                                    
                                text += "\n ********** \n"
                                previous_content_length = 0
                                first = False

                            # If it's a starting tag, add to `startingText`
                            if startingTag:
                                if not endingTag:
                                    startingText.append(rawText)
                                    endingTag = True  # Set endingTag to True
                                    startingTag = False  # Reset startingTag

                            text_list.append(text)
                        elif text and (text == 'Ans.' ) == True:
                            text = re.sub(r'\s+', ' ', text)
                            processed_texts.add(text)
                            rawText = text  # Save the raw text before HTML wrapping
                            text = "<" + tag.name + ">" + text + "</" + tag.name + ">"  # Wrap in HTML tag

                            # Update content length tracker
                            previous_content_length += len(text)

                            # Insert `**********` based on content length and tag type
                            if (tag.name == 'h2' or tag.name == "h3" or tag.name == 'h7' or tag.name == 'h8'  ) and previous_content_length > 500:
                                if endingTag:  # If endingTag is True, store in endingText
                                    endingText.append(rawText)
                                startingTag = True
                                endingTag = False  # This block marks the transition
                                next_tag = tag.find_next()  # Find the next sibling

                                if next_tag and next_tag.name == 'p':
                                    span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                    if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                        question_text = next_tag.get_text(strip=True)
                                        text += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                        processed_texts.add(question_text)
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                text = "\n ********** \n" + text
                                previous_content_length = 0

                            elif tag.name == 'p' and previous_content_length > 5000:
                                if endingTag:  # If endingTag is True, store in endingText
                                    endingText.append(rawText)
                                startingTag = True
                                endingTag = False  # This block marks the transition
                                next_tag = tag.find_next()  # Find the next sibling
                                while next_tag:
                                    if next_tag.name == 'strong':  # If the next tag is <strong>, check the next sibling
                                        next_tag_ = next_tag.find_next()
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                        next_tag = next_tag_
                                    elif next_tag.name == 'p':  # If the next tag is <p>, check for the question text
                                        span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                        if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                            question_text = next_tag.get_text(strip=True)
                                            text += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                            processed_texts.add(question_text)
                                            next_tag.extract()  # Remove the <p> tag from the soup
                                            break  
                                        else:
                                            next_tag = next_tag.find_next()
                                    else:
                                        break
                                    
                                    
                                text = text + "\n ********** \n"
                                previous_content_length = 0
                                first = False

                            # If it's a starting tag, add to `startingText`
                            if startingTag:
                                if not endingTag:
                                    startingText.append(rawText)
                                    endingTag = True  # Set endingTag to True
                                    startingTag = False  # Reset startingTag

                            text_list.append(text)
                        else:
                            processed_texts.add(str(tag))  # Mark the tag as processed

                        # Add delimiter for specific tags
                        if tag.name == 'h2' or tag.name == "h3":
                            text_list.append("\n ")
                elif tag.name == 'ol' and id(tag) not in processed_uls:
                    # Process <ol> tags similarly to <ul>
                    processed_uls.add(id(tag))
                    ol_content = []
                    for li in tag.find_all('li'):
                        li_text = li.get_text(strip=True)
                        if li_text not in processed_texts:
                            processed_texts.add(li_text)
                            if 'style' in li.attrs:
                                del li.attrs['style']  # Remove inline styles
                            ol_content.append(str(li))
                            li.extract()
                    if ol_content:  # Add the <ol> only if it has content
                        ol_html = f"<ol>{''.join(ol_content)}</ol>"
                        if ol_html not in processed_texts:  # Avoid duplicates
                            processed_texts.add(ol_html)
                            previous_content_length += len(ol_html)
                            if previous_content_length > 5000:
                                next_tag = tag.find_next()  # Find the next sibling
                                if next_tag and next_tag.name == 'p':
                                    span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                    if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                        question_text = next_tag.get_text(strip=True)
                                        ol_html += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                        processed_texts.add(question_text)
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                                                        # Check for <span> or <img> tags
                                    span_or_img = next_tag.find(lambda t: 
                                                                    (t.name == 'span' and 
                                                                    t.get('class') and 
                                                                    ('fr-img-caption' in t.get('class'))) or 
                                                                    t.name == 'img')  # Check for <span> or <img>
                                    if span_or_img:
                                        if span_or_img.name == 'span':  # Handle <span> tags
                                            span_text = str(span_or_img)
                                            ol_html += f"\n{span_text}"  # Append the <span> content
                                            processed_texts.add(span_text)
                                        elif span_or_img.name == 'img':  # Handle <img> tags
                                            img_text = str(span_or_img)
                                            ol_html += f"\n{img_text}"  # Append the <img> content
                                            processed_texts.add(img_text)
                                        next_tag.extract()  # Remove the tag from the soup
                                                
                                ol_html = ol_html+"\n ********** \n"
                                previous_content_length = 0
                                first = False
                                startingTag = True
                                endingTag = False  
                            text_list.append(ol_html)
                            
                    if startingTag:
                        if not endingTag:
                            startingText.append(rawText)
                            endingTag = True  # Set endingTag to True
                            startingTag = False  # Reset startingTag
                elif tag.name == 'ul' and id(tag) not in processed_uls:
                        # Track the processed <ul> to avoid duplicates
                        processed_uls.add(id(tag))
                        ul_content = []
                        for li in tag.find_all('li'):
                            li_text = li.get_text(strip=True)
                            if li_text not in processed_texts:
                                processed_texts.add(li_text)
                                if 'style' in li.attrs:
                                    del li.attrs['style']  # Remove inline styles
                                
                                ul_content.append(str(li))
                                li.extract()

                        if ul_content:  # Add the <ul> only if it has content
                            ul_html = f"<ul>{''.join(ul_content)}</ul>"
                            if ul_html not in processed_texts:  # Avoid duplicates
                                processed_texts.add(ul_html)
                                previous_content_length += len(ul_html)
                                if previous_content_length > 5000:
                                    next_tag = tag.find_next()  # Find the next sibling
                                    if next_tag and next_tag.name == 'p':
                                        span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                        if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                            question_text = next_tag.get_text(strip=True)
                                            ul_html += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                            processed_texts.add(question_text)
                                            next_tag.extract()  # Remove the <p> tag from the soup
                                        # Check for <span> or <img> tags
                                        span_or_img = next_tag.find(lambda t: 
                                                                    (t.name == 'span' and 
                                                                    t.get('class') and 
                                                                    ('fr-img-caption' in t.get('class'))) or 
                                                                    t.name == 'img')  # Check for <span> or <img>
                                        if span_or_img:
                                            if span_or_img.name == 'span':  # Handle <span> tags
                                                span_text = str(span_or_img)
                                                ul_html += f"\n{span_text}"  # Append the <span> content
                                                processed_texts.add(span_text)
                                            elif span_or_img.name == 'img':  # Handle <img> tags
                                                img_text = str(span_or_img)
                                                ul_html += f"\n{img_text}"  # Append the <img> content
                                                processed_texts.add(img_text)
                                            next_tag.extract()  # Remove the tag from the soup
                                                
                                        
                                    ul_html = ul_html+"\n ********** \n"
                                    previous_content_length = 0
                                    first = False
                                    startingTag = True
                                    endingTag = False  
                                text_list.append(ul_html)
                        if startingTag:
                            if not endingTag:
                                startingText.append(rawText)
                                endingTag = True  # Set endingTag to True
                                startingTag = False  # Reset startingTag
            result = ""
            for text in text_list:
                result += text + '\n'
            # replace any double space from the result using regex
            # result = re.sub(r'\s+', ' ', result).strip()
            
            # print(result)
            result = re.sub(r'\n+', '', result)
            result_in_parts = result.split("**********")
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
        else:
            # this case is when the text only contains text we need to add separator after 1500 characters plus a fullstop 
            max_length = 1500
            text = data
            while len(text) > max_length:
                # Find the position of the next full stop after max_length
                end_pos = text[max_length:].find('.')
                
                if end_pos != -1:
                    # Adjust end_pos to be the position in the original text
                    end_pos += max_length + 1
                else:
                    # If no full stop is found, look for the next space
                    end_pos = text[max_length:].find(' ')
                    if end_pos != -1:
                        end_pos += max_length
                    else:
                        # If no space is found, set to max_length
                        end_pos = max_length

                output += text[:end_pos] + "**********"
                text = text[end_pos:]
                
            output += text
    except Exception as e:
        print(str(e))
        output = ""
    # logging.info("INFO :::::::::::::::::::::::: BEFORE OUTPUT Tag: " + output)

    output = output.replace('__PLUS__', '+')
    logging.info("INFO :::::::::::::::::::::::: OUTPUT Tag: " + output)
    output = output.replace("<h7>", "<h2>")
    output = output.replace("</h7>", "</h2>")
    output = output.replace("<h8>", "<h3>")
    output = output.replace("</h8>", "</h3>")
    # print(output)
    return output
def scrapeExcel(text, quizrr = False):
    # Setup Selenium WebDriver
    # latex to image 
    html_text = excelRun(text,quizrr)
  
    return html_text
def mathTexToImg(text):
    # Setup Selenium WebDriver
    # latex to image 
    html_text = mathTexToImgFun(text)
  
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
        if "touchpoint" in data:
            website = data.get('touchpoint')
        if "geeksforgeeks.org" in url:
            # geeksforgeeks = True
            website = "geeksforgeeks"
        output_text = scrape_website(url,website)
        print(output_text)
        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error: "+str(e)}), 500

@app.route('/collect/data', methods=['POST'])
def collect_data():
    data = request.json
    input_value = data.get('input')
    prompt_value = data.get('prompt')
    if prompt_value == "":
        prompt_value = ""   
    output_value = data.get('output')

    # Define the CSV file path
    file_path = "/root/webScrapping/dataSet.csv"

    # Check if the file exists
    file_exists = os.path.isfile(file_path)
    try:
        # Open the CSV file in append mode
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # If the file does not exist, write the header first
            if not file_exists:
                writer.writerow(["Input","Prompt", "Output"])
            
            # Write the data
            writer.writerow([input_value,prompt_value, output_value])
        
        return jsonify({"message": "Data saved successfully!"})
    except Exception as e:
        print(str(e))
        return jsonify({"message": "some error occured: " +str(e)}), 500

def sendQuestionsToP1( quizId, quizGuid, formatted_questions, marks, negMarks):
    api_to_send_questions = "https://er.edurev.in/Tools/PDF_TO_QuizQuestions_Automation"
    logging.info("INFO : sending questions to this api : " + api_to_send_questions)
    res = {
            "quizId": quizId,
            "quizGuid": quizGuid,
            "api_token" : "45b22444-3023-42a0-9eb4-ac94c22b15c2",
            "result": formatted_questions,
            "marks":marks,
            "negMarks": negMarks
        }
    response = requests.post(api_to_send_questions, json=res)
    return response
@app.route('/csvToTest', methods=['POST'])
def csvToTest():
    file = request.files['xl_file']
    quizId = ""
    quizGuid = ""
    if "quizId" in request.form:
        quizId = request.form['quizId']
        quizGuid = request.form['quizGuid']
    marks = "4"
    negMarks = "1"
    df = pd.read_csv(file)
    result = {
        'questions':[]
        }
    for index, row in df.iterrows():
        formatted_questions = {
        'questions':[]
        }
        quizId = row.get('QID')
        quizGuid = row.get('GUID')
        question = row.get('Statement', 'No question provided')
        optionA = row.get('Option A', 'No optionA provided')
        optionB = row.get('Option B', 'No optionB provided')
        optionC = row.get('Option C', 'No optionC provided')
        optionD = row.get('Option D', 'No optionD provided')
        answer = row.get('Answer', 'No answer provided')
        sol = row.get('Explanation', 'No solution provided')
        # print("*********************** question**********************************")
        # print(question)
        # print("*********************** question ends**********************************")
        question = str(question)
        optionA = str(optionA)
        optionB = str(optionB)
        optionC = str(optionC)
        optionD = str(optionD)
        answer = str(answer)
        sol = str(sol)
        

        question_ = question.replace("$#$",",")
        optionA_ = optionA.replace("$#$",",")
        optionB_ = optionB.replace("$#$",",")
        optionC_ = optionC.replace("$#$",",")
        optionD_ = optionD.replace("$#$",",")
        answer_ = answer.replace("$#$",",")
        sol_ = sol.replace("$#$",",")   
        if sol_ == "" or sol_ == "nan":
            continue     
        question_ = scrapeExcel(question_,True)    
        optionA_ = scrapeExcel(optionA_,True)
        optionB_ = scrapeExcel(optionB_,True)
        optionC_ = scrapeExcel(optionC_,True)
        optionD_ = scrapeExcel(optionD_,True)
        answer_ = scrapeExcel(answer_,True)
        sol_ = scrapeExcel(sol_,True)
        question_ = question_.replace("<br><br>","<br>")
        question_ = question_.replace("<br/><br/>","<br/>")
        sol_ = sol_.replace("<br><br>","<br>")
        sol_ = sol_.replace("<br/><br/>","<br/>")
        
        formatted_questions["questions"].append({"question":question_, "options":[optionA_,optionB_,optionC_,optionD_], "answer":answer_, "solution":sol_})
        result["questions"].append({"question":question_, "options":[optionA_,optionB_,optionC_,optionD_], "answer":answer_, "solution":sol_})
        response = sendQuestionsToP1(quizId, quizGuid, formatted_questions, marks, negMarks)
        
        # res = {
        #     "quizId": quizId,
        #     "quizGuid": quizGuid,
        #     "api_token" : "45b22444-3023-42a0-9eb4-ac94c22b15c2",
        #     "result": formatted_questions
        #     "marks":marks,
        #     "negMarks": negMarks
        # }
        # response = requests.post(api_to_send_questions, json=res)
        if response.status_code == 200:
            print(f"Successfully sent question {index + 1}")
    with open("/root/webScrapping/api_result_json/csvToTest.json", "w") as f:
        json.dump(result, f)
    return "XL file received and processed successfully"
    

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
    language = data.get("language")
    marks = ""
    negMarks = ""
    startRange = 0
    endRange = 0
    testName = ""
    if "marks" in data:
        marks = data.get("marks")
    if "negMarks" in data:
        negMarks = data.get("negMarks")
    logging.info("INFO : TEST SCROLLER quizId: " + quizId)
    logging.info("INFO : TEST SCROLLER quizGuid: " + quizGuid)
    logging.info("INFO : TEST SCROLLER url: " + url)

    if not url:
        return jsonify({'error': 'text is required'}), 400
    testCat= ""
    if "www.smartkeeda.com" in url:
        print(data)
        if "startRange" in data:
            startRange = data.get("startRange")
        if 'endRange' in data:
            endRange = data.get("endRange")
        if 'testName' in data:
            testName = data.get("testName")
        if 'testCat' in data:
            testCat = data.get('testCat')

    # try:
    all_questions = getScrollerTest(url,language,startRange,endRange,testName,testCat)
    # return all_questions

    send_question = sendQuestionsToP1(quizId, quizGuid, all_questions, marks, negMarks)
    # api_to_send_questions = "https://er.edurev.in/Tools/PDF_TO_QuizQuestions_Automation"

    res = {
        "quizId": quizId,
        "quizGuid": quizGuid,
        "api_token" : "45b22444-3023-42a0-9eb4-ac94c22b15c2",
        "result": all_questions,
        "marks":marks,
        "negMarks": negMarks
    }
    # logging.info("INFO : TEST SCROLLER Sending Result to API : " + api_to_send_questions)
    logging.info(res)
        # output_text = scrapeExcel(text)
    # send_question = requests.post(api_to_send_questions, json=res)
    if send_question.status_code == 200:
        print("Question sent successfully!")
        logging.info("***********************************Question sent successfully!***********************************")
    else:
        print("Internal Server Error")
        logging.error("***********************************Internal Server Error with code *********************************** " + str(send_question.status_code))


    return jsonify(res), 200
# url = "https://www.mockers.in/test-solution1/test-575422"


@app.route('/excel/scrapper', methods=['POST'])
def excelScrapper():
    data = request.json
    text = data.get('url')
    
    url = ""
    if 'sourceBaseURL' in data:
        url = data.get('sourceBaseURL')
    # url = "view-source:"+url
    # print(text)
    logging.info("INFO : EXCEL SCRAPPER text URL: " + url)
    quizrr = False
    if "app.quizrr.in" in url:
        quizrr = True
    if not text:
        return jsonify({'error': 'Text is required'}), 400

    try:
        output_text = scrapeExcel(text,quizrr)
        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error Happend at Excel Scrapper "}), 500
def url_to_base64(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()  # Check if the request was successful
    return b64encode(response.content).decode("utf-8")


@app.route('/image/scrapper', methods=['POST'])
def imageScrapper():
    data = request.json
    logging.info("INFO : Image Base 64 SCRAPPER data: " + str(data))
    img_url = data.get('url')
    logging.info("INFO : Image Base 64 SCRAPPER text URL: " + img_url)
    quizrr = False
    
    try:
        output_img_bs64 = url_to_base64(img_url)
        logging.info("INFO : Image Base 64 SCRAPPER data response : " + str(output_img_bs64))
        return jsonify({'content': output_img_bs64}), 200
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
    print(len(div_elements))
    
    for i, div in enumerate(div_elements):
        if i == len(div_elements) - 1:
            break
        for child in div.descendants:
            
            if child.name == "img":
                all_data += str(child) + "\n"
            if child.string and child.string.strip() and child.string.strip() not in all_data:
                all_data += child.string.strip() + "\n"
        all_data+="**********"+"\n"
    logging.info("Data Scraped from IASBABA: \n"+str(all_data))
    # print(all_data)
    # with open("iasbaba.txt", "w") as f:
    #     f.write(all_data)
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
            if "Article" in soup.find('div', class_='box-header').find("h3").text or "Current Affairs" in soup.find('div', class_='box-header').find("h3").text:
                date_element = soup.find('small')
                date_text = date_element.text.strip()
                # print(date_text)
                if "hour ago" not in str(date_text) and "hours ago" not in str(date_text) and "days ago" not in date_text and "day ago" not in date_text:
                    # formats = ["%B %d, %Y", "%d %B %Y", "%d %B, %Y", "%d %b %Y"]
                    formats = ["%B %d, %Y", "%d %B %Y", "%d %B, %Y", "%d %b %Y", "%b. %d, %Y"]

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
                    elif date_obj.strftime("%B %d, %Y") == today_date:
                        result+= get_data_vija(soup)
                

        except Exception as e:
            print("error: "+str(e))
            
    return result
       
def scrape_website_current_affair(url):
    try:
        # Setup Selenium WebDriver
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
        if "https://www.gktoday.in/" in url:
            try:
                div_elements = soup.find('div', class_="inside_post")
                for style_tag in div_elements.find_all('style'):
                    style_tag.decompose()

                removeDivs = div_elements.find_all('blockquote')
                for div in removeDivs:
                    div.decompose()
                removeDivs = div_elements.find_all('script')
                for div in removeDivs:
                    div.decompose()
                removePs = div_elements.find_all('p',class_ = "small-font")
                for p in removePs:
                    p.decompose()
                removeDiv = div_elements.find('div', id="relatedposts")
                removeDiv.decompose()
                removeDiv = div_elements.find('div', id="comments")
                removeDiv.decompose()
                removeDivs = div_elements.find_all('div', class_="google-auto-placed")
                for div in removeDivs:
                    div.decompose()
                removeDiv = div_elements.find('div', class_="prenext")
                removeDiv.decompose()
                removeDiv = div_elements.find('div', class_="sharethis-inline-share-buttons")
                removeDiv.decompose()
                result = ""
                for child in div_elements.descendants:
                    if child.string and child.string.strip() and child.string.strip() not in result:
                        result += child.string.strip() + "\n"
                return result.strip()
            except Exception as e:
                logging.info("Error in gk today current affairs : "+str(e))
        elif "https://ensureias.com" in url:
            try:
                div_elements = soup.find_all('div', class_="v-card")
                removeDiv = div_elements.find('div',class_= "v-card__loader")
                removeDiv.decompose()
                result = ""
                for div in div_elements:
                    for child in div.descendants:
                        if child.string and child.string.strip() and child.string.strip() not in result:
                            result += child.string.strip() + "\n"
                    result+="**********"+"\n"
                return result.strip()
            except Exception as e:
                logging.info("Error in ensureias current affairs : "+str(e))

        elif url == "https://iasbaba.com/current-affairs-for-ias-upsc-exams/":
            try:
                print("entered")
                today_date = datetime.datetime.now()  # Format like '22 May 2024'
                formatted_date = f"{get_ordinal(today_date.day)} {today_date.strftime('%B %Y')}"  # Format like '22nd May 2024'
                # Find the link for today's date
                ul_elements = soup.find_all('ul', class_='lcp_catlist')
                result = ""
                # print(ul_elements)
                for ul_element in ul_elements:
                    li_elements = ul_element.find_all('li')
                    for li in li_elements:
                        a_element = li.find('a')
                        # print(formatted_date, a_element.text)
                        if a_element and formatted_date in a_element.text:
                            logging.info("INFO : Found today's date in IAS BABA website")
                            logging.info(f"{formatted_date}: {a_element.text}")

                            # logging.info(formatted_date, a_element.text)
                            result += scrape_website_iasbaba(a_element['href'])
                return result
            except Exception as e:
                logging.info("Error in IAS BABA current affairs : "+str(e))
            
        elif "www.drishtiias.com" in url:
            # decompose all fa-star span
            span_elements = soup.find_all('span', class_="fa-star")
            for span in span_elements:
                span.decompose()
            tags_new = soup.find_all('div', class_="tags-new")
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('div', class_ ="border-bg")
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('div', class_ ="social-shares02")
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('div', class_ ="next-post")
            for tag in tags_new:
                tag.decompose()
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            tags_new = soup.find_all('style')
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('ul', class_="actions")
            for tag in tags_new:
                tag.decompose()
            main_content = soup.find('div', class_="article-detail")
            result = ""
            # processed_texts = set()
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            
            return result
        elif url == "https://www.civilsdaily.com/":
            try:
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
                logging.info("Data Scraped from Civils Daily: \n"+str(result))
                return result
            except Exception as e:
                logging.info("Error in civils daily current affairs : "+str(e))
        elif "www.civilsdaily.com" in url:
            result += scrape_website_civilDaily(url)
            return result
        elif "iasbaba.com" in url:
            result+=scrape_website_iasbaba(url)
            return result
        elif "iasgyan.in" in url:
            
            tags_new = soup.find_all('div', class_ ="content-btn")
            for tag in tags_new:
                tag.decompose()
            
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            tags_new = soup.find_all('style')
            for tag in tags_new:
                tag.decompose()
            
            main_content = soup.find('div', class_="article_descr")
            result = ""
            # processed_texts = set()
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            
            return result
        elif "vajiramias.com" in url:
            
            
            
            main_content = soup.find('div', class_=" padding-10")
            result = ""
            # processed_texts = set()
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            
            return result

        elif "https://visionias.in/" in url:
            tags_new = soup.find_all('style')
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('script')
            for tag in tags_new:
                tag.decompose()
            main_content = soup.find('div', class_="flex flex-col w-full mt-10 lg:mt-0")
            result = ""
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            return result
        elif "dce.visionias.in" in url:
        
            tags_new = soup.find_all('div', class_ ="flex justify-between items-center mb-10")
            for tag in tags_new:
                tag.decompose()
            
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            tags_new = soup.find_all('style')
            for tag in tags_new:
                tag.decompose()
            
            main_content = soup.find('div', class_="flex flex-col w-full mt-6 lg:mt-0")
            result = ""
            # processed_texts = set()
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            
            return result
        elif "pwonlyias.com" in url:
            tags_new = soup.find_all('div', class_ ="vc_print_text")
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('div', class_ ="ftwp-in-post ftwp-float-none")
            for tag in tags_new:
                tag.decompose()
            
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            tags_new = soup.find_all('style')
            for tag in tags_new:
                tag.decompose()
            
            main_content = soup.find('div', class_="desc my-4")
            result = ""
            # processed_texts = set()
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            
            return result
        elif "www.legacyias.com" in url:
            tags_new = soup.find_all('div', class_ ="elementor-column elementor-col-33 elementor-inner-column elementor-element elementor-element-54e13bc")
            for tag in tags_new:
                tag.decompose()
            
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            tags_new = soup.find_all('style')
            for tag in tags_new:
                tag.decompose()
            
            main_content = soup.find('div', class_="elementor-column elementor-col-66 elementor-top-column elementor-element elementor-element-2bc9084")
            result = ""
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            
            return result
        elif "theiashub.com" in url:
            tags_new = soup.find_all('div', class_ ="download-div")
            for tag in tags_new:
                tag.decompose()
            tags_new = soup.find_all('img', class_ ="mob_hei")
            for tag in tags_new:
                tag.decompose()
            
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            tags_new = soup.find_all('style')
            for tag in tags_new:
                tag.decompose()
            
            main_content = soup.find('div', class_="mt-1 p-3")
            result = ""
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            
            return result
        elif "vajiramandravi.com" in url:
            tags_new = soup.find_all('div', class_ ="print-no download-and-share")
            for tag in tags_new:
                tag.decompose()
            # remove all a tag with target argument as _blank
            tags_new = soup.find_all('a', target="_blank")
            for tag in tags_new:
                tag.decompose()
            
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            tags_new = soup.find_all('style')
            for tag in tags_new:
                tag.decompose()
            
            main_content = soup.find('div', class_="article-content")
            result = ""
            for child in main_content.descendants:
                if child.name == "img":
                    result += str(child) + "\n"
                if child.string and child.string.strip() and child.string.strip() not in result:
                    result += child.string.strip() + "\n"
            
            return result
        return ""  
    except Exception as e:
        logging.info(str(e))
        return ""
    

def get_right_answer(data):
    try:
        # gpt_model = ""
        # if pairs:
        #     gpt_model = "gpt-4o"
        # else:
        #     gpt_model = "gpt-4o"
            # gpt_model = "gpt-3.5-turbo"

        result_test = {"questions": []}
        print("Type of data_test for right answer: " +  str(type(data)))
        # logging.info("Type of data_test for right answer:", type(data))
        if type(data) == str:
            data = json.loads(data)
            print('converted to json')                    
            

        print("Content of data_test for right answer: " + str(data))
        # logging.info("Content of data_test for right answer:", data)
        if isinstance(data, dict) and 'questions' in data:
            for question in data['questions']:
                # print(question)
                result_test['questions'].append(question)
        else:
            result_test['questions'].append(data)
        for question in result_test['questions']:
            option_text = ""
            solution_text =""
            solution_text = question['solution']
            for option in question['options']:
                 option_text += option + "\n"
            query = f'''
            "solution": {solution_text} \n
            "options": {option_text}'''

            current_date = datetime.datetime.now()
            # Format the date as a string in a specific format
            formatted_date = current_date.strftime("%Y-%m-%d")
            prompt = '''
            You are tasked with reading a given solution to a problem and determining the correct answer based on that solution. Your response should be concise, only stating the correct option among 'Option A', 'Option B', 'Option C', or 'Option D'. Ensure that the answer is derived directly from the provided solution without adding any additional information or explanation. give only 'Option A', 'Option B', 'Option C', or 'Option D' and never give full option in the result. 
            '''
            user_prompt = {
                "Role": "You are an expert exam solution verifier, specializing in reading and interpreting provided solutions to determine the correct multiple-choice answer. Your primary role involves carefully analyzing the given solution and selecting the correct option (Option A, Option B, Option C, or Option D) based solely on the information presented. Your expertise lies in ensuring accuracy and precision, making sure that the chosen option perfectly aligns with the solution provided. You excel in providing clear, unambiguous answers and play a crucial role in maintaining the integrity and reliability of the assessment process. Your goal is to assist educators and learners by offering accurate and dependable answer verification. Always ensure that the answer directly corresponds with the given solution without adding any extra information or interpretation",
                "objective": query + "\n" + prompt
            }
            logging.info("User Prompt for right answer:" + str(user_prompt))
            response_ans = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are ChatGPT, a large language model trained by OpenAI, based on the GPT-3.5/GPT-4o architecture. Knowledge cutoff: 2021-09 Current date: "+formatted_date
                    },
                    {
                        "role": "user",
                        "content": json.dumps(user_prompt)
                    }
                ],
                max_tokens=4096,
                temperature=0.7
            )

            # Print the response
            

            if response_ans.choices:
                # Access the content from the response
                data_res_ans = response_ans.choices[0].message.content
                data_res_ans = str(data_res_ans)
                if ":" in data_res_ans:

                    data_res_ans = data_res_ans.split(":")[0]
                    logging.info("found : in opton so now the result is : "+ str(data_res_ans))
                if "=" in data_res_ans:
                    data_res_ans = data_res_ans.split("=")[0]
                    logging.info("found = in opton so now the result is : "+ str(data_res_ans))

                logging.info("Response for right answer: "+ str(data_res_ans))
                
                question['answer'] = data_res_ans
                logging.info("In result_test JSON for right answer: " + str(question['answer']))
        return result_test
    except Exception as e:
        print("Error:", str(e))
        logging.info("Error in getting right answer: "+ str(e))     
def getGPTResponse(prompt,i,no_of_para,weeklyCA = False,daily = False):
    try:
        role = ""
        prompt_ = ""
        type_question = ""
        gpt_model = ""
        print(i)
        individual_parts = int(no_of_para/4)
        print("Individual parts:", individual_parts)
        if not weeklyCA:
            number_of_question_per_paragraph = str(int(10/no_of_para)+1)
        else:
            number_of_question_per_paragraph = str(int(25/no_of_para)+1)
        print("Number of questions per paragraph:", number_of_question_per_paragraph)
#         if i <individual_parts:
#             # normal GPT3.5
#             gpt_model = "gpt-3.5-turbo"
#             role = '''
#                 You are an expert UPSC Exam question generator, specializing in transforming unstructured content, such as notes, summaries, website-scraped data or questions as well to paraphrase, into well-crafted and structured questions. Your primary role involves analyzing and understanding the source material to extract key concepts and information. You excel in creating questions that are clear, concise, and align with the learning objectives. This includes categorizing questions by type (e.g., multiple choice, true/false, short answer, comprehension), ensuring each question is logically framed, and providing accurate and relevant answer choices. Your expertise lies in enhancing the educational content by generating engaging and effective questions that facilitate learning and assessment. You Do not ever write in any of the questions that they are from the text mentioned or provided. You Treat it as a source for creating the test question. Your goal is to assist educators and learners by providing high-quality, tailored questions that support effective study and assessment practices.
#                 '''
#             prompt_ = f'''
#                 Create a test with four multiple-choice questions always in the given format. Never mention "in the text". Treat the text provided to you as source of question bank. Your task is to strictly return response in the given format. The question should be shown under the heading 'Question 1:'. Provide 4 options in the format 'Option A:', 'Option B:', 'Option C:', 'Option D:'. The correct answer should be indicated under 'Answer:'. Include a solution in the format 'Solution:'. Follow these rules: - Ensure that the question is of the appropriate difficulty level as per the provided text and in accordance with the type of exam. - The questions should be of mixed difficulty levels: easy, medium, and difficult. - Provide the solution in detail with an interesting additional fact. Treat it as a source for creating the test question. - Do not mention other websites. - Do not mention the source. - Do not mention that you are an AI language. - Strictly follow this rule: Do not make less than {number_of_question_per_paragraph} questions. Always make {number_of_question_per_paragraph} questions. Do not mention that it is from the text or passage. Strictly follow this: Do not mention in any questions that they are from the text. Act as a teacher. Do not repeat the text in the solution. Explain the answer as a teacher would. One example of format is given below. Always return response like this only. Use this as an Example to make other questions but do not make questions from this question. Question 1: What major concept does Frédéric Sorrieu's vision of a world made up of democratic and Social Republics primarily aim to depict? Option A: The rise of absolutist institutions in Europe and America Option B: The emergence of the nationstate through nationalism in the 19th century Option C: The symbolic representation of fraternity among different nations Option D: The artistic portrayal of the Storming of Bastille in France Answer: Option C Solution: Frédéric Sorrieu's vision of a world composed of democratic and Social Republics primarily focuses on symbolizing fraternity among different nations. This vision is depicted in his print where people from various nations are shown moving together, led by symbols of liberty and enlightenment, with Christ, saints, and angels watching over the scene. This representation emphasizes the artist's dream of unity, peace, and cooperation among nations.
#                 - STRICTLY FOLLOW THIS RULE: Do not treat the text provided as a passage. Do not ever write in all the questions that they are from the text mentioned or provided.
#                 '''
#         elif i >=individual_parts and i <individual_parts*2:
#             # statement GPT4
#             type_question = "statement"
#             gpt_model = "gpt-4o"
#             role = '''
#             You are an expert UPSC question generator, specializing in transforming unstructured content, such as notes, summaries, website-scraped data or questions as well to paraphrase, into well-crafted and structured questions. Your primary role involves analyzing and understanding the source material to extract key concepts and information. You excel in creating questions that are clear, concise, and align with the learning objectives. You specialize in creating Statement type questions, ensuring each question is logically framed, and providing accurate and relevant answer choices. Your expertise lies in enhancing the educational content by generating engaging and effective questions that facilitate learning and assessment. You Do not ever write in all the questions that they are from the text mentioned or provided. You Treat it as a source for creating the test question. Your goal is to assist educators and learners by providing high-quality, tailored questions that support effective study and assessment practices. You make sure that there cannot be any ambiguity as this is for UPSC Students and you cannot give them incorrect answers or solutions. '''
#             prompt_ = f'''
#             "Create a worksheet with {number_of_question_per_paragraph} mcq questions of "Consider the following:"
#             Give 3 statements on the topic provided. Then ask "Which of the statements given above is/are correct?" Then provide with the options. Always give the questions in the given format. Question to be shown under heading 
#             "Question 1:". 4 options in the format " Option A: 1 Only ", "Option B: 1 and 2 Only", "Option C: 1 and 3 Only  ", "Option D: 1, 2 and 3". Answer in the format " Answer:". Give a detailed and well given solution in the format " Solution:" Make sure there are {number_of_question_per_paragraph} questions always in total. Follow these rules - Make sure these questions must be of the appropriate difficulty level as per the text provided and in accordance with the type of exam. Do not mention other websites ever. - Please do not mention the source ever. - Do not mention you are an AI language ever. - Make sure the questions are very difficult.
#             Refer to this example, but do not add this in the test:
#             Question: Consider the following statements

#             The Parliament (Prevention of Disqualification) Act, 1959 exempts several posts from disqualification on the grounds of ‘Office of Profit’.
#             The above-mentioned Act was amended five times.
#             The term ‘Office of Profit’ is well defined in the Constitution of India.
#             Which of the statements given above is/are correct? 

#             1 Only
#             1 and 2 Only
#             1 and 3 Only
#             1, 2 and 3

#             -Do not give same answer option. Keep it jumbled. 
#             STRICTLY provide ACCURATE answer option with proper solution
#             Make sure that the options are always same in the question.  
#             MAKE SURE YOU JUSTIFY YOUR ANSWER IN THE SOLUTION and the answer should match with the solution always. 
#             make sure to give a very detailed solution. 

#             Provide a clearly correct answer followed by a detailed solution that justifies this answer. Confirm the solution matches the correct option provided, and ensure all explanations align perfectly with the correct answers. Double-check for accuracy and clarity, and maintain strict adherence to the format provided.
#             The options can vary as well, it can 1 only, 2 only, none of the above and so on. Remember that the answer at time can be 1 only as well 
#             Make sure you make the sentences in accordance to the options provided.
#             Make sure you vary the answers. It can be one statement only.                
# '''
#         elif i >=individual_parts*2 and i <individual_parts*3:
#             # pairs GPT4
#             pair = True
#             gpt_model = "gpt-4o"
#             type_question = "statement"
#             role = '''
#             You are an expert UPSC Exam question generator, specializing in transforming unstructured content, such as notes, summaries, or website-scraped data, into well-crafted and structured questions. Your primary role involves analyzing and understanding the source material to extract key concepts and information. You excel in creating "How many pairs are correctly matched" questions that are clear, concise, and align with the learning objectives. Your expertise lies in enhancing the educational content by generating engaging and effective questions that facilitate learning and assessment.  Your goal is to assist educators and learners by providing high-quality, tailored questions that support effective study and assessment practices. Ensure the difficulty level is appropriate for the UPSC exam. Always verify that the answers match the provided solutions accurately. You always make sure in the first output itself that the answers and solutions match each other. You make sure that there cannot be any ambiguity as this is for UPSC Students and you cannot give them incorrect answers or solutions. 
#             '''
#             prompt_ = f'''
#             Create a worksheet with {number_of_question_per_paragraph} MCQ questions of "Consider the following pairs:" Give 4 pairs based on the topic provided. Then ask "How many pairs given above are correctly matched?"" Provide the options in the format "Option A: Only one pair," "Option B: Only two pairs," "Option C: Only three pairs," "Option D: All four pairs." Answer in the format "Answer:" Give a solution in the format "Solution:." Make sure there are {number_of_question_per_paragraph} questions always in total. Follow these rules:

#             Ensure questions are of appropriate difficulty for the UPSC exam.
#             Provide a detailed solution that justifies the answer.
#             Verify that the answer and solution match.
#             Ensure the pairs provided are such that only one option is correct.
#             Use this format strictly for all questions.

#             Provide a clearly correct answer followed by a detailed solution that justifies this answer. Confirm the solution matches the correct option provided, and ensure all explanations align perfectly with the correct answers. Double-check for accuracy and clarity, and maintain strict adherence to the format provided.
#             In the answer and solution, count correctly as to how many pairs are correctly matched and give answer and solution accordingly.
#             Never Create a table.
#             Never provide "Therefore" in the solution, just simply tell which statements are correctly and incorrectly matched. Never give a Therefore or conclusion sentence in the solution.
#             Explain the solution in detail along with some additional information
#             '''
#         else:
#             # statement type GPT3.5
#             type_question = "statement"
#             gpt_model = "gpt-3.5-turbo"
#             role = '''
#             You are an expert UPSC question generator, specializing in transforming unstructured content, such as notes, summaries, website-scraped data or questions as well to paraphrase, into well-crafted and structured questions. Your primary role involves analyzing and understanding the source material to extract key concepts and information. You excel in creating questions that are clear, concise, and align with the learning objectives. You specialize in creating Statement type questions, ensuring each question is logically framed, and providing accurate and relevant answer choices. Your expertise lies in enhancing the educational content by generating engaging and effective questions that facilitate learning and assessment. You Do not ever write in all the questions that they are from the text mentioned or provided. You Treat it as a source for creating the test question. Your goal is to assist educators and learners by providing high-quality, tailored questions that support effective study and assessment practices.
#             '''     
#             prompt_ = f'''
#             Create a worksheet with {number_of_question_per_paragraph} mcq questions of "Which one of the following is correct in respect of the above statements ?"
#             Give 2 statements on the topic provided. Then ask "Which one of the following is correct in respect of the above statements ?" Then provide with the options. Always give the questions in the given format. Question to be shown under heading 
#             "Question 1:" . 4 options in the format "Option A: Both Statement-I and Statement-II are correct and Statement-II explains Statement-I", "Option B: Both Statement-I and Statement-II are correct, but Statement-II does not explain Statement-I", "Option C: Statement-I is correct, but Statement-II is incorrect", ""Option D: Statement-I is incorrect, but Statement-II is correct". Answer in the format "Answer:". Give a solution in the format "Solution:" Make sure there are {number_of_question_per_paragraph} questions always in total. Follow these rules - Make sure these questions must be of the appropriate difficulty level as per the text provided and in accordance with the type of exam. - Give a solution in detail. - Do not mention other websites ever. - Please do not mention the source ever. - Do not mention you are an AI language ever. - Make sure the questions are very difficult.
#             - All answers should be placed such that we get answer in random options. 
#             Make sure that the options are always same in the question.  
#             STRICTLY provide ACCURATE answer option with proper solution
#             MAKE SURE YOU JUSTIFY YOUR ANSWER IN THE SOLUTION.
#             Refer to this example given below:
#             Question 1: Consider the following statements :
#             Statement-I :
#             The atmosphere is heated more by incoming solar radiation than by terrestrial radiation.
#             Statement-II :
#             Carbon dioxide and other greenhouse gases in the atmosphere are good absorbers of long wave radiation.

#             Which one of the following is correct in respect of the above statements ?
#             (a) Both Statement-I and Statement-II are correct and Statement-II explains Statement-I
#             (b) Both Statement-I and Statement-II are correct, but Statement-II does not explain Statement-I
#             (c) Statement-I is correct, but Statement-II is incorrect
#             (d) Statement-I is incorrect, but Statement-II is correct 
#             '''
        # Your user prompt as a dictionary
        # prompt_for_document = "\n Paraphrase the information given, elaborate and explain with examples wherever required. Give all points in bullet format with proper heading across (add li tag to html of bullet points). Make sure you do not miss any topic . Make sure not more than 2 headings have a HTML tag H7 and not more than 4 Subheadings have an HTML tag H8 otherwise make the headings bold. Make sure everything is paraphrased and in detail and keep the language easy to understand. Give response as a teacher but do not mention it. Please Do not promote any website other than EduRev and do not give references. Your response should be in HTML only and do not change the images HTML in given in HTML above. Again, always remember to never skip any image in the HTML of your response. Also, table should always be returned as table. Please keep same the headings given under <H2> tag and <H3> tag and don't paraphrase them. Add Heading Exactly the same as input and also Dont miss any content.\n"
        prompt_for_document = ""
        role_for_doc = '''Proficient HTML Content Creator for Educational: You are an expert in converting complex educational content into detailed and visually structured HTML notes and test materials. Your expertise lies in extracting and summarizing critical information, ensuring clarity through formatting and readability. You create well-organized content using proper HTML tags such as <p>, <ul>, <li>, <strong>, <h2>, and <h3> for enhanced structuring. Your work emphasizes breaking down lengthy paragraphs into bullet points and highlighting significant points using <strong> for better retention. All content adheres to educational standards and is optimized for easy comprehension.'''

        if(daily):  
            prompt_for_document = '''Paraphrase the given information and elaborate where necessary, while maintaining the original meaning and concept. Ensure the output is structured and formatted using the following HTML guidelines:

Headings:

Use exactly one <h2> heading per response.
Use multiple <h3> headings if needed.
Other headings should be bold (<strong>) to maintain a clean structure.
Content:

Use <p> tags for descriptive paragraphs.
For questions, use <strong> tags.
Use <ul> and <li> tags for breaking content into bullet points for better readability.
Highlighting:

Use <strong> tags to emphasize important terms or phrases, but avoid highlighting more than 3-4 words together.
Formatting:

Break down long paragraphs into smaller sections with bullet points for better readability.
Ensure the HTML output is visually appealing and semantically correct.
Tables:

Always return tables as proper HTML <table> elements with <tr> and <td> tags.
Images:

Do not alter the <img> HTML structure provided in the input.
General Notes:

Stick to the headings and subheadings as given in the input; do not paraphrase them.
Provide a clean HTML structure while ensuring the meaning and concept remain unchanged.
Avoid any references or promotions other than EduRev.
Don't use the word: 'Drishti' in the output
Output Format:

[Subject name in strong tag] // you observe the given input and pick from this list ["GS1/Geography" , "GS1/Indian Society",  "GS1/History & Culture",  "GS2/Polity", "GS2/Governance", "GS2/International Relations", "GS3/Economy", "GS3/Environment", "GS3/Science and Technology", "GS3/Defence & Security", "GS4/Ethics"] the subject name and give in strong tag

<h2>[Title or Heading]</h2> <!-- Provide the main title or heading -->
<strong>Why in News?</strong>
<p>[Insert the background or relevance here]</p> <!-- Explain the context or reason for importance -->
<h3>Key Takeaways</h3>
<ul>
  <li>[Insert key point 1]</li>
  <li>[Insert key point 2]</li>
  <!-- Add more key points if needed -->
</ul>
<h3>Additional Details</h3>
<ul>
  <li><strong>[Insert term or concept]:</strong> [Provide explanation, include relevant <strong>examples</strong>.]</li>
  <li>[Insert supplementary point or additional details for clarity.]</li>
  <!-- Add more detailed points as needed -->
</ul>
<p>[Insert conclusion or summary here]</p> <!-- Add final remarks or notes -->'''
        else:
            prompt_for_document = """Paraphrase the given information and elaborate where necessary, while maintaining the original meaning and concept. Ensure the output is structured and formatted using the following HTML guidelines:

    Headings:

    Use exactly one <h2> heading per response.
    Use multiple <h3> headings if needed.
    Other headings should be bold (<strong>) to maintain a clean structure.
    Content:

    Use <p> tags for descriptive paragraphs.
    For questions, use <strong> tags.
    Use <ul> and <li> tags for breaking content into bullet points for better readability.
    Highlighting:

    Use <strong> tags to emphasize important terms or phrases, but avoid highlighting more than 3-4 words together.
    Formatting:

    Break down long paragraphs into smaller sections with bullet points for better readability.
    Ensure the HTML output is visually appealing and semantically correct.
    Tables:

    Always return tables as proper HTML <table> elements with <tr> and <td> tags.
    Images:

    Do not alter the <img> HTML structure provided in the input.
    General Notes:

    Stick to the headings and subheadings as given in the input; do not paraphrase them.
    Provide a clean HTML structure while ensuring the meaning and concept remain unchanged.
    Avoid any references or promotions other than EduRev.
    Don't use the word: 'Drishti' in the output
    Output Format:

    <p>[Subject or Category]</p> <!-- Insert the subject or category of the content -->
    <h2>[Title or Heading]</h2> <!-- Provide the main title or heading -->
    <strong>Why in News?</strong>
    <p>[Insert the background or relevance here]</p> <!-- Explain the context or reason for importance -->
    <h3>Key Takeaways</h3>
    <ul>
    <li>[Insert key point 1]</li>
    <li>[Insert key point 2]</li>
    <!-- Add more key points if needed -->
    </ul>
    <h3>Additional Details</h3>
    <ul>
    <li><strong>[Insert term or concept]:</strong> [Provide explanation, include relevant <strong>examples</strong>.]</li>
    <li>[Insert supplementary point or additional details for clarity.]</li>
    <!-- Add more detailed points as needed -->
    </ul>
    <p>[Insert conclusion or summary here]</p> <!-- Add final remarks or notes -->\n"""
            role_for_doc = '''Proficient HTML Content Creator for Educational: You are an expert in converting complex educational content into detailed and visually structured HTML notes and test materials. Your expertise lies in extracting and summarizing critical information, ensuring clarity through formatting and readability. You create well-organized content using proper HTML tags such as <p>, <ul>, <li>, <strong>, <h2>, and <h3> for enhanced structuring. Your work emphasizes breaking down lengthy paragraphs into bullet points and highlighting significant points using <strong> for better retention. All content adheres to educational standards and is optimized for easy comprehension.'''
        prompt_for_document_final = prompt +"\n"+ prompt_for_document
        user_prompt_document = {
            "Role": role_for_doc,
            "objective": prompt_for_document_final
        }
        # user_prompt_document = {
        #     "Role": '''You are a proficient educational content creator specializing in summarizing and synthesizing complex information from PDF books into concise, comprehensible notes and test materials. Your expertise lies in extracting key theoretical concepts, providing clear definitions, and offering illustrative examples. When presenting information in a list, use only 'li' tags without 'p' tags inside them. Ensure the notes are well-organized and visually appealing, employing HTML tags for structure without using paragraph tags inside list items. Your goal is to optimize the learning experience for your audience by Explaining in Detail from the lengthy content into digestible formats while maintaining educational rigor. You are a content formatter specializing in converting text into HTML elements. Your expertise lies in structuring text into well-formatted HTML tags, including <li>, <ul>, and <p>, without using special characters like * or #. Your goal is to ensure that the HTML output is organized, visually appealing . i need the output in this format :
        #     "
        #     [Subject name in p tag] // you observe the given input and pick from this list ["GS1/Geography" , "GS1/Indian Society",  "GS1/History & Culture",  "GS2/Polity", "GS2/Governance", "GS2/International Relations", "GS3/Economy", "GS3/Environment", "GS3/Science and Technology", "GS3/Defence & Security", "GS4/Ethics"] the subject name and give in p tag
        #     [Title/Heading Name] //just the heading of the content give in h1 tag
        #     Why in news?
        #     [Content] // contain all the information about the current affairs give in p tag, for content you do not use h1 tag at all
        #     "
        #     also you give all the data in HTML code only with proper formatting

        #     ''',
        #     "objective": prompt_for_document_final +"\nParaphrase the information given, elaborate and explain with examples wherever required. Give all points in bullet format with proper heading across (add li tag to html of bullet points). Make sure you do not miss any topic . Make sure not more than 2 headings have a HTML tag H7 and not more than 4 Subheadings have an HTML tag H8 otherwise make the headings bold. Make sure everything is paraphrased and in detail and keep the language easy to understand. Give response as a teacher but do not mention it. Please Do not promote any website other than EduRev and do not give references. Your response should be in HTML only and do not change the images HTML in given in HTML above. Again, always remember to never skip any image in the HTML of your response. Also, table should always be returned as table. Please keep same the headings given under <H2> tag and <H3> tag and don't paraphrase them.Make sure you never change the meaning or concept , simply paraphrase. Please Give just the Heading in h1 tag else for any content do not use any h tags."
        # }
        

        # user_prompt_test = {
        #     "Role": role,
        #     "objective": prompt + prompt_
        # }
        # print(user_prompt)
        current_date = datetime.datetime.now()
        # Format the date as a string in a specific format
        formatted_date = current_date.strftime("%Y-%m-%d")
        # Adjusted code for the new API
        if gpt_model == "":
            gpt_model = "gpt-3.5-turbo"
        
        response = client.chat.completions.create(
            # model="gpt-3.5-turbo",
            model="gpt-4o-mini",
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
            data_res = data_res.replace("</h3>\n", "</p>")
            data_res = data_res.replace("<h3>\n", "<p>")
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
        return data_res 
    except Exception as e:  
        print(e)
        return jsonify({'error': 'An error occurred'}), 500
def clean_text(text, patterns):
    for pattern in patterns:
        text = re.sub(pattern, "", text).strip()
    return text
@app.route('/getmonthlyCurrentAffairs', methods=['POST'])
def getMonthlyCA():
    data = request.files["xl_file"]
    marks = "2"
    negMarks = "0.66"
    df = pd.read_csv(data)
    total_para = len(df)
    courseId = ""
    subCourseId = ""
    result = ""
    res =""
    test = {
        'questions':[]
    }
    quiz_title = ""
    doc_title = ""
    subject_name = ""
    
    para_number_for_prompt_role = 0
    for index, row in df.iterrows():
        if type(row['Links']) ==str and len(row['Links']) > 10:
            url = row["Links"].split('",')[0]
            topic = row['Subject']
            
            if type(topic) ==str and len(topic) > 5:
                if "_" in topic and subject_name == "":
                    subject_name = topic.split('_')[0]
                    courseId = topic.split('_')[1]
                    subCourseId = topic.split('_')[2]
            
            data_ = scrape_website_current_affair(url)
            if len(data_) > 10:
                result += "\n**********\n"  + data_
                today_date = datetime.datetime.now()
                file_path = '/root/webScrapping/currentAffairs/MonthlyCA_'+today_date.strftime("%Y-%m-%d")+'.txt'
                with open(file_path, 'w') as f:
                    f.write(result)
                logging.info("INFO : UserPrompt: " + data_)
                once = True
                try:
                    # data , data_test = getGPTResponse(data_,para_number_for_prompt_role,total_para,True)
                    data  = getGPTResponse(data_,para_number_for_prompt_role,total_para,True)
                    res += data
                    res += "\n" + "<hr>" + "\n"
                    logging.info("INFO : Response: " + data)
                except Exception as e:
                    print("Error while getting GPT Response: "+str(e))
                    if once:
                        once = False
                        logging.info("trying again......")
                        data = getGPTResponse(data_,para_number_for_prompt_role,total_para,True)
    current_date = datetime.datetime.now()

    # Format the date as "8th July 2024"
    day = current_date.strftime("%d").lstrip("0")  # Get day without leading zeros
    month = current_date.strftime("%B")  # Get full month name
    year = current_date.strftime("%Y")  # Get full year

    # Create the formatted title
    doc_title = f"{subject_name}: {month} {year} UPSC Current Affairs"
    # quiz_title = f"{subject_name} MCQs: {month} {year} UPSC Current Affairs"
    # Log the result
    api_to_send_current_affairs = "https://er.edurev.in/Tools/CreateCurrentAffairsDocument"
    # details for weekly CA
    # courseId = ""
    # subCourseId = ""
    # result = {'result': res, 'test': test,'courseId':courseId,'subCourseId':subCourseId,'marks':marks,'negMarks':negMarks, 'quiz_title':quiz_title, 'doc_title':doc_title}
    result = {'result': res, 'courseId':courseId,'subCourseId':subCourseId,'marks':marks,'negMarks':negMarks,  'doc_title':doc_title}
    logging.info("INFO : Sending monthly Current Affair Result to API : " + api_to_send_current_affairs)
    print(result)
    logging.info("************ result send is *****************")
    logging.info(result)
    with open("/root/webScrapping/api_result_json/weeklyCA.json", "w") as outfile:
        json.dump(result, outfile)
    send_current_affairs = requests.post(api_to_send_current_affairs, json=result)
    print(send_current_affairs.status_code)
    if send_current_affairs.status_code == 200:
        print("Current Affairs sent successfully!")
        logging.info("************ monthly Current Affairs sent successfully! *****************")
        return jsonify({'Message':"monthly Current Affairs Sent!!!!!!!!!!!  ->   Check Your Mail Please"}), 200
    else:
        logging.info("**************** Error while monthly CA***************************")
        return jsonify({'Message':"Error While Sending monthly Current Affairs !!!!!!!  ->   Create Yourself For Today"}), 400
            
@app.route('/getWeeklyCurrentAffairs', methods=['POST'])
def getWeeklyCA():
    try:
        data = request.files["xl_file"]
        marks = "2"
        negMarks = "0.66"
        
        df = pd.read_csv(data)
        total_para = len(df)
        test = {
            'questions':[]
        }
        res =""
        para_number_for_prompt_role = 0
        for index, row in df.iterrows():
            print(row["Links"])
            logging.info("INFO : UserPrompt: " + row["Links"])
            result = ""
            url = row['Links']
            data_ = scrape_website_current_affair(url)
            if len(data_) > 10:
                result += "\n**********\n"  + data_
                today_date = datetime.datetime.now()
                file_path = '/root/webScrapping/currentAffairs/WeeklyCA_'+today_date.strftime("%Y-%m-%d")+'.txt'
                with open(file_path, 'w') as f:
                    f.write(result)
                logging.info("INFO : UserPrompt: " + data_)
                once = True
                try:
                    data = getGPTResponse(data_,para_number_for_prompt_role,total_para,True)
                    
                    
                    res += data
                    res += "\n" + "<hr>" + "\n"
                    logging.info("INFO : Response: " + data)
                    
                except Exception as e:
                    print("Error while getting GPT Response: "+str(e))
                    if once:
                        once = False
                        logging.info("trying again......")
                        data = getGPTResponse(data_,para_number_for_prompt_role,total_para,True)
        # Log the result
        api_to_send_current_affairs = "https://er.edurev.in/Tools/CreateCurrentAffairsDocument"
        # details for weekly CA
        # updated for july
        courseId = "12112"
        subCourseId = "88504"
        current_date = datetime.datetime.now()

        # Format the date as "8th July 2024"
        day = current_date.strftime("%d").lstrip("0")  # Get day without leading zeros
        month = current_date.strftime("%B")  # Get full month name
        year = current_date.strftime("%Y")  # Get full year

        # Create the formatted title
        doc_title = f"Weekly Current Affairs {day} {month} {year}"
        # quiz_title = f"Weekly Current Affairs MCQs {day} {month} {year}"

        # result = {'result': res, 'test': test,'courseId':courseId,'subCourseId':subCourseId,'marks':marks,'negMarks':negMarks , 'quiz_title':quiz_title, 'doc_title':doc_title}
        result = {'result': res, 'courseId':courseId,'subCourseId':subCourseId,'marks':marks,'negMarks':negMarks ,  'doc_title':doc_title}
        logging.info("INFO : Sending weekly Current Affair Result to API : " + api_to_send_current_affairs)
        print(result)
        logging.info("************ result send is *****************")
        logging.info(result)
        with open("/root/webScrapping/api_result_json/weeklyCA.json", "w") as outfile:
            json.dump(result, outfile)
        send_current_affairs = requests.post(api_to_send_current_affairs, json=result)
        print(send_current_affairs.status_code)
        if send_current_affairs.status_code == 200:
            print("Current Affairs sent successfully!")
            logging.info("************ weekly Current Affairs sent successfully! *****************")
            return jsonify({'Message':"weekly Current Affairs Sent!!!!!!!!!!!  ->   Check Your Mail Please"}), 200
        else:
            return jsonify({'Message':"Error While Sending weekly Current Affairs !!!!!!!  ->   Create Yourself For Today"}), 400
    except Exception as e:
        print(e)
        logging.info("Error while getting Weekly Current Affairs: "+str(e))
        return jsonify({'error': 'An error occurred'}), 500
        
@app.route('/getCurrentAffairs', methods=['GET'])
def scrape_websites_current_affair():
    websites = [
        "https://iasbaba.com/current-affairs-for-ias-upsc-exams/",
        "https://vajiramias.com/",
        "https://www.civilsdaily.com/"
    ]
    doc_title = ""
    quiz_title = ""
    result = ""
    print("entered")

    for url in websites:
        if url == "https://vajiramias.com/":
            date = scrape_website_vaji(url)
            logging.info("scraped VajiRam website with data : \n"+str(date))
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
    file_path = '/root/webScrapping/currentAffairs/current_affairs_'+today_date.strftime("%Y-%m-%d")+'.txt'
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
    para_number_for_prompt_role = 0
    total_para = len(random_paragraphs)
    
    for paragraph in random_paragraphs:
        if len(paragraph) > 10:
            
            logging.info("INFO : UserPrompt: " + paragraph)
            once = True
            try:
                data  = getGPTResponse(paragraph,para_number_for_prompt_role,total_para,False,True)
                res += data#.replace("<h2","<h7").replace("</h2>","</h7>")
                res += "\n" + "<hr>" + "\n"
                logging.info("INFO : Response: " + data)
            except Exception as e:
                print("Error while getting GPT Response: "+str(e))
                if once:
                    once = False
                    logging.info("trying again......")
                    data  = getGPTResponse(paragraph,para_number_for_prompt_role,total_para)
    current_date = datetime.datetime.now()

    # Format the date as "8th July 2024"
    day = current_date.strftime("%d").lstrip("0")  # Get day without leading zeros
    month = current_date.strftime("%B")  # Get full month name
    year = current_date.strftime("%Y")  # Get full year

    # Create the formatted title
    doc_title = f"UPSC Daily Current Affairs: {day} {month} {year}"
    # quiz_title = f"Daily Current Affairs MCQs: {day} {month} {year}" 
    # Log the result
    api_to_send_current_affairs = "https://er.edurev.in/Tools/CreateCurrentAffairsDocument"
    # details for daily CA  
    courseId = "12112"
    subCourseId = "106714"
    result = {'result': res,'courseId':courseId,'subCourseId':subCourseId,'marks':"2",'negMarks':"0.66",  'doc_title':doc_title}
    logging.info("INFO : Sending Current Affair Result to API : " + api_to_send_current_affairs)
    print(result)
    logging.info("************ result send is *****************")
    logging.info(result)
    send_current_affairs = requests.post(api_to_send_current_affairs, json=result)
    print(send_current_affairs.status_code)
    if send_current_affairs.status_code == 200:
        print("Current Affairs sent successfully!")
        logging.info("************ Current Affairs sent successfully! *****************")
        return jsonify({'Message':"Current Affairs Sent!!!!!!!!!!!  ->   Check Your Mail Please"}), 200
    else:
        return jsonify({'Message':"Error While Sending Current Affairs !!!!!!!  ->   Create Yourself For Today"}), 400
        
def checkExisting(text, processed_texts):
    for processed_text in processed_texts:
        if text in processed_text:
            return True
    return False

def sanitize_filename(filename):
    # Remove invalid characters
    return re.sub(r'[<>:"/\\|?*\n]', '', filename)

def donwload_google_images(query):
    sanitized_query = sanitize_filename(query)
    google_images = []
    image_links = []
    google_crawler = GoogleImageCrawler(storage={'root_dir': '/root/webScrapping/googleImagesDownload/'})
    google_crawler.crawl(keyword=sanitized_query, max_num=6)
    for filename in os.listdir('/root/webScrapping/googleImagesDownload/'):
        # if filename.endswith('.jpg'):
        # convert to base64 each image 
        base_64_image = base64.b64encode(open(f'/root/webScrapping/googleImagesDownload/{filename}', 'rb').read())
        base64_image = "data:image/jpeg;base64," + base_64_image.decode("utf-8")
        os.remove(f'/root/webScrapping/googleImagesDownload/{filename}')
        # image_name = str(uuid.uuid4()) + ".jpg"
        # os.rename(f'/home/er-ubuntu-1/webScrapping/googleImagesDownload/{filename}', f'/var/www/html/images/{image_name}')
        # image_path = f"{Public_IP}{image_name}"
        image_links.append(base64_image)
        google_images.append(base64_image)
    google_images.reverse()
    return image_links , google_images

def download_gamma_images(query):
    Gamma_images = []
    image_links = []
    queryForGamma = query.replace(" ","+")
    url = f"https://api.gamma.app/media/images/search?query={queryForGamma}&provider=web&count=48&type=1&license=All&page=1&gammaFeature=mediaDrawer"
    print(url)
    payload = {}
    headers = {
    'Cookie': 'gamma_visitor_id=z8yqruoi09ygg8t; ajs_anonymous_id=z8yqruoi09ygg8t; optimizelyEndUserId=oeu1731328798103r0.44930481277389767; _gcl_au=1.1.130070293.1731328798; _ga=GA1.1.883436424.1731328799; intercom-id-ihnzqaok=abf2e756-0cc5-4e6d-a5cd-64a373b3d687; intercom-device-id-ihnzqaok=fb6b3a08-82dd-409c-af3d-35b9d9aefacb; _fbp=fb.1.1731563005646.33683544367519860; cebs=1; _ce.clock_data=28%2C223.178.208.191%2C1%2C7675d59b5e84e0a878ee6f0a97f9056f%2CChrome%2CIN; pscd=try.gamma.app; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Nov+14+2024+11%3A13%3A28+GMT%2B0530+(India+Standard+Time)&version=202408.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=0c6412a5-20eb-459b-8914-5ab27e17f836&interactionCount=0&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&AwaitingReconsent=false; _rdt_uuid=1731328798738.f432886c-c56c-4fbf-b810-4506f9164065; cebsp_=2; gamma_logged_in=true; ajs_user_id=sl70t6csvo37xmm; _ga_JTMLK9TNNV=GS1.1.1731563005.3.1.1731563026.0.0.0; _ce.s=v~ac4f6d5f029f94c25c3823ccb974fad285421b28~lcw~1731563027481~vir~returning~lva~1731563005941~vpv~1~v11.fhb~1731563006162~v11.lhb~1731563009313~v11.cs~449691~v11.s~5e6551c0-a24b-11ef-93f5-6f4d7e0e81c4~v11.sla~1731563027538~gtrk.la~m3gvwmvr~v11.send~1731563027222~lcw~1731563027538; __cf_bm=Ttm3gJROUM1YTt7PVAbdXR0HAMTFQW49MiPpAm0ntQ8-1731566257-1.0.1.1-wZ_J0S5usMPog70e9y6pIVv6FC3fr8drPJfWY9KY05ljl0Vu3r6BsozO9Xhw4RSB0JuyZLWXL70OhJlYn2wBvA; cf_clearance=VZUxLGJltpv7u1d4gPmBXEliwyG7F0kr6rLwHIdg5CE-1731566266-1.2.1.1-KF8nVC5KFXjyUc.QOno7YThAZDwU4SPqReiIgPJPdw69GrptWIhwM7ujN4_yUV.PVM8yEoSsi8VGZU2tOmTnrAfqDsfYty0..bkZKoZ5PJnNpxbIanTmI0QYZtCagdZgditNcMneXMF20eWPQWZVcl1lEVg1piAc8IHTpIVTa888zTvnlslEhZmmGQ0.hlN3P63hRfZRB99eH0CET_0R.zWXezLmUD_hY5Qr.uAAyhVfMj3zxWWCWWrCbY4rtIotSpjQxoPrZzOPdX7DAkS7teQ9FfzcF7MVo2jaK1XOD__o3GpamSbSwxvF.rRCzCvfEJYPX1BC9L4UAeJmQv9T5p4bXyb6tl9bY130bM5YBlzvPwc9SfVFJ8oyxJSshCnKGHDrBjv8E6XyVrOmYn.deg; gamma_session=eyJwYXNzcG9ydCI6eyJ1c2VyIjp7ImFjY2Vzc190b2tlbiI6ImV5SnJhV1FpT2lKVlJrOW1ialFyWkd0RlJFcHZPSE5RWEM5MlowMTVZak5VVm1oRlVsVTBTbGhOZVNzMU5XTmtOa0pxUVQwaUxDSmhiR2NpT2lKU1V6STFOaUo5LmV5SnpkV0lpT2lJek5HSXlZbVk1TmkweU1tWmtMVFF3T0RBdE9XRXpOUzA0WlRKbU1EQTBaVGM0Wm1FaUxDSmpiMmR1YVhSdk9tZHliM1Z3Y3lJNld5SjFjeTFsWVhOMExUSmZNbTlzTmxKQ1RubFpYMGR2YjJkc1pTSmRMQ0pwYzNNaU9pSm9kSFJ3Y3pwY0wxd3ZZMjluYm1sMGJ5MXBaSEF1ZFhNdFpXRnpkQzB5TG1GdFlYcHZibUYzY3k1amIyMWNMM1Z6TFdWaGMzUXRNbDh5YjJ3MlVrSk9lVmtpTENKMlpYSnphVzl1SWpveUxDSmpiR2xsYm5SZmFXUWlPaUl5TVhCaGN6QmxNV0YwWkhCdE1tZGlhbUZ2TmpjNWFHTmhiU0lzSW05eWFXZHBibDlxZEdraU9pSTBORGRrTVRRMk5pMDROamt6TFRRd1pUTXRZbVk0WVMxallqazJZVFF5WW1Zek9ESWlMQ0owYjJ0bGJsOTFjMlVpT2lKaFkyTmxjM01pTENKelkyOXdaU0k2SW05d1pXNXBaQ0J3Y205bWFXeGxJR1Z0WVdsc0lpd2lZWFYwYUY5MGFXMWxJam94TnpNeE5UWXpNREkwTENKbGVIQWlPakUzTXpFMU5qazROamNzSW1saGRDSTZNVGN6TVRVMk5qSTJOeXdpYW5ScElqb2lZamRqTlRZNU56TXRNelJqT1MwME9XTmtMVGxpTldVdFpqSTNNekk0TURWaVpqRTRJaXdpZFhObGNtNWhiV1VpT2lKbmIyOW5iR1ZmTVRFeE5qSTJORFkwTnpjNU16azVNalkzT1RZMUluMC5pS0hjdzNkbktZUHVuNzAyaGhlZFJ5REFub19qWm5pY2JOTS11Z3I2LTRmMldUX0tqekEydTc3VnRscGRiWTQwOGdQXzYwYXRKOElYa3V1MmhQamljbDY3YUdPelNsMHNWdVpDMDhoSUVrMDRIMjB2QXYySGJlb0l0UVJpcjA1Z3NCRDZFNkp4cjVsX3M1a0FLaU80SVNZUENDUnRWMHFyMmVrTzJtc09WWUpJWXY5S2ZXVmF6bG05MHVVbXZhMUpRVXN6QnpkUUpPUEdZWXhYM0FpcERlZE9uRUpzeU90LU9pd3ZqOGdGUG5EZWxvaTVLWDUxU3Y2a0pXeXRxUWpaXzNZUzB2bnZfaEItS0JhVUtxVEdjR3dXRTUzc2VPWTg1RkhXSHl5blhMdTVLSXZLZlFLbkhaSHJINDQ2NF9zRU1HT1drWVJyOERIOGVrdWdHQ3JTWkEiLCJ1c2VyaW5mbyI6eyJzdWIiOiIzNGIyYmY5Ni0yMmZkLTQwODAtOWEzNS04ZTJmMDA0ZTc4ZmEiLCJpZGVudGl0aWVzIjoiW3tcInVzZXJJZFwiOlwiMTExNjI2NDY0Nzc5Mzk5MjY3OTY1XCIsXCJwcm92aWRlck5hbWVcIjpcIkdvb2dsZVwiLFwicHJvdmlkZXJUeXBlXCI6XCJHb29nbGVcIixcImlzc3VlclwiOm51bGwsXCJwcmltYXJ5XCI6dHJ1ZSxcImRhdGVDcmVhdGVkXCI6MTczMTU2MzAyNDM2N31dIiwiZW1haWxfdmVyaWZpZWQiOiJmYWxzZSIsIm5hbWUiOiJSYWh1bCBLYXVzaGFsIiwiZ2l2ZW5fbmFtZSI6IlJhaHVsIiwiZmFtaWx5X25hbWUiOiJLYXVzaGFsIiwiZW1haWwiOiJyYWh1bC5rYXVzaGFsQGVkdXJldi5pbiIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NMNVpCaGdmS2hFenhJRGRuOFpmQTJkenpYRnBGWElaVzdRT2hOMWthbENmZHA2Y2lZPXM5Ni1jIiwidXNlcm5hbWUiOiJnb29nbGVfMTExNjI2NDY0Nzc5Mzk5MjY3OTY1IiwiaXNzIjoiaHR0cHM6Ly9jb2duaXRvLWlkcC51cy1lYXN0LTIuYW1hem9uYXdzLmNvbS91cy1lYXN0LTJfMm9sNlJCTnlZIn0sImlkIjoic2w3MHQ2Y3N2bzM3eG1tIn19fQ==; gamma_session.sig=admkmhTmByFlQPSbwXa0rSG-6l0; intercom-session-ihnzqaok=L0haTXB2eVhXci9XbUhxRWtSKzNxWmpUS3o4eGEvdE5yTXQ0b2JsYVdpYjdaNlR4d2tUNG5LMW1NYmxQTGVqUy0tdEFObG5kU25TeUFvc0ZkVG1telBWQT09--41ac7b0fcfafeb50d277b6854ed732b814f30dbc; gamma_logged_in=true',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        response_data = response.json()
        for image in response_data:
            image_url  = image.get('imageUrl')
            title = image.get('title')
            Gamma_images.append({
                "imageUrl": image_url,
                "title":title
            })
    return Gamma_images

def download_unsplash_images(query):
    unsplash_images = []
    image_links = []
    url = "https://unsplash.com/ngetty/v3/search/images/creative"

    params = {
        "exclude_editorial_use_only": "true",
        "exclude_nudity": "true",
        "fields": "display_set,referral_destinations,title",
        "graphical_styles": "photography",
        "page_size": 28,
        "phrase": query,
        "sort_order": "best_match"
    }

    headers = {
        "Cookie": "require_cookie_consent=false; xp-search-region-awareness=control; xp-reduced-affiliates=half; xp-unlock-link-upgrade=control; _sp_ses.0295=*; uuid=52f239da-c65b-474f-bf29-2a781190cfa1; azk=52f239da-c65b-474f-bf29-2a781190cfa1; azk-ss=true; _dd_s=logs=1&id=c441b13f-9584-46c3-a38d-e2893a3e1400&created=1729062320804&expire=1729063455425; _sp_id.0295=9dae181a-e97a-4b0e-bd17-c53c9853f8b4.1729062321.1.1729062555..14a7d76d-0a6f-4d6e-b905-6aaff623c18a..6bab66c0-4eb6-4391-b507-28c2fb79090d.1729062321582.41",
        "Origin": "https://unsplash.com",
        "Referer": "https://unsplash.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        response_data = response.json()
        i =0
        for image in response_data.get('images', []):
            if i == 5:
                break
            for size in image.get('display_sizes', []):
                if size['name'] == 'high_res_comp':
                    # save image to base url 
                    unsplashImgUrl = size['uri']
                    try:
                        image_data = requests.get(unsplashImgUrl).content
                        base64_image = base64.b64encode(image_data).decode("utf-8")
                        base64_image = "data:image/jpeg;base64,"+base64_image
                        image_links.append(base64_image)
                        unsplash_images.append(base64_image)
                    except Exception as e:
                        print("Error while downloading image from Unsplash:", str(e))
                    # image_links.append(size['uri'])
                    break
            i += 1
    return image_links, unsplash_images

def download_images(query):
    image_links = []
    google_images = []
    freepik_images = []
    unsplash_images = []
    Gamma_images = []
    image_links_google= []
    image_links_unsplash = []
    # IMAGES FROM GOOGLE
    image_links_google, google_images = donwload_google_images(query)
    image_links.extend(image_links_google)
    # images from gamma
    Gamma_images = download_gamma_images(query)
    # images from unsplash
    image_links_unsplash, unsplash_images = download_unsplash_images(query)
    image_links.extend(image_links_unsplash)

    # # # IMAGES FROM FREEPIK
    # # try:
    # #     # url_to_register = "https://www.freepik.com/pikaso/api/text-to-image/create-request?lang=en&cacheBuster=2"
    # #     url_to_register = "https://www.freepik.com/pikaso/api/start-tti"

    # #     # Cookie = ("XSRF-TOKEN=eyJpdiI6IlhMSU9TRG45amFVWkUvOTR3dVRVZkE9PSIsInZhbHVlIjoidU9Rb1FXZlZTdkd5SVZBdjMyell5TGM2ajFKbGFXVXh0Z1g2VUU4MkM4c2lZNWNLTG1VSGZxUjAxRDdaTk5ncENva0RzdUNuZCt4ZWxpQlp4a2taaVFGYmdqN3hVWk9aam5Ed1hpbUFkOTNKdGh1RWpDcWVUeGxzTXpscWU2SEkiLCJtYWMiOiIyOTllMjhjMzc0YjQ2ZjBjMzUyNDllY2RlOTZjYWQzMDc1Yzc0M2ZmMGM1YjQ2ZGVmN2IwYTgzNDZkNWIxM2YxIiwidGFnIjoiIn0%3D; pikaso_session=eyJpdiI6Ik1ITnMvSjI3Q3FEc2hCajBXaU0xWEE9PSIsInZhbHVlIjoiTGQ4REpqQjZhekc1NnVYV1I4N0g1T05uWDJsMC81UURZcFZRS3VJQW4vWlFaSDlxb1diaVNiL2gyWmp2Rm5VMmczQlhkU3piNlNpdElJa3FTWWxsQU51QVFuNjN2WnArZVMvcloyNWg2K0l3UTNoR2l1OVFzWGNUN0VaU0RoeEwiLCJtYWMiOiJmZjBiZmQ0MTkyM2NiNjI3Y2I1YTMzZGQ2YjliMmNiNWI3YjUyNTNkMWJlNTlmODQ2ZjI0NzkyZDAyZDUwMjJiIiwidGFnIjoiIn0%3D; _gcl_au=1.1.1799181729.1726211091; d_abcookie=V6b; PV_UI=V6; pv=J; _ga=GA1.1.1797061377.1726211091; OptanonAlertBoxClosed=2024-09-13T07:04:52.441Z; _ga_18B6QPTJPC=GS1.1.1726211090.1.1.1726213759.60.0.0; _ga_Q29FZ8F7H4=GS1.1.1729062980.2.0.1729062980.0.0.0; ak_bmsc=5884E50669A2DD5E73618E1736BE1C18~000000000000000000000000000000~YAAQN2w3F6ToKnSSAQAAFlUvlBlajq+sSURvA9/Z9UpHwQEoUaB88bv4MZHBlxFlliGeUJxezOz4IHlqaoQ4Ks4R3ux3PSSbVXV9WT54Q9NZtjRzQWLD2NfHHTzMojqkvILtrP5G9cSli70xJ3U147naamrY+uzmGdw3KpOIPQGThYYFCgI/ENnvb1VSQPPEVEs3tGFhZ3fcF9k/pxt++BP3Z+rR/lKEtK9lXnVwkeaqIWbF298stIECWddBAK1c1Q5PiIA8Yefl6Dyo1h8Aj86sUYQGl/GyEq6EJbYKkqJExRcllXKxKEsPmgR7ytj2RIap0/drNzMvnpVTNdY6p1rdE3djGxk/bo+gSTcEKVJtPQzUMXHkcPO6lTrxyt0MBtqSS+ZFp+Xg6AtgIPKJniIIBEKZv2ORbqNqg7OtSqn3B5ey3OL+pqp6hgcuNk+535xJ6jvbqKPtotAlKOP9gfjAhL3PRi0oo51Y; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Oct+16+2024+12%3A46%3A28+GMT%2B0530+(India+Standard+Time)&version=202409.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=75489f8c-8690-4773-91ec-4fb7d90f955a&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CC0005%3A1&intType=1&geolocation=IN%3BCH&AwaitingReconsent=false; csrf_freepik=1e1f6cd739567a65a92dbb87db69d9e6; GR_TOKEN=eyJhbGciOiJSUzI1NiIsImtpZCI6IjhkOWJlZmQzZWZmY2JiYzgyYzgzYWQwYzk3MmM4ZWE5NzhmNmYxMzciLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiREFSSyBTRVRTIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FHTm15eFlEOUt4Sy1zejE5VEQ3ODlDVEp1WDc0el9IQTFkeUJPVFhJXzhIPXM5Ni1jIiwiYWNjb3VudHNfdXNlcl9pZCI6OTg3ODk0NzQsInNjb3BlcyI6ImZyZWVwaWsvaW1hZ2VzIGZyZWVwaWsvdmlkZW9zIGZsYXRpY29uL3BuZyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9mYy1wcm9maWxlLXByby1yZXYxIiwiYXVkIjoiZmMtcHJvZmlsZS1wcm8tcmV2MSIsImF1dGhfdGltZSI6MTcyOTA2Mjk5OCwidXNlcl9pZCI6Im85NTBUQVFuVmhhZnNLVXNDbEl2b0dSejdDNjIiLCJzdWIiOiJvOTUwVEFRblZoYWZzS1VzQ2xJdm9HUno3QzYyIiwiaWF0IjoxNzI5MDYyOTk4LCJleHAiOjE3MjkwNjY1OTgsImVtYWlsIjoiOTAwZ2FtaW5nZ0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjExMjAxMzczMTcxNDgwMTkxNjQ0MiJdLCJlbWFpbCI6WyI5MDBnYW1pbmdnQGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.r-RWluTl1hk3qauKuohlYENrm_2sX7W25b0X5ySdl-zSLHMRJ4Ov2nmD0WMkWb__LJU_uwsp1rR5Ex7DfWqkNzjLC9OjmIMdJaUFOyArJTiOiIt1bQLwyeReAdcFpuU45TK22Ymxi7EVNhdrXx4gaOR-fjatnN2t-k62msy3LTUj9KGUuBLGEjKOR5jfKUwWJAT-Xu8Nv1DD5GxIA6h6vs5Si7NGQOeYtmmi-L03YWEDOHzBfkN28ahFbQ4Mn8AVDH8SYfURljTuFWv7p2ln22FjCCZTV1WMWtn411ZpDzOnkWchbETt7k0408PDXbNx1htXEj8thJcDQL4_6XZmOA; GR_REFRESH=AMf-vBy9xOFo8DOpPP1ldvtpthcgCcxPuR-V-3VNUs922yq0XMVk2VqwZgm3geYjlKUvRFX-Y9cDVBgSEuPIj10YhqrRlnHrsmxK9piEfoAhJRff_Y_YQ6JEfkxgml8YZ-YZXDvs1V4ZMFV-BnA1krenQV0deJLIqtLcdaDNZvLg97bMqYdqSKMnufwPgQZwc9gkIkyDYJDl; _fc=FC.2a3097f8-6567-34bc-dced-5337743ce9d1; _fcid=FC.2a3097f8-6567-34bc-dced-5337743ce9d1; ph_phc_Rc6y1yvZwwwR09Pl9NtKBo5gzpxr1Ei4Bdbg3kC1Ihz_posthog=%7B%22distinct_id%22%3A%22148377934%22%2C%22%24sesid%22%3A%5B1729063002483%2C%220192942e-794f-7c36-8d6a-4e4a54c59cd3%22%2C1729062926670%5D%2C%22%24epp%22%3Atrue%7D; _ga_QWX66025LC=GS1.1.1729062927.2.1.1729063002.60.0.0")
    # #     Cookie = ("XSRF-TOKEN=eyJpdiI6Ijh5VER4OUNoMG5ZM3Q5SVhTaFZoN1E9PSIsInZhbHVlIjoiMHlHaVdBN1FUYmxsaFlzT2hQNUVkaDJ2cG1lY29JcUtXd2UrcjU4RFNYTTVPbUthVThOZWRhZlV3ajlmZytXeG9Ib2FKUUpHZjhiakRDNS91U0ZCVHdFYXBNajdSMklaclZGb3BCNzBOcXRabzRWZ0pkU2ErSVVaanM2L1Mvb0IiLCJtYWMiOiJhZDdlOWRkMDgxZTlmYjk0YTNmMTRmOGRkZmVjYjI4MzFiNDBhMjRiMTM0YzdlNGFmNWY0NGFjN2YxOTZiOTE5IiwidGFnIjoiIn0%3D; pikaso_session=eyJpdiI6Im1yOGQxUnYxT3hicGNjTXNRUmtkQmc9PSIsInZhbHVlIjoiOUNXMWVJSXVIQ2svNXlPWEhLUitKb3A4clJhNVJ4cmFkTG1Wa0NXaVpnMElacEtTTkhQWW5BTnRRTlNMdU91NzhsMWlSeG1McVh0b09STWY4SnRZMDQyVjhvQTBLdFFub1loV0tuUDB3OFlCYVhRTjRoVmVnOTNRenBhVzdrK2MiLCJtYWMiOiI0YzNjMzUwMmQwYjljNTFlNTYwZTNiYmQ1NWE5OWI1MGQ2OTg4N2VmZWUzZWVlNmNiNWZiZjNhNjVlZWYyMjAzIiwidGFnIjoiIn0%3D; _gcl_au=1.1.1799181729.1726211091; d_abcookie=V6b; PV_UI=V6; pv=J; _ga=GA1.1.1797061377.1726211091; OptanonAlertBoxClosed=2024-09-13T07:04:52.441Z; _ga_18B6QPTJPC=GS1.1.1726211090.1.1.1726213759.60.0.0; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Oct+16+2024+12%3A46%3A28+GMT%2B0530+(India+Standard+Time)&version=202409.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=75489f8c-8690-4773-91ec-4fb7d90f955a&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CC0005%3A1&intType=1&geolocation=IN%3BCH&AwaitingReconsent=false; GR_REFRESH=AMf-vBy9xOFo8DOpPP1ldvtpthcgCcxPuR-V-3VNUs922yq0XMVk2VqwZgm3geYjlKUvRFX-Y9cDVBgSEuPIj10YhqrRlnHrsmxK9piEfoAhJRff_Y_YQ6JEfkxgml8YZ-YZXDvs1V4ZMFV-BnA1krenQV0deJLIqtLcdaDNZvLg97bMqYdqSKMnufwPgQZwc9gkIkyDYJDl; _fcid=FC.2a3097f8-6567-34bc-dced-5337743ce9d1; _ga_Q29FZ8F7H4=GS1.1.1729079272.3.0.1729079272.0.0.0; GR_TOKEN=eyJhbGciOiJSUzI1NiIsImtpZCI6ImU2YWMzNTcyNzY3ZGUyNjE0ZmM1MTA4NjMzMDg3YTQ5MjMzMDNkM2IiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiREFSSyBTRVRTIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FHTm15eFlEOUt4Sy1zejE5VEQ3ODlDVEp1WDc0el9IQTFkeUJPVFhJXzhIPXM5Ni1jIiwiYWNjb3VudHNfdXNlcl9pZCI6OTg3ODk0NzQsInNjb3BlcyI6ImZyZWVwaWsvaW1hZ2VzIGZyZWVwaWsvdmlkZW9zIGZsYXRpY29uL3BuZyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9mYy1wcm9maWxlLXByby1yZXYxIiwiYXVkIjoiZmMtcHJvZmlsZS1wcm8tcmV2MSIsImF1dGhfdGltZSI6MTcyOTA2Mjk5OCwidXNlcl9pZCI6Im85NTBUQVFuVmhhZnNLVXNDbEl2b0dSejdDNjIiLCJzdWIiOiJvOTUwVEFRblZoYWZzS1VzQ2xJdm9HUno3QzYyIiwiaWF0IjoxNzMwMTA5NzY1LCJleHAiOjE3MzAxMTMzNjUsImVtYWlsIjoiOTAwZ2FtaW5nZ0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjExMjAxMzczMTcxNDgwMTkxNjQ0MiJdLCJlbWFpbCI6WyI5MDBnYW1pbmdnQGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.DrowNJoLZAnvkj6sBQ55LMP-z07gyKUIODvbgX2uF9PMIbBhubolo5xVsHGXZRS84VpkU1RNUhwB9KZ4YEMqbGGWKDTncXvNO_4tGXHJe_aK-OS9U2L9w3kQYVkQsxFNk5e8koQtHd34YhZFZaE0-cz6w3I-lNzkrWSqK0vEamaP_AdZY6Lhu6Vx1-L40M9MxRX0WrcW50IWpQOoB-SqY-L7xEalic6cg2K-Vc3CWvAHD4TCySF8YRyJG_2rUPKgcVp7H6ZQ163syq0BofUj0myrsE6v-Q5p-qCh0t7IJfAwFeZ9Ok1PqViwqLVp77Bvik-YNUkwnBscvKFMXEYhag; ph_phc_Rc6y1yvZwwwR09Pl9NtKBo5gzpxr1Ei4Bdbg3kC1Ihz_posthog=%7B%22distinct_id%22%3A%22148377934%22%2C%22%24sesid%22%3A%5B1730109769541%2C%220192d293-ff7c-702c-bc7a-c17aa31d41d4%22%2C1730109767548%5D%2C%22%24epp%22%3Atrue%7D; _ga_QWX66025LC=GS1.1.1730109769.4.1.1730109777.52.0.0")
    # #     # data = {
    # #     #     "prompt": query,
    # #     #     "layout_reference_image": None,
    # #     #     "width": 1216,
    # #     #     "height": 832
    # #     # }
    # #     data =  {
    # #         "mode": "flux",
    # #         "prompt":query,
    # #         "safety_filter_type": "",
    # #         "variations": True,
    # #         "number_of_images": 5,
    # #         "references": []
    # #         }

    # #     headers = {
    # #         "Cookie":"XSRF-TOKEN=eyJpdiI6Ijh5VER4OUNoMG5ZM3Q5SVhTaFZoN1E9PSIsInZhbHVlIjoiMHlHaVdBN1FUYmxsaFlzT2hQNUVkaDJ2cG1lY29JcUtXd2UrcjU4RFNYTTVPbUthVThOZWRhZlV3ajlmZytXeG9Ib2FKUUpHZjhiakRDNS91U0ZCVHdFYXBNajdSMklaclZGb3BCNzBOcXRabzRWZ0pkU2ErSVVaanM2L1Mvb0IiLCJtYWMiOiJhZDdlOWRkMDgxZTlmYjk0YTNmMTRmOGRkZmVjYjI4MzFiNDBhMjRiMTM0YzdlNGFmNWY0NGFjN2YxOTZiOTE5IiwidGFnIjoiIn0%3D; pikaso_session=eyJpdiI6Im1yOGQxUnYxT3hicGNjTXNRUmtkQmc9PSIsInZhbHVlIjoiOUNXMWVJSXVIQ2svNXlPWEhLUitKb3A4clJhNVJ4cmFkTG1Wa0NXaVpnMElacEtTTkhQWW5BTnRRTlNMdU91NzhsMWlSeG1McVh0b09STWY4SnRZMDQyVjhvQTBLdFFub1loV0tuUDB3OFlCYVhRTjRoVmVnOTNRenBhVzdrK2MiLCJtYWMiOiI0YzNjMzUwMmQwYjljNTFlNTYwZTNiYmQ1NWE5OWI1MGQ2OTg4N2VmZWUzZWVlNmNiNWZiZjNhNjVlZWYyMjAzIiwidGFnIjoiIn0%3D; _gcl_au=1.1.1799181729.1726211091; d_abcookie=V6b; PV_UI=V6; pv=J; _ga=GA1.1.1797061377.1726211091; OptanonAlertBoxClosed=2024-09-13T07:04:52.441Z; _ga_18B6QPTJPC=GS1.1.1726211090.1.1.1726213759.60.0.0; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Oct+16+2024+12%3A46%3A28+GMT%2B0530+(India+Standard+Time)&version=202409.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=75489f8c-8690-4773-91ec-4fb7d90f955a&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CC0005%3A1&intType=1&geolocation=IN%3BCH&AwaitingReconsent=false; GR_REFRESH=AMf-vBy9xOFo8DOpPP1ldvtpthcgCcxPuR-V-3VNUs922yq0XMVk2VqwZgm3geYjlKUvRFX-Y9cDVBgSEuPIj10YhqrRlnHrsmxK9piEfoAhJRff_Y_YQ6JEfkxgml8YZ-YZXDvs1V4ZMFV-BnA1krenQV0deJLIqtLcdaDNZvLg97bMqYdqSKMnufwPgQZwc9gkIkyDYJDl; _fcid=FC.2a3097f8-6567-34bc-dced-5337743ce9d1; _ga_Q29FZ8F7H4=GS1.1.1729079272.3.0.1729079272.0.0.0; GR_TOKEN=eyJhbGciOiJSUzI1NiIsImtpZCI6ImU2YWMzNTcyNzY3ZGUyNjE0ZmM1MTA4NjMzMDg3YTQ5MjMzMDNkM2IiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiREFSSyBTRVRTIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FHTm15eFlEOUt4Sy1zejE5VEQ3ODlDVEp1WDc0el9IQTFkeUJPVFhJXzhIPXM5Ni1jIiwiYWNjb3VudHNfdXNlcl9pZCI6OTg3ODk0NzQsInNjb3BlcyI6ImZyZWVwaWsvaW1hZ2VzIGZyZWVwaWsvdmlkZW9zIGZsYXRpY29uL3BuZyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9mYy1wcm9maWxlLXByby1yZXYxIiwiYXVkIjoiZmMtcHJvZmlsZS1wcm8tcmV2MSIsImF1dGhfdGltZSI6MTcyOTA2Mjk5OCwidXNlcl9pZCI6Im85NTBUQVFuVmhhZnNLVXNDbEl2b0dSejdDNjIiLCJzdWIiOiJvOTUwVEFRblZoYWZzS1VzQ2xJdm9HUno3QzYyIiwiaWF0IjoxNzMwMTA5NzY1LCJleHAiOjE3MzAxMTMzNjUsImVtYWlsIjoiOTAwZ2FtaW5nZ0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjExMjAxMzczMTcxNDgwMTkxNjQ0MiJdLCJlbWFpbCI6WyI5MDBnYW1pbmdnQGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.DrowNJoLZAnvkj6sBQ55LMP-z07gyKUIODvbgX2uF9PMIbBhubolo5xVsHGXZRS84VpkU1RNUhwB9KZ4YEMqbGGWKDTncXvNO_4tGXHJe_aK-OS9U2L9w3kQYVkQsxFNk5e8koQtHd34YhZFZaE0-cz6w3I-lNzkrWSqK0vEamaP_AdZY6Lhu6Vx1-L40M9MxRX0WrcW50IWpQOoB-SqY-L7xEalic6cg2K-Vc3CWvAHD4TCySF8YRyJG_2rUPKgcVp7H6ZQ163syq0BofUj0myrsE6v-Q5p-qCh0t7IJfAwFeZ9Ok1PqViwqLVp77Bvik-YNUkwnBscvKFMXEYhag; ph_phc_Rc6y1yvZwwwR09Pl9NtKBo5gzpxr1Ei4Bdbg3kC1Ihz_posthog=%7B%22distinct_id%22%3A%22148377934%22%2C%22%24sesid%22%3A%5B1730109769541%2C%220192d293-ff7c-702c-bc7a-c17aa31d41d4%22%2C1730109767548%5D%2C%22%24epp%22%3Atrue%7D; _ga_QWX66025LC=GS1.1.1730109769.4.1.1730109777.52.0.0",
    # #         "X-Xsrf-Token": "eyJpdiI6Ijh5VER4OUNoMG5ZM3Q5SVhTaFZoN1E9PSIsInZhbHVlIjoiMHlHaVdBN1FUYmxsaFlzT2hQNUVkaDJ2cG1lY29JcUtXd2UrcjU4RFNYTTVPbUthVThOZWRhZlV3ajlmZytXeG9Ib2FKUUpHZjhiakRDNS91U0ZCVHdFYXBNajdSMklaclZGb3BCNzBOcXRabzRWZ0pkU2ErSVVaanM2L1Mvb0IiLCJtYWMiOiJhZDdlOWRkMDgxZTlmYjk0YTNmMTRmOGRkZmVjYjI4MzFiNDBhMjRiMTM0YzdlNGFmNWY0NGFjN2YxOTZiOTE5IiwidGFnIjoiIn0=",
    # #         # "X-Xsrf-Token": "eyJpdiI6IlhMSU9TRG45amFVWkUvOTR3dVRVZkE9PSIsInZhbHVlIjoidU9Rb1FXZlZTdkd5SVZBdjMyell5TGM2ajFKbGFXVXh0Z1g2VUU4MkM4c2lZNWNLTG1VSGZxUjAxRDdaTk5ncENva0RzdUNuZCt4ZWxpQlp4a2taaVFGYmdqN3hVWk9aam5Ed1hpbUFkOTNKdGh1RWpDcWVUeGxzTXpscWU2SEkiLCJtYWMiOiIyOTllMjhjMzc0YjQ2ZjBjMzUyNDllY2RlOTZjYWQzMDc1Yzc0M2ZmMGM1YjQ2ZGVmN2IwYTgzNDZkNWIxM2YxIiwidGFnIjoiIn0=",
    # #     }
    # #     response = requests.post(url_to_register, headers=headers, json = data)
    # #     # print(response)
    # #     logging.info("************ response from freepik *****************")
    # #     logging.info(response.text)
    # #     logging.info(response.json())

        
    # #     id_ = 0
    # #     if response.status_code == 200:
    # #         response_data = response.json()
            
    # #         if "family" in response_data:
    # #             id_ = response_data["family"]
    # #         # if "id" in response_data:
    # #         #     id_ = response_data["id"]


    # #     url_to_fetch_images = "https://www.freepik.com/pikaso/api/render/v2?experiment=flux-schnell&lang=en&user_id=98789474"
    # #     for i in range(1, 6):
    # #         seed = random.randint(10000000, 99999999)
            
    # #         # data = {
    # #         #     "prompt": query,
    # #         #     "permuted_prompt": query,
    # #         #     "height": 832,
    # #         #     "width": 1216,
    # #         #     "num_inference_steps": 8,
    # #         #     "guidance_scale": 1.5,
    # #         #     "seed": seed,
    # #         #     "negative_prompt": "",
    # #         #     "seed_image": "",
    # #         #     "sequence": i,
    # #         #     "image_request_id": id_,
    # #         #     "should_save": True,
    # #         #     "selected_styles": {},
    # #         #     "aspect_ratio": "3:2",
    # #         #     "tool": "text-to-image",
    # #         #     "experiment": "8steps-lightning-cfg1-5",
    # #         #     "mode": "realtime",
    # #         #     "style_reference_image_strength": 1,
    # #         #     "layout_reference_image_strength": 1,
    # #         #     "user_id": 583477
    # #         # }
    # #         data = {"metadata":{"seed":seed,"index":i,"prompt":query,"width":896,"height":1152,"negativePrompt":f", overly processed, unnatural, {query}, , ","inputPrompt":query,"variationPrompt":None,"modifiers":[{"key":"photo","type":"style"}],"aspectRatio":"4:5","mode":"flux","tags":["4:5","Flux Fast","smart"],"experiment":"flux-schnell"},"family":id_,"width":896,"height":1152,"prompt":query,"seed":seed,"experiment":"flux-schnell","mode":"flux","tool":"text-to-image","aspect_ratio":"4:5","style_reference_image":"","style_reference_image_strength":0.7,"layout_reference_image":"","layout_reference_image_strength":0.7}

    # #         response = requests.post(url_to_fetch_images, headers=headers, json=data)
    # #         print(response)
    # #         logging.info("************ response from freepik *****************")    
    # #         logging.info(response)
    # #         if response.status_code == 200:
    # #             response_data = response.json()
    # #             if "image" in response_data:
    # #                 base64_image = response_data["image"]
    # #                 base64_image = "data:image/jpeg;base64,"+base64_image
    # #                 image_links.append(base64_image)
    # #                 freepik_images.append(base64_image) 
    # #             # if "results" in response_data and "output_image" in response_data["results"]:
    # #             #     base64_image = response_data["results"]["output_image"][0]
    # #             #     base64_image = "data:image/jpeg;base64,"+base64_image
    # #             #     # print("Base64 Image Data:", base64_image)
    # #             #     # 11 july 2024 sending base 64 directly to the output 
    # #             #     # image_data = base64.b64decode(base64_image)
    # #             #     # image_name = str(uuid.uuid4()) + ".jpg"
    # #             #     # with open(f'/var/www/html/images/{image_name}', 'wb') as f:
    # #             #     #     f.write(image_data)
    # #             #     # image_path = f"{Public_IP}{image_name}"
    # #             #     image_links.append(base64_image)
    # #             #     freepik_images.append(base64_image) 
    # #             else:
    # #                 print("Image data not found in the response.")
    # #         else:
    # #             print("Failed to fetch data. Status code:", response.status_code)
    # # except Exception as e:
    # #     print(e)

    
    return image_links, google_images, freepik_images, unsplash_images,Gamma_images 

@app.route('/download_images', methods=['POST'])
def download_images_endpoint():
    data = request.json
    query = data.get('query')
    image_links = []
    google_images = []
    freepik_images = []
    unsplash_images = []


    if query:
        image_links,google_images,freepik_images,unsplash_images,gamma_images = download_images(query)

    return jsonify({'image_links': image_links,'google_images':google_images,'freepik_images':freepik_images,'unsplash_images':unsplash_images,'gamma_images':gamma_images}), 200

@app.route('/download_google_images', methods=['POST']) 
def download_google_images_endpoint():
    data = request.json
    query = data.get('query')
    image_links = []
    google_images = []

    if query:
        image_links,google_images = donwload_google_images(query)

    return jsonify({'image_links': google_images}), 200

@app.route('/download_gamma_images', methods=['POST'])
def download_gamma_images_endpoint():
    data = request.json
    query = data.get('query')
    gamma_images = []

    if query:
        gamma_images = download_gamma_images(query)

    return jsonify({'gamma_images': gamma_images}), 200

@app.route('/download_unsplash_images', methods=['POST'])
def download_unsplash_images_endpoint():
    data = request.json
    query = data.get('query')
    unsplash_images = []
    image_links = []


    if query:
        image_links,unsplash_images = download_unsplash_images(query)

    return jsonify({'image_links': unsplash_images}), 200

def createWhatToReadInHTML(json_data):
    try:
        print(json_data)
        json_data = json.loads(json_data)
        res = ""
        res += """<p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 10px; line-height: 1.8; letter-spacing: inherit; color: black;"><img src="https://edurev.gumlet.io/ApplicationImages/Temp/661880_a18205fb-2870-4d67-b73d-7f833d3f5616_lg.png" style="display: block; margin: 5px auto; text-align: center; cursor: pointer; padding: 0px 1px; user-select: none; word-break: break-word; width: auto; max-width: 100%; letter-spacing: inherit;" class="fr-draggable"></p>"""
        final_json = []
        for data in json_data:
            news = data.get('heading')
            if news:
                split_news = news.split('.', 1)
                if len(split_news) > 1:
                    news = split_news[1].strip()
                else:
                    news = split_news[0].strip()
            page = data.get('page')
            page = page.replace("Page", "")
            des = data.get('des')
            des = des.split(":")[0]
            # json = {
            #     page:"8",
            #     subject:[{
            #         topic:"gs2",
            #         news:["news1","news2"]
            #     },
            #     {
            #         topic:"gs3",
            #         news:["news1","news2"]
            #     }]
            # }
            matched = False
            for final in final_json:
                if( final.get('page') == page):
                    matched = True
                    subjectMatched = False
                    for subject in final.get('subject'):
                        
                        if(subject.get('topic') == des):
                            subject.get('news').append(news)
                            subjectMatched = True
                    if(not subjectMatched):
                        final.get('subject').append({
                            "topic": des,
                            "news": [news]
                        })
                    break
            if(not matched):
                final_json.append({
                    "page": page,
                    "subject": [{
                        "topic": des,
                        "news": [news]
                    }]
                })
        for final in final_json:
            # <p><h8 style="word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 22px; letter-spacing: inherit; color: black; display: inline-block; font-weight: 900;">Page Number 8</h8></p>
            # <p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 10px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">1. UPSC Syllabus Heading:&nbsp;</strong>GS 2</p>
            # <blockquote style="border-left: 2px solid rgb(94, 53, 177); margin-left: 0px; padding-left: 5px; color: black; word-break: break-word; padding-top: 0px; padding-bottom: 0px; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit;"><p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 0px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">News:&nbsp;</strong>A good beginning but China negotiations must continue&nbsp;</p></blockquote>
            # <p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 10px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">2. UPSC Syllabus Heading:&nbsp;</strong>GS 3</p>
            # <blockquote style="border-left: 2px solid rgb(94, 53, 177); margin-left: 0px; padding-left: 5px; color: black; word-break: break-word; padding-top: 0px; padding-bottom: 0px; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit;"><p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 0px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">News:&nbsp;</strong>The issue of India’s economic growth versus emissions&nbsp;</p></blockquote>
            # <p><h8 style="word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 22px; letter-spacing: inherit; color: black; display: inline-block; font-weight: 900;">Page Number 9</h8></p>
            res += f"""<p><h8 style="word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 22px; letter-spacing: inherit; color: black; display: inline-block; font-weight: 900;">Page Number{final.get('page')}</h8></p>"""
            for j,subject in enumerate(final.get('subject')):
                initials_subject = ""
                if(len(final.get('subject')) > 1):
                    initials_subject = f"{j+1}. "
                    
                res += f"""<p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 10px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">{initials_subject}UPSC Syllabus Heading:&nbsp;</strong>{subject.get('topic')}</p>"""
                res += """<blockquote style="border-left: 2px solid rgb(94, 53, 177); margin-left: 0px; padding-left: 5px; color: black; word-break: break-word; padding-top: 0px; padding-bottom: 0px; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit;">"""
                if(len(subject.get('news')) > 1):
                    res += """<p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 0px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">News:&nbsp;</strong></p>"""
                    # <p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 0px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">i)</strong>Gamify India’s skilling initiatives&nbsp;</p>
                    # <p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 0px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">ii)</strong>India’s new digital currency&nbsp;</p>
                    for i, news in enumerate(subject.get('news')):
                        initials = ""
                        n = i+1
                        while n >0 :
                            initials += "i"
                            n-=1
                        res += f"""<p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 0px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">{initials})</strong>{news}</p>"""
                else:
                    for news in subject.get('news'):
                        res += f"""<p style="font-size: 20px; font-family: Lato, sans-serif; word-break: break-word; padding-bottom: 0px; line-height: 1.8; letter-spacing: inherit; color: black;"><strong style="font-weight: 700; word-break: break-word; line-height: 1.8; font-family: Lato, sans-serif; font-size: 20px; letter-spacing: inherit; color: black;">News:&nbsp;</strong>{news}</p>"""
                res += "</blockquote>"
        return res
    except Exception as e:
        print(e)
    
    

def getWhatToReadInJSONCA(url):
    html = getHTMLfromURL(url)
    soup = BeautifulSoup(html, 'html.parser')
    soup = soup.find('div', id='home')
    news_data = []
    for p in soup.find_all('p', style="text-align:justify"):
        if p.text.strip() == "" or p.text.strip() == "&nbsp;" or p.text.strip() == " ":
            p.decompose()
    for p in soup.find_all('p', style="margin-left:48px; text-align:justify"):
        if p.text.strip() == "" or p.text.strip() == "&nbsp;" or p.text.strip() == " ":
            p.decompose()

    with open('/root/webScrapping/test.html', 'w') as file:
        file.write(str(soup))
    # Iterate over each news block (replace the tag and class as per your HTML structure)
    all_p_tags = soup.find_all('p')
    all_ul_tags = soup.find_all('ul')
    print(len(all_p_tags))
    print(len(all_ul_tags))
    for i in range(0,len(all_p_tags)):
        if(len(all_ul_tags) <= len(all_p_tags)):
            try:
                heading = all_p_tags[i].find('span').text if all_p_tags[i].find('span') else ""
                page = all_ul_tags[i].find('li').text if all_ul_tags[i].find('li') else ""
                des = all_ul_tags[i].find_all('li')[1].text if all_ul_tags[i].find_all('li') else ""
                prelims = ""
                if(len(all_ul_tags[i].find_all('li')) > 2):
                    prelims = all_ul_tags[i].find_all('li')[2].text if all_ul_tags[i].find_all('li') else ""
                # Add the extracted data to the array
                news_data.append({
                    "heading": heading.strip(),
                    "page": page.strip(),
                    "des": des.strip(),
                    "prelims": prelims.strip()
                })
            except Exception as e:
                logging.error("error in chahal : " +str(e))


    # Convert the array to a JSON string
    news_json = json.dumps(news_data, indent=4)
    return news_json

@app.route('/getWhatToReadInJSONCA', methods=['POST'])
def getWhatToReadInJSONCA_endpoint():
    data = request.json
    url = data.get('url')
    if url:
        news_json = getWhatToReadInJSONCA(url)
        result = createWhatToReadInHTML(news_json)
        return jsonify({'news_json': news_json,'content':result}), 200
    return jsonify({'error': 'URL not provided'}), 400
# @app.route('/download_images', methods=['POST'])
# def download_images_endpoint():
#     data = request.json
#     query = data.get('query')
#     image_links = []
#     google_images = []
#     freepik_images = []
#     unsplash_images = []


#     if query:
#         image_links,google_images,freepik_images,unsplash_images = download_images(query)

#     return jsonify({'image_links': image_links,'google_images':google_images,'freepik_images':freepik_images,'unsplash_images':unsplash_images}), 200
@app.route('/missedCalls', methods=['POST'])
def saveMissCalls():
    # print(request)
    phoneNo = request.args.get('phone_no')
    # print(phoneNo)
    if not os.path.exists('/root/webScrapping/missedCalls.json'):
        with open('/root/webScrapping/api_result_json/missedCalls.json', 'w') as f:
            json.dump([], f)
    with open('/root/webScrapping/api_result_json/missedCalls.json', 'r') as f:
        phoneNumbers = json.load(f)
    if phoneNo not in phoneNumbers:
        phoneNumbers.append(phoneNo)
    with open('/root/webScrapping/api_result_json/missedCalls.json', 'w') as f:
        json.dump(phoneNumbers, f)
    return "number saved"
@app.route('/createSeparatorImprover', methods=['POST'])
def createSeparatorImprover():
    req = request.json
    data = req.get('data')
    
    data = data.replace('+', '__PLUS__')
    data = data.replace("<h7", "<h2")
    data = data.replace("</h7", "</h2")
    data = data.replace("<h8", "<h3")
    data = data.replace("</h8", "</h3")
    # logging.info("INFO :::::::::::::::::::::::: STARTING DATA   data Tag: " + data)

    # if data:
    #     with open('/home/er-ubuntu-1/webScrapping/api_result_json/separator.json', 'w') as f:
    #         json.dump(data, f)
    # check if there i any html in data using soup
    soup = BeautifulSoup(data, 'html.parser')
    # for parent_span in soup.find_all("span", class_="fr-img-wrap"):
    #     # Find and remove any nested spans with class 'fr-inner'
    #     nested_inner = parent_span.find("span", class_="fr-inner")
    #     if nested_inner:
    #         nested_inner.decompose()  # Remove the nested span from the HTML
    # allStrongTags = soup.find_all('strong')
    # for strongTag in allStrongTags:
    #     strongTagText = strongTag.get_text()
    #     # add space both sides 
    #     strongTagText = " "+strongTagText+" "
    #     # replace this text in original strong tag 
    #     strongTag.string = strongTagText
    startingText = []
    endingText = []
    allBrTags = soup.find_all('br')
    for brTag in allBrTags:
        brTag.replace_with(" ")
    for tag in soup.find_all(True):  # True fetches all tags
        if 'style' in tag.attrs:  # Check if the tag has a 'style' attribute
            if tag.name not in ['span', 'img']:  # Exclude 'span' and 'img' tags
                del tag.attrs['style']  # Remove the 'style' attribute
    for tag in soup.find_all(class_ ="span"):  # True fetches all tags
        if(tag.get('class') and 'fr-inner' in tag.get('class')):
            continue
        #if tag class is fr-new then add as it is 
        if tag.get('class') and ('fr-img-caption' in tag.get('class') or 'fr-video' in tag.get('class')):
            if 'style' in tag.attrs:  # Check if the tag has a 'style' attribute
                style_content = tag['style']
                # Split the style into individual properties
                style_properties = [prop.strip() for prop in style_content.split(';') if prop.strip()]
                
                # Filter the properties to keep only display and cursor
                filtered_styles = [
                    prop for prop in style_properties 
                    if prop.startswith('display:') or prop.startswith('cursor:') or  prop.startswith('line-height') or prop.startswith('font-size') or prop.startswith('color') or prop.startswith('text-align') or prop.startswith('margin') or  # Matches margin, margin-right, etc.
                    prop.startswith('padding') or  # Matches padding, padding-top, etc.
                    prop.startswith('height:') or
                    prop.startswith('width:')
                ]
                
                # Reassemble the style string and set it back
                if filtered_styles:
                    tag['style'] = '; '.join(filtered_styles)
                else:
                    del tag['style']  # Remove style if nothing remains
                

    # html_text = excelRun(str(soup),True)
    # soup = BeautifulSoup(html_text, 'html.parser')
    # print(data)
    processed_texts = set()
    previous_content_length = 0
    first = True
    output = ""
    startingTag = True
    endingTag = False
    
    processed_uls = set()  
    ul_content= []
    text_list = []
    processed_img_urls = set()
    rawText = ""
    processed_texts = set()
    processed_uls = set()  # Track processed 'ul' elements
    processed_tags = set()  # Track processed tags
    first = True
    h2_tags = 0
    count_p = 0
    previous_content_length = 0
    for tag in soup.descendants:
        if tag.name in ['h2']:
            h2_tags += 1
    # try:
    # if (h2_tags > 4):
    
    try:

        if soup.find_all('div') or soup.find_all("p"):
            for tag in soup.descendants:
                if tag.name in ['p', 'img','strong', 'span', 'h1', 'h2', 'h3','table', 'h4', 'h5', 'h6','h7','h8','blockquote']:
                    
                    if tag.name == 'table':
                    # Remove inline CSS and attributes from the table and its descendants
                        tag.attrs = {}
                        for element in tag.find_all(True):  # True fetches all child tags
                            if 'style' in element.attrs:
                                del element.attrs['style']  # Remove inline CSS
                            # Optionally remove other attributes if needed
                            element.attrs = {key: value for key, value in element.attrs.items() if key != 'style'}
                        
                        # Get the updated full HTML of the table
                        table_html = str(tag)
                        previous_content_length += len(table_html)
                        text_list.append(table_html)  # Add the cleaned table HTML to the text list
                        processed_texts.add(table_html)
                        # Skip processing further descendants of this table
                        continue
                    if tag.name == 'p' :
                        # Check if the <p> tag contains only a <strong> tag
                        text = str(tag)
                        if '<h2' in text or '<h3' in text or '<h7' in text or '<h8' in text:
                            continue
                        if 'fr-img-caption' in text or 'fr-video' in text:
                            continue
                        span_elements = tag.find_all('span', recursive=False)
                        
                        # Check if there is exactly one <span> inside the <p> tag
                        if len(span_elements) == 1:
                            span = span_elements[0]
                            
                            # Check if the <span> contains an <img> tag
                            if span.find('img') and 'edurev.gumlet.io/ApplicationImages/Temp' in span.find('img').get('src'):
                                continue

                        
                    if tag.name == 'span':
                        if(tag.get('class') and 'fr-inner' in tag.get('class')):
                            continue
                        
                        #if tag class is fr-new then add as it is 
                        if tag.get('class') and ('fr-img-caption' in tag.get('class') or 'fr-video' in tag.get('class')):
                            text = str(tag)
                            text_list.append(text)
                            previous_content_length += len(text)
                            processed_texts.add(text)
                            for img_tag in tag.find_all('img'):
                                img_text = str(img_tag)
                                processed_texts.add(img_text)
                                processed_img_urls.add(img_tag['src'])
                            # tag.extract()
                            continue
                        else:
                            img = tag.find('img')
                            img_url = img.get('src') if img else None
                            if img and img_url not in processed_img_urls:
                                if 'edurev.gumlet.io/ApplicationImages/Temp' in img['src']:
                                    text = str(tag)
                                    text_list.append(text)
                                    previous_content_length += len(text)
                                    processed_texts.add(text)
                                    for img_tag in tag.find_all('img'):
                                        img_text = str(img_tag)
                                        processed_texts.add(img_text)
                                        processed_img_urls.add(img_tag['src'])
                                    # tag.extract()
                                    continue
                        if("question" in tag.get_text().lower()) and tag.get_text() not in processed_texts:
                            text = str(tag)
                            text_list.append(text)
                            previous_content_length += len(text)
                            processed_texts.add(text)
                    elif tag.name == 'img':
                        if str(tag) not in processed_texts:
                            text = str(tag)
                            processed_texts.add(text)
                            text_list.append(text)
                    elif tag.name == 'blockquote':
                        logging.info("inside blockquote")
                        logging.info(tag)
                        text_list.append(str(tag))
                        for child in tag.find_all():
                            child.extract()
                    elif tag.name == "strong":
                        logging.info("inside Strong")
                        logging.info(tag)
                        if(checkExisting(tag.get_text(), processed_texts)) and str(tag) not in processed_tags:
                            processed_texts.add(str(tag.get_text()))
                            text_list.append(str(tag))
                            processed_tags.add(str(tag))
                            for child in tag.find_all():
                                processed_tags.add(str(child))
                                child.extract()
                    else:
                        
                        if tag.name == 'p':
                            strong_tags = tag.find_all('strong')
                            if len(strong_tags) == 1 and tag.get_text(strip=True) == strong_tags[0].get_text(strip=True) and str(tag) not in processed_tags:
                                text = str(tag)
                                processed_tags.add(str(strong_tags[0]))
                                # tag.extract()
                            elif len(strong_tags) >0 and tag.get_text(strip=True) != strong_tags[0].get_text(strip=True) and str(tag) not in processed_tags:
                                # text = tag.get_text()
                                text = str(tag)
                                # processed_tags.add(str(tag))
                                for child in strong_tags:
                                    processed_tags.add(str(child))
                                    child.extract()
                            else:
                                text = tag.get_text()

                            
                        else:
                            text = tag.get_text()
                        if text and (checkExisting(text, processed_texts) or  text == 'Ans.' ) == False:
                            text = re.sub(r'\s+', ' ', text)  # Clean up extra spaces
                            processed_texts.add(text)
                            rawText = text  # Save the raw text before HTML wrapping
                            text = "<" + tag.name + ">" + text + "</" + tag.name + ">"  # Wrap in HTML tag

                            # Update content length tracker
                            previous_content_length += len(text)

                            # Insert `**********` based on content length and tag type
                            if (tag.name == 'h2' or tag.name == "h3" or tag.name == 'h7' or tag.name == 'h8' ) and previous_content_length > 500:
                                text = str(tag)
                                for child in tag.find_all():
                                    if child.name == 'strong':
                                        processed_tags.add(str(child))
                                        # child.extract()
                                if endingTag:  # If endingTag is True, store in endingText
                                    endingText.append(rawText)
                                startingTag = True
                                endingTag = False  # This block marks the transition
                                next_tag = tag.find_next()  # Find the next sibling
                                if next_tag and next_tag.name == 'p':
                                    span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                    if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                        question_text = next_tag.get_text(strip=True)
                                        text += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                        processed_texts.add(question_text)
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                text = "\n ********** \n" + text
                                previous_content_length = 0

                            elif tag.name == 'p' and previous_content_length > 5000:
                                if endingTag:  # If endingTag is True, store in endingText
                                    endingText.append(rawText)
                                startingTag = True
                                endingTag = False  # This block marks the transition
                                next_tag = tag.find_next()  # Find the next sibling
                                while next_tag:
                                    if next_tag.name == 'strong':  # If the next tag is <strong>, check the next sibling
                                        next_tag_ = next_tag.find_next()
                                        processed_tags.add(str(next_tag))
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                        next_tag = next_tag_
                                    elif next_tag.name == 'p':  # If the next tag is <p>, check for the question text
                                        span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                        if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                            question_text = next_tag.get_text(strip=True)
                                            text += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                            processed_texts.add(question_text)
                                            next_tag.extract()  # Remove the <p> tag from the soup
                                            break
                                        else:
                                            next_tag = next_tag.find_next()
                                    else:
                                        break
                                        # next_tag = next_tag.find_next()
                                    
                                text += "\n ********** \n"
                                previous_content_length = 0
                                first = False
                            if (tag.name == 'h2' or tag.name == "h3" or tag.name == 'h7' or tag.name == 'h8' ):
                                for child in tag.find_all():
                                    if child.name == 'strong':
                                        processed_tags.add(str(child))
                            # If it's a starting tag, add to `startingText`
                            if startingTag:
                                if not endingTag:
                                    startingText.append(rawText)
                                    endingTag = True  # Set endingTag to True
                                    startingTag = False  # Reset startingTag

                            text_list.append(text)
                        elif text and (text == 'Ans.' ) == True:
                            text = re.sub(r'\s+', ' ', text)
                            processed_texts.add(text)
                            rawText = text  # Save the raw text before HTML wrapping
                            text = "<" + tag.name + ">" + text + "</" + tag.name + ">"  # Wrap in HTML tag

                            # Update content length tracker
                            previous_content_length += len(text)

                            # Insert `**********` based on content length and tag type
                            if (tag.name == 'h2' or tag.name == "h3" or tag.name == 'h7' or tag.name == 'h8'  ) and previous_content_length > 500:
                                if endingTag:  # If endingTag is True, store in endingText
                                    endingText.append(rawText)
                                startingTag = True
                                endingTag = False  # This block marks the transition
                                next_tag = tag.find_next()  # Find the next sibling

                                if next_tag and next_tag.name == 'p':
                                    span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                    if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                        question_text = next_tag.get_text(strip=True)
                                        text += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                        processed_texts.add(question_text)
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                text = "\n ********** \n" + text
                                previous_content_length = 0

                            elif tag.name == 'p' and previous_content_length > 5000:
                                if endingTag:  # If endingTag is True, store in endingText
                                    endingText.append(rawText)
                                startingTag = True
                                endingTag = False  # This block marks the transition
                                next_tag = tag.find_next()  # Find the next sibling
                                while next_tag:
                                    if next_tag.name == 'strong':  # If the next tag is <strong>, check the next sibling
                                        next_tag_ = next_tag.find_next()
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                        next_tag = next_tag_
                                    elif next_tag.name == 'p':  # If the next tag is <p>, check for the question text
                                        span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                        if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                            question_text = next_tag.get_text(strip=True)
                                            text += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                            processed_texts.add(question_text)
                                            next_tag.extract()  # Remove the <p> tag from the soup
                                            break  
                                        else:
                                            next_tag = next_tag.find_next()
                                    else:
                                        break
                                    
                                    
                                text = text + "\n ********** \n"
                                previous_content_length = 0
                                first = False

                            # If it's a starting tag, add to `startingText`
                            if startingTag:
                                if not endingTag:
                                    startingText.append(rawText)
                                    endingTag = True  # Set endingTag to True
                                    startingTag = False  # Reset startingTag

                            text_list.append(text)
                        else:
                            processed_texts.add(str(tag))  # Mark the tag as processed

                        # Add delimiter for specific tags
                        if tag.name == 'h2' or tag.name == "h3":
                            text_list.append("\n ")
                elif tag.name == 'ol' and id(tag) not in processed_uls:
                    # Process <ol> tags similarly to <ul>
                    processed_uls.add(id(tag))
                    ol_content = []
                    for li in tag.find_all('li'):
                        li_text = li.get_text(strip=True)
                        if li_text not in processed_texts:
                            processed_texts.add(li_text)
                            if 'style' in li.attrs:
                                del li.attrs['style']  # Remove inline styles
                            ol_content.append(str(li))
                            li.extract()
                    if ol_content:  # Add the <ol> only if it has content
                        ol_html = f"<ol>{''.join(ol_content)}</ol>"
                        if ol_html not in processed_texts:  # Avoid duplicates
                            processed_texts.add(ol_html)
                            previous_content_length += len(ol_html)
                            if previous_content_length > 5000:
                                next_tag = tag.find_next()  # Find the next sibling
                                if next_tag and next_tag.name == 'p':
                                    span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                    if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                        question_text = next_tag.get_text(strip=True)
                                        ol_html += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                        processed_texts.add(question_text)
                                        next_tag.extract()  # Remove the <p> tag from the soup
                                                                        # Check for <span> or <img> tags
                                    span_or_img = next_tag.find(lambda t: 
                                                                    (t.name == 'span' and 
                                                                    t.get('class') and 
                                                                    ('fr-img-caption' in t.get('class'))) or 
                                                                    t.name == 'img')  # Check for <span> or <img>
                                    if span_or_img:
                                        if span_or_img.name == 'span':  # Handle <span> tags
                                            span_text = str(span_or_img)
                                            ol_html += f"\n{span_text}"  # Append the <span> content
                                            processed_texts.add(span_text)
                                        elif span_or_img.name == 'img':  # Handle <img> tags
                                            img_text = str(span_or_img)
                                            ol_html += f"\n{img_text}"  # Append the <img> content
                                            processed_texts.add(img_text)
                                        next_tag.extract()  # Remove the tag from the soup
                                                
                                ol_html = ol_html+"\n ********** \n"
                                previous_content_length = 0
                                first = False
                                startingTag = True
                                endingTag = False  
                            text_list.append(ol_html)
                            
                    if startingTag:
                        if not endingTag:
                            startingText.append(rawText)
                            endingTag = True  # Set endingTag to True
                            startingTag = False  # Reset startingTag
                elif tag.name == 'ul' and id(tag) not in processed_uls:
                        # Track the processed <ul> to avoid duplicates
                        processed_uls.add(id(tag))
                        ul_content = []
                        for li in tag.find_all('li'):
                            li_text = li.get_text(strip=True)
                            if li_text not in processed_texts:
                                processed_texts.add(li_text)
                                if 'style' in li.attrs:
                                    del li.attrs['style']  # Remove inline styles
                                
                                ul_content.append(str(li))
                                li.extract()

                        if ul_content:  # Add the <ul> only if it has content
                            ul_html = f"<ul>{''.join(ul_content)}</ul>"
                            if ul_html not in processed_texts:  # Avoid duplicates
                                processed_texts.add(ul_html)
                                previous_content_length += len(ul_html)
                                if previous_content_length > 5000:
                                    next_tag = tag.find_next()  # Find the next sibling
                                    if next_tag and next_tag.name == 'p':
                                        span = next_tag.find('span', {'data-quiz_question_id': True})  # Check for <span> with attribute
                                        if span and '[Question:' in span.get_text(strip=True):  # Match the text pattern
                                            question_text = next_tag.get_text(strip=True)
                                            ul_html += f"\n{str(next_tag)}"  # Append the <p> text to the output
                                            processed_texts.add(question_text)
                                            next_tag.extract()  # Remove the <p> tag from the soup
                                        # Check for <span> or <img> tags
                                        span_or_img = next_tag.find(lambda t: 
                                                                    (t.name == 'span' and 
                                                                    t.get('class') and 
                                                                    ('fr-img-caption' in t.get('class'))) or 
                                                                    t.name == 'img')  # Check for <span> or <img>
                                        if span_or_img:
                                            if span_or_img.name == 'span':  # Handle <span> tags
                                                span_text = str(span_or_img)
                                                ul_html += f"\n{span_text}"  # Append the <span> content
                                                processed_texts.add(span_text)
                                            elif span_or_img.name == 'img':  # Handle <img> tags
                                                img_text = str(span_or_img)
                                                ul_html += f"\n{img_text}"  # Append the <img> content
                                                processed_texts.add(img_text)
                                            next_tag.extract()  # Remove the tag from the soup
                                                
                                        
                                    ul_html = ul_html+"\n ********** \n"
                                    previous_content_length = 0
                                    first = False
                                    startingTag = True
                                    endingTag = False  
                                text_list.append(ul_html)
                        if startingTag:
                            if not endingTag:
                                startingText.append(rawText)
                                endingTag = True  # Set endingTag to True
                                startingTag = False  # Reset startingTag
            result = ""
            for text in text_list:
                result += text + '\n'
            # replace any double space from the result using regex
            # result = re.sub(r'\s+', ' ', result).strip()
            
            # print(result)
            result = re.sub(r'\n+', '', result)
            result_in_parts = result.split("**********")
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
        else:
            # this case is when the text only contains text we need to add separator after 1500 characters plus a fullstop 
            max_length = 1500
            text = data
            while len(text) > max_length:
                # Find the position of the next full stop after max_length
                end_pos = text[max_length:].find('.')
                
                if end_pos != -1:
                    # Adjust end_pos to be the position in the original text
                    end_pos += max_length + 1
                else:
                    # If no full stop is found, look for the next space
                    end_pos = text[max_length:].find(' ')
                    if end_pos != -1:
                        end_pos += max_length
                    else:
                        # If no space is found, set to max_length
                        end_pos = max_length

                output += text[:end_pos] + "**********"
                text = text[end_pos:]
                
            output += text
    except Exception as e:
        print(str(e))
        output = ""
    # logging.info("INFO :::::::::::::::::::::::: BEFORE OUTPUT Tag: " + output)

    output = output.replace('__PLUS__', '+')
    logging.info("INFO :::::::::::::::::::::::: OUTPUT Tag: " + output)
    output = output.replace("<h7>", "<h2>")
    output = output.replace("</h7>", "</h2>")
    output = output.replace("<h8>", "<h3>")
    output = output.replace("</h8>", "</h3>")
    # print(output)

    return {"data":str(output),"mappingStart":startingText,"mappingEnd":endingText}


@app.route('/createSeparator', methods=['POST'])
def createSeparator():
    req = request.json
    data = req.get('data')
    output = createSepLocal(data)
    print(output)
    return output

    
def createSepLocal(data):
    data = data.replace('+', '__PLUS__')
    data = data.replace("<h7>", "<h2>")
    data = data.replace("</h7>", "</h2>")
    data = data.replace("<h8>", "<h2>")
    data = data.replace("</h8>", "</h2>")
    logging.info("INFO :::::::::::::::::::::::: STARTING DATA   data Tag: " + data)

    # if data:
    #     with open('/root/webScrapping/api_result_json/separator.json', 'w') as f:
    #         json.dump(data, f)
    # check if there i any html in data using soup
    soup = BeautifulSoup(data, 'html.parser')
    for parent_span in soup.find_all("span", class_="fr-img-wrap"):
        # Find and remove any nested spans with class 'fr-inner'
        nested_inner = parent_span.find("span", class_="fr-inner")
        if nested_inner:
            nested_inner.decompose()  # Remove the nested span from the HTML
    # allStrongTags = soup.find_all('strong')
    # for strongTag in allStrongTags:
    #     strongTagText = strongTag.get_text()
    #     # add space both sides 
    #     strongTagText = " "+strongTagText+" "
    #     # replace this text in original strong tag 
    #     strongTag.string = strongTagText
    allBrTags = soup.find_all('br')
    for brTag in allBrTags:
        brTag.replace_with(" ")
        
    # print(data)

    processed_texts = set()
    text_list = []
    previous_content_length = 0
    first = True
    output = ""
    startingTag = True
    endingTag = False
    startingText = []
    endingText = []
    if soup.find_all('div') or soup.find_all("p"):
        for tag in soup.descendants:
            if tag.name in ['p', 'img', 'span', 'h1', 'h2', 'h3', 'tr', 'td', 'h4', 'h5', 'h6', 'h7', 'h8', 'ul', 'li']:
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
                    text = tag.get_text()
                    if text and checkExisting(text, processed_texts) == False:
                        text = re.sub(r'\s+', ' ', text)  # Clean up extra spaces
                        processed_texts.add(text)
                        rawText = text  # Save the raw text before HTML wrapping
                        text = "<" + tag.name + ">" + text + "</" + tag.name + ">"  # Wrap in HTML tag

                        # Update content length tracker
                        previous_content_length += len(text)

                        # Insert `**********` based on content length and tag type
                        if (tag.name == 'h2' or tag.name == "h7") and previous_content_length > 700:
                            if endingTag:  # If endingTag is True, store in endingText
                                endingText.append(rawText)
                            startingTag = True
                            endingTag = False  # This block marks the transition
                            text = "\n ********** \n" + text
                            previous_content_length = 0

                        elif tag.name == 'p' and previous_content_length > 1500:
                            if endingTag:  # If endingTag is True, store in endingText
                                endingText.append(rawText)
                            startingTag = True
                            endingTag = False  # This block marks the transition
                            text = text + "\n ********** \n"
                            previous_content_length = 0
                            first = False

                        # If it's a starting tag, add to `startingText`
                        if startingTag:
                            if not endingTag:
                                startingText.append(rawText)
                                endingTag = True  # Set endingTag to True
                                startingTag = False  # Reset startingTag

                        text_list.append(text)

                    else:
                        processed_texts.add(str(tag))  # Mark the tag as processed

                    # Add delimiter for specific tags
                    if tag.name == 'h2' or tag.name == "h7":
                        text_list.append("\n ")

        result = ""
        for text in text_list:
            result += text + '\n'
        # replace any double space from the result using regex
        # result = re.sub(r'\s+', ' ', result).strip()
        
        # print(result)
        result = re.sub(r'\n+', '', result)
        result_in_parts = result.split("**********")
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
    else:
        # this case is when the text only contains text we need to add separator after 1500 characters plus a fullstop 
        max_length = 1500
        text = data
        while len(text) > max_length:
            # Find the position of the next full stop after max_length
            end_pos = text[max_length:].find('.')
            
            if end_pos != -1:
                # Adjust end_pos to be the position in the original text
                end_pos += max_length + 1
            else:
                # If no full stop is found, look for the next space
                end_pos = text[max_length:].find(' ')
                if end_pos != -1:
                    end_pos += max_length
                else:
                    # If no space is found, set to max_length
                    end_pos = max_length

            output += text[:end_pos] + "**********"
            text = text[end_pos:]
            
        output += text
    logging.info("INFO :::::::::::::::::::::::: BEFORE OUTPUT Tag: " + output)

    output = output.replace('__PLUS__', '+')
    logging.info("INFO :::::::::::::::::::::::: OUTPUT Tag: " + output)

    return {"data":str(output),"mappingStart":startingText,"mappingEnd":endingText}


@app.route('/getHTMLTextBasedSeparator', methods=['POST'])
def getHTMLTextBasedSeparator():
    req = request.json
    data = req.get('data')
    
    data = data.replace('+', '__PLUS__')
    data = data.replace("<h7>", "<h2>")
    data = data.replace("</h7>", "</h2>")
    data = data.replace("<h8>", "<h2>")
    data = data.replace("</h8>", "</h2>")
    logging.info("INFO :::::::::::::::::::::::: STARTING DATA   data Tag: " + data)

    # if data:
    #     with open('/root/webScrapping/api_result_json/separator.json', 'w') as f:
    #         json.dump(data, f)
    # check if there i any html in data using soup
    soup = BeautifulSoup(data, 'html.parser')
    for parent_span in soup.find_all("span", class_="fr-img-wrap"):
        # Find and remove any nested spans with class 'fr-inner'
        nested_inner = parent_span.find("span", class_="fr-inner")
        if nested_inner:
            nested_inner.decompose()  # Remove the nested span from the HTML
    # allStrongTags = soup.find_all('strong')
    # for strongTag in allStrongTags:
    #     strongTagText = strongTag.get_text()
    #     # add space both sides 
    #     strongTagText = " "+strongTagText+" "
    #     # replace this text in original strong tag 
    #     strongTag.string = strongTagText
    allBrTags = soup.find_all('br')
    for brTag in allBrTags:
        brTag.replace_with(" ")
        
    # print(data)

    processed_texts = set()
    text_list = []
    previous_content_length = 0
    first = True
    output = ""
    startingTag = True
    endingTag = False
    startingText = []
    endingText = []
    if soup.find_all('div') or soup.find_all("p"):
        for tag in soup.descendants:
            if tag.name in ['p', 'span', 'h1', 'h2', 'h3', 'tr', 'td', 'h4', 'h5', 'h6', 'h7', 'h8', 'ul', 'li']:
                if tag.name == 'span':
                    if str(tag) not in processed_texts:
                        text = str(tag.get_text())
                        processed_texts.add(text)
                        # Handle <img> tags inside <span> separately
                        for img_tag in tag.find_all('img'):
                            if str(img_tag) not in processed_texts:
                                img_text = str(img_tag)
                                processed_texts.add(img_text)
                                # text_list.append(img_text)

                elif tag.name == 'img':
                    if str(tag) not in processed_texts:
                        text = str(tag)
                        processed_texts.add(text)
                        # text_list.append(text)

                else:
                    text = tag.get_text()
                    if text and checkExisting(text, processed_texts) == False:
                        text = re.sub(r'\s+', ' ', text)  # Clean up extra spaces
                        processed_texts.add(text)
                        rawText = text  # Save the raw text before HTML wrapping
                        # text = "<" + tag.name + ">" + text + "</" + tag.name + ">"  # Wrap in HTML tag

                        # Update content length tracker
                        previous_content_length += len(text)

                        # Insert `**********` based on content length and tag type
                        if (tag.name == 'h2' or tag.name == "h7") and previous_content_length > 700:
                            if endingTag:  # If endingTag is True, store in endingText
                                endingText.append(rawText)
                            startingTag = True
                            endingTag = False  # This block marks the transition
                            text = "\n ********** \n" + text
                            previous_content_length = 0

                        elif tag.name == 'p' and previous_content_length > 1500:
                            if endingTag:  # If endingTag is True, store in endingText
                                endingText.append(rawText)
                            startingTag = True
                            endingTag = False  # This block marks the transition
                            text = text + "\n ********** \n"
                            previous_content_length = 0
                            first = False

                        # If it's a starting tag, add to `startingText`
                        if startingTag:
                            if not endingTag:
                                startingText.append(rawText)
                                endingTag = True  # Set endingTag to True
                                startingTag = False  # Reset startingTag

                        text_list.append(text)

                    else:
                        processed_texts.add(str(tag))  # Mark the tag as processed

                    # Add delimiter for specific tags
                    if tag.name == 'h2' or tag.name == "h7":
                        text_list.append("\n ")

        result = ""
        for text in text_list:
            result += text + '\n'
        # replace any double space from the result using regex
        # result = re.sub(r'\s+', ' ', result).strip()
        
        # print(result)
        result = re.sub(r'\n+', '', result)
        result_in_parts = result.split("**********")
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
    else:
        # this case is when the text only contains text we need to add separator after 1500 characters plus a fullstop 
        max_length = 1500
        text = data
        while len(text) > max_length:
            # Find the position of the next full stop after max_length
            end_pos = text[max_length:].find('.')
            
            if end_pos != -1:
                # Adjust end_pos to be the position in the original text
                end_pos += max_length + 1
            else:
                # If no full stop is found, look for the next space
                end_pos = text[max_length:].find(' ')
                if end_pos != -1:
                    end_pos += max_length
                else:
                    # If no space is found, set to max_length
                    end_pos = max_length

            output += text[:end_pos] + "**********"
            text = text[end_pos:]
            
        output += text
    logging.info("INFO :::::::::::::::::::::::: BEFORE OUTPUT Tag: " + output)

    output = output.replace('__PLUS__', '+')
    logging.info("INFO :::::::::::::::::::::::: OUTPUT Tag: " + output)

    return {"data":str(output),"mappingStart":startingText,"mappingEnd":endingText}

import schedule
import time
import subprocess
from flask import send_file
from flask import request


@app.route('/')
def hello_world():
    return 'Hello World'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=81)
