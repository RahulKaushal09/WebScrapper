import base64
from calendar import c
from lib2to3.pytree import convert
from flask import Flask, request, jsonify
from httpx import get
import pandas as pd
from pydantic import SubclassError
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
logging.basicConfig(filename='Scrapper.log', level=logging.INFO)

model = SentenceTransformer('all-MiniLM-L6-v2')

locations_of_images = "/var/www/html/images/"
Public_IP = "https://fc.edurev.in/images/"


from flask_cors import CORS
app = Flask(__name__)
CORS(app)

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
    with open('/home/er-ubuntu-1/webScrapping/api_result_json/agricraf.json', 'w', encoding='utf-8') as f:
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
    mathjax_str = mathjax_str.replace('<br>', '')

    # Format the LaTeX delimiters properly
    mathjax_str = mathjax_str.replace(r'\$', '$')
    mathjax_str = mathjax_str.replace(r'$', '')
    # mathjax_str = mathjax_str.replace(r' ', r'\ ')

    # Wrap in MathJax inline math delimiters
    mathjax_str = f'${mathjax_str}$'
    mathjax_str = clean_latex_code(mathjax_str)
    return mathjax_str
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

        with open('/home/er-ubuntu-1/webScrapping/api_result_json/mockers.json', 'w') as f:
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
        auth_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2Njc1NDc2OGJkMTE2MGU2NTEzMTYwMTYiLCJuYW1lIjoiQWFoYW4gTWlzaHJhIiwiZW1haWwiOiJtaXNocmFhc2h3YW5pMDczQGdtYWlsLmNvbSIsInVzZXJUeXBlIjoic3R1ZGVudCIsImlhdCI6MTcxOTExNTY0NCwiZXhwIjoxNzIxNzA3NjQ0fQ.Ytp62ZuFcrxELonyzKwjy0B5KJ1m22ndu_v8E36bh-A"
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
                with open("/home/er-ubuntu-1/webScrapping/bytxt.txt", "w") as f:
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
                # if not "<img" in question and contains_latex_symbol(question):
                #     if convert_latex_to_image_for_quizeer(question, ques_img_path):
                #         question = f'<img src="https://fc.edurev.in/images/{ques_uuid}.png" alt="Question Image">'
                #     else:
                        
                #         if get_image("quizrr",question, ques_img_path):
                #             question = f'<img src="https://fc.edurev.in/images/{ques_uuid}.png" alt="Question Image">'
                        
                # elif "<img" in question and  contains_latex_symbol(question):
                    
                #     if get_image("quizrr",question, ques_img_path):
                #         question = f'<img src="https://fc.edurev.in/images/{ques_uuid}.png" alt="Question Image">'
                    
                # else:
                #     # question = question.replace("br/","br")
                #     if get_image("quizrr",question, ques_img_path):
                #         question = f'<img src="https://fc.edurev.in/images/{ques_uuid}.png" alt="Question Image">'
                    
                
                
                        # json.dump(formatted_questions, f)
                solution_ = solution_.replace("br/","br")
                if "br" in solution_:
                    with open('/home/er-ubuntu-1/webScrapping/bytxt.txt', 'w') as f:
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
                        option = formatted_options[i].replace("$","")
                    option_ = format_mathjax_html(option)
                    # formatted_options[i] = formatted_options[i].replace("br/","br")
                    if get_image("quizrr",option_, option_img_path) and len(option) != 0:
                        formatted_options[i] = f'<img src="https://fc.edurev.in/images/{option_uuid}.png" alt="Option Image">'
                    
                formatted_questions['questions'].append({
                        'question':question_,
                        'options':formatted_options,
                        'answer':answer,
                        'solution':solution_,
                        'section_name':sections_and_name[sectionId]
                    })
                # print(formatted_questions)
            previous_question_length += question_len 
        with open('/home/er-ubuntu-1/webScrapping/api_result_json/quizerr.json', 'w') as f:
            json.dump(formatted_questions, f)
        with open('/home/er-ubuntu-1/webScrapping/api_result_json/processing_quizerr.json', 'w') as f:
            json.dump(processing_formatted_question, f)
        with open('/home/er-ubuntu-1/webScrapping/api_result_json/raw_quizerr.json', 'w') as f:
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
                with open('/home/er-ubuntu-1/webScrapping/api_result_json/atpstar.json', 'w') as f:
                    json.dump(formatted_questions, f)
                break
            except Exception as e:
                print(str(e))
                logging.info("Error in getting data from atpstar.com with cookie: "+str(e))
            
        
        
    elif "https://testbook.com/" in url:
        test_id = url.split('?')[0].split('/')[-1]
        # ashwini code,sushil code
        auth_codes = [
            'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjY1Nzk5NTRmODBiN2U5MGU2NDhkN2VjZCIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNC0wNy0yMVQwNzo1ODo0NC4yMjQ1MjE4NzlaIiwiaWF0IjoiMjAyNC0wNi0yMVQwNzo1ODo0NC4yMjQ1MjE4NzlaIiwibmFtZSI6IkFzaHdhbmkiLCJlbWFpbCI6Im1pc2hyYWFzaHdhbmkwNzNAZ21haWwuY29tIiwib3JnSWQiOiIiLCJpc0xNU1VzZXIiOmZhbHNlLCJyb2xlcyI6InN0dWRlbnQifQ.DWTeumcdTJvJ7AmGzuf1bDZ9jGSatl8eEmDmfl4si4mHdF4e4nJxiQ46W-Ql4c5zB-00Wg_4Cm-OoLOVmRkJKxKlaeVOc1BXZXnUzZJkQ2gtq_QH63E5Q7jqzYr7PsI5kHkZkIqNdkn083v5wQxzZxWfvKIkUzZpTtlOwjHJgjM',
            'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3Rib29rLmNvbSIsInN1YiI6IjViZWE2NTlkNmZmNmZlMjFhNDczZmNkMiIsImF1ZCI6IlRCIiwiZXhwIjoiMjAyNC0wNy0wM1QwNDoxMzoyOC41NjkyODE5ODJaIiwiaWF0IjoiMjAyNC0wNi0wM1QwNDoxMzoyOC41NjkyODE5ODJaIiwibmFtZSI6Imx1Y2t5IiwiZW1haWwiOiJsdWNreXRhbmVqYTk5OUBnbWFpbC5jb20iLCJvcmdJZCI6IiIsImlzTE1TVXNlciI6ZmFsc2UsInJvbGVzIjoic3R1ZGVudCJ9.iCEKSYJmciL8Znd4XaEtU5Wna0v07Y9n1jMxmPKsS7ELtGqfxQhuw196hM_E4blvzoFRMoOcvgO2ZgEXWygHysFP-RJMWGN18Yhzc9g6xQtpZiI6912kgMDU5mnnzm6u31hno5J66rXukLc3bkiyDLQLnXVx8H1-4-Z9LYre0k0'
        ]
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
                print(response)
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
                            # print(question_data)
                            question_id = question['_id']
                            for option in question['en']['options']:
                                # option = html.unescape(option)
                                option = option['value']
                                option = convert_special_characters_to_html(option)
                                option = BeautifulSoup(option, 'html.parser')
                                formatted_options.append(str(option))
                            answer = answers.json()['data'][question_id]['correctOption']
                            question = convert_special_characters_to_html(question_data)
                            answer = convert_special_characters_to_html(answer)
                            solution = answers.json()['data'][question_id]['sol']['en']['value']
                            solution = convert_special_characters_to_html(solution)
                            question = BeautifulSoup(question, 'html.parser')
                            answer = BeautifulSoup(answer, 'html.parser')
                            solution = BeautifulSoup(solution, 'html.parser')
                            answer = str(answer)
                            question = str(question)
                            solution = str(solution)
                            solution = solution.replace('<img height=\"26px\" src=\"//cdn.testbook.com/resources/lms_creative_elements/in_news.png\" width=\"26px\"/>','')
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
                            
                            # Remove mjx container 
                            question = scrapeExcel(question)
                            answer = scrapeExcel(answer)
                            solution = scrapeExcel(solution)
                            for i in range(len(formatted_options)):
                                formatted_options[i] = scrapeExcel(formatted_options[i])
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
                            # print(formatted_questions)
                break
            except Exception as e:
                print(str(e))
                logging.info("auth code not working where auth code is : "+ str(auth)) 
                logging.error(str(e))
        with open ('/home/er-ubuntu-1/webScrapping/api_result_json/testbook.json','w') as f:
            json.dump(formatted_questions,f) 
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
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
    options.add_argument('--disable-extensions')  # Disable extensions 

    
   
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    

    driver.implicitly_wait(10)
    html = driver.execute_script("return document.documentElement.outerHTML")

    # Get page source after JavaScript execution
    driver.quit()  # Close the browser
    if "testbook.com" in url:
        html_text = excelRun(str(html),True)
    else:
        html_text = excelRun(str(html))
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
        if "geeksforgeeks.org" in url:
            # geeksforgeeks = True
            website = "geeksforgeeks"
        output_text = scrape_website(url,website)
        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error: "+str(e)}), 500
def sendQuestionsToP1( quizId, quizGuid, formatted_questions, marks, negMarks):
    api_to_send_questions = "https://p1.edurev.in/Tools/PDF_TO_QuizQuestions_Automation"
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
    with open("/home/er-ubuntu-1/webScrapping/api_result_json/csvToTest.json", "w") as f:
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
    marks = ""
    negMarks = ""
    if "marks" in data:
        marks = data.get("marks")
    if "negMarks" in data:
        negMarks = data.get("negMarks")
    logging.info("INFO : TEST SCROLLER quizId: " + quizId)
    logging.info("INFO : TEST SCROLLER quizGuid: " + quizGuid)
    logging.info("INFO : TEST SCROLLER url: " + url)

    if not url:
        return jsonify({'error': 'text is required'}), 400
    # try:
    all_questions = getScrollerTest(url)
    send_question = sendQuestionsToP1(quizId, quizGuid, all_questions, marks, negMarks)
    # api_to_send_questions = "https://p1.edurev.in/Tools/PDF_TO_QuizQuestions_Automation"
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
                    elif date_obj.strftime("%B %d, %Y") == today_date:
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
        try:
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
                        logging.info(formatted_date, a_element.text)
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
def getGPTResponse(prompt,i,no_of_para,weeklyCA = False):
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
        prompt_for_document = "\n Paraphrase the information given, elaborate and explain with examples wherever required. Give all points in bullet format with proper heading across (add li tag to html of bullet points). Make sure you do not miss any topic . Make sure not more than 2 headings have a HTML tag H7 and not more than 4 Subheadings have an HTML tag H8 otherwise make the headings bold. Make sure everything is paraphrased and in detail and keep the language easy to understand. Give response as a teacher but do not mention it. Please Do not promote any website other than EduRev and do not give references. Your response should be in HTML only and do not change the images HTML in given in HTML above. Again, always remember to never skip any image in the HTML of your response. Also, table should always be returned as table. Please keep same the headings given under <H2> tag and <H3> tag and don't paraphrase them. Add Heading Exactly the same as input and also Dont miss any content.\n"
        prompt_for_document_final = prompt + prompt_for_document
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
            "objective": prompt_for_document_final +"\nParaphrase the information given, elaborate and explain with examples wherever required. Give all points in bullet format with proper heading across (add li tag to html of bullet points). Make sure you do not miss any topic . Make sure not more than 2 headings have a HTML tag H7 and not more than 4 Subheadings have an HTML tag H8 otherwise make the headings bold. Make sure everything is paraphrased and in detail and keep the language easy to understand. Give response as a teacher but do not mention it. Please Do not promote any website other than EduRev and do not give references. Your response should be in HTML only and do not change the images HTML in given in HTML above. Again, always remember to never skip any image in the HTML of your response. Also, table should always be returned as table. Please keep same the headings given under <H2> tag and <H3> tag and don't paraphrase them."
        }
        

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
        # logging.info("FOR test Role: "+role)
        # logging.info("FOR test Prompt: "+prompt_)
        # response_test = client.chat.completions.create(
        #     model=gpt_model,
        #     messages=[
        #         {
        #             "role": "system",
        #             "content": "You are ChatGPT, a large language model trained by OpenAI, based on the GPT-3.5/GPT-4o architecture. Knowledge cutoff: 2021-09 Current date: "+formatted_date
        #         },
        #         {
        #             "role": "user",
        #             "content": json.dumps(user_prompt_test)
        #         }
        #     ],
        #     max_tokens=4096,
        #     temperature=0.7
        # )

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


#         if response_test.choices:
#             # Access the content from the response
#             data_res_test = response_test.choices[0].message.content
#             data_res_test = str(data_res_test)
#             logging.info("INFO : Response NORMAL test: " + data_res_test)
#             prompt_for_single_question = """
#             Extract the information from the above HTML content and provide the JSON format for the questions, options, answers, and solutions. Each question must be formatted according to the following example:
            
#             {
#                 "questions": 
#                 [
#                     {
#                     "question": "<p>Question: Which of the following is an example of endothermic reaction?</p>",
#                     "options": [
#                         "Option A: <p>Example1</p>",
#                         "Option B: <p>Example2</p>",
#                         "Option C: <p>Example3</p>",
#                         "Option D: <p>Example4</p>"
#                     ],
#                     "answer": "<p>Answer: Option A</p>",
#                     "solution": "<p>Solution:</p>"
#                     }
#                 ]
#             }


#                     Ensure to:
#                     1. Extract each question, all 4 options, answer, and solution from the given HTML at the start. 
#                     2. Format each extracted part into JSON as shown in the example.
#                     3. Preserve the <img> tags and any other HTML tags within the content.
#                     4. Provide the output strictly in JSON format without any additional text or formatting markers.
#                     5. Carefully understand the html at the top and make sure it is extracted in question, answer, options and solution with none of these fields being blank. 
#                     6. Always give Option A, Option B, Option C, Option D only in the answer, Dont right full answer.
#                     7. Always give only question in question along with statements and pairs if provided and option in options 
                    
# """
#             prompt_for_multiple_question = """

#                     Extract the information from the above HTML content and provide the JSON format for the questions, options, answers, and solutions. Each question must be formatted according to the following example:
#             {
#                 "questions": [
#                     {
#                     "question": "<p>Question: Which of the following is an example of endothermic reaction?</p>",
#                     "options": [
#                         "Option A: <p>Example1</p>",
#                         "Option B: <p>Example2</p>",
#                         "Option C: <p>Example3</p>",
#                         "Option D: <p>Example4</p>"
#                     ],
#                     "answer": "<p>Answer: Option A</p>",
#                     "solution": "<p>Solution:</p>"
#                     },
#                     {
#                     "question": "<p>Question: Which of the following is an example of endothermic reaction?</p>",
#                     "options": [
#                         "Option A: <p>Example1</p>",
#                         "Option B: <p>Example2</p>",
#                         "Option C: <p>Example3</p>",
#                         "Option D: <p>Example4</p>"
#                     ],
#                     "answer": "<p>Answer: Option A</p>",
#                     "solution": "<p>Solution: </p>"
#                     }
#                 ]
#             }


#                     Ensure to:
#                     1. Extract each question, all 4 options, answer, and solution from the given HTML at the start. 
#                     2. Format each extracted part into JSON as shown in the example.
#                     3. Preserve the <img> tags and any other HTML tags within the content.
#                     4. Provide the output strictly in JSON format without any additional text or formatting markers.
#                     5. Carefully understand the html at the top and make sure it is extracted in question, answer, options and solution with none of these fields being blank. 
#                     6. Always give Option A, Option B, Option C, Option D only in the answer, Dont right full answer.
#                     7. Always give only question in question and option in options 

#                     """
#             if number_of_question_per_paragraph == 1:
#                 prompt_json = data_res_test + prompt_for_single_question
#             else:
#                 prompt_json = data_res_test+prompt_for_multiple_question
                
#             user_prompt_json = {
                        
#                         "Role": "You are an expert HTML formatter specializing in converting text into well-structured HTML code for educational purposes. Your task is to Understand the given input and fetch questions, options , correct answer and the solution perfectly and  format each question, its options, the correct answer, and the solution in a JSON as provided in the prompt. if the content provided is scrape and not much of releveant to make a question you give all the elements of the JSON in empty ",
#                         "objective": prompt_json
#                     }
#             response_test_json = client.chat.completions.create(
#                     model="gpt-3.5-turbo",
#                     messages=[
#                         {
#                             "role": "system",
#                             "content": "You are ChatGPT, a large language model trained by OpenAI, based on the GPT-3.5 architecture. Knowledge cutoff: 2021-09 Current date: "+formatted_date
#                         },
#                         {
#                             "role": "user",
#                             "content": json.dumps(user_prompt_json)
#                         }
#                     ],
#                     max_tokens=4096,
#                     temperature=0.3
#                 )
#                 # Print the response
#             if response_test_json.choices:
#                 # Access the content from the response
#                 data_res_json = response_test_json.choices[0].message.content
#             # print(content)
#             data_res_json = str(data_res_json)
#             logging.info("INFO : Response test: " + data_res_json)
#             if "```json" in data_res_json:
#                 data_res_json = data_res_json.split("```json")[1]
#                 data_res_json = data_res_json.split("```")[0]
#                 # data_res_test = json.loads(data_res_test)
#                 try:
#                     data_res_json = json.loads(data_res_json)        
#                 except json.JSONDecodeError as e:
#                     logging.info(f"ERROR : JSON decoding error: {e}")
#         else:
#             logging.info("ERROR : No test response generated.")
#             # return data_res 
        # right_ans = False
        # if type_question == "statement":
        #     logging.info("sending to get right answer with data :" + str(data_res_json))
        #     right_ans = True
        #     data_res_json_after_right_answer = get_right_answer(data_res_json)
        # if right_ans:
        #     return data_res , data_res_json_after_right_answer
        # else:
        #     return data_res , data_res_json
        # logging.info("INFO : Response test after cleaning: " + str(data_res_json))
        
        # data_res = str(data_res) 
        # if '<body>' in data_res:
        #     data_res = data_res.split('<body>')[1].split('</body>')[0]
        # # return data_res 
        # return data_res , data_res_json
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
                file_path = '/home/er-ubuntu-1/webScrapping/currentAffairs/MonthlyCA_'+today_date.strftime("%Y-%m-%d")+'.txt'
                with open(file_path, 'w') as f:
                    f.write(result)
                logging.info("INFO : UserPrompt: " + data_)
                once = True
                try:
                    # data , data_test = getGPTResponse(data_,para_number_for_prompt_role,total_para,True)
                    data  = getGPTResponse(data_,para_number_for_prompt_role,total_para,True)
                    # para_number_for_prompt_role+=1
                    # try:
                    #     print("Type of data_test:", type(data_test))
                    #     if type(data_test) == str:
                    #         data_test = json.loads(data_test)
                    #         print('converted to json')                    
                            

                    #     print("Content of data_test:", data_test)
                    #     if isinstance(data_test, dict) and 'questions' in data_test:
                    #         for question in data_test['questions']:
                    #             # print(question)
                    #             test['questions'].append(question)
                    #     else:
                    #         test['questions'].append(data_test)
                    #         print("data_test is not a dictionary or does not contain 'questions' key. therefore added to test directly as a question")
                    # except Exception as e:
                    #     print("Error:", str(e))
                    
                    res += data
                    res += "\n" + "<hr>" + "\n"
                    logging.info("INFO : Response: " + data)
                    # for question in test['questions']:
                    #     question_patterns = [r"Question \d+:", r"Question:"]
                    #     answer_patterns = [r"ANSWER", r"ANS", r"ANSWEROPTION", r"Answer:"]
                    #     solution_patterns = [r"Solution:"]
                        
                    #     question["question"] = clean_text(question["question"], question_patterns)
                    #     question["answer"] = clean_text(question["answer"], answer_patterns)
                    #     question["solution"] = clean_text(question["solution"], solution_patterns)
                    #     question["answer"] = question["answer"].replace("OPTION","")
                    #     question["answer"] = question["answer"].replace("Option","")
                    #     question["answer"] = question["answer"].replace("option","")
                    #     option_patterns = [r"Option [A-Z]:", r"^\(\d+\)|^\([A-Z]\)", r"\([a-z]\):",r"\([a-z]\)",r"\([A-Z]\)"]
                    #     for i, option in enumerate(question["options"]):
                    #         question["options"][i] = clean_text(option, option_patterns)
                            # print(question["options"][i])
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
    api_to_send_current_affairs = "https://p1.edurev.in/Tools/CreateCurrentAffairsDocument"
    # details for weekly CA
    # courseId = ""
    # subCourseId = ""
    # result = {'result': res, 'test': test,'courseId':courseId,'subCourseId':subCourseId,'marks':marks,'negMarks':negMarks, 'quiz_title':quiz_title, 'doc_title':doc_title}
    result = {'result': res, 'courseId':courseId,'subCourseId':subCourseId,'marks':marks,'negMarks':negMarks,  'doc_title':doc_title}
    logging.info("INFO : Sending monthly Current Affair Result to API : " + api_to_send_current_affairs)
    print(result)
    logging.info("************ result send is *****************")
    logging.info(result)
    with open("/home/er-ubuntu-1/webScrapping/api_result_json/weeklyCA.json", "w") as outfile:
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
        print(row['Links'])
        result = ""
        url = row['Links']
        data_ = scrape_website_current_affair(url)
        if len(data_) > 10:
            result += "\n**********\n"  + data_
            today_date = datetime.datetime.now()
            file_path = '/home/er-ubuntu-1/webScrapping/currentAffairs/WeeklyCA_'+today_date.strftime("%Y-%m-%d")+'.txt'
            with open(file_path, 'w') as f:
                f.write(result)
            logging.info("INFO : UserPrompt: " + data_)
            once = True
            try:
                data = getGPTResponse(data_,para_number_for_prompt_role,total_para,True)
                # para_number_for_prompt_role+=1
                # try:
                #     print("Type of data_test:", type(data_test))
                #     if type(data_test) == str:
                #         data_test = json.loads(data_test)
                #         print('converted to json')                    
                        

                #     print("Content of data_test:", data_test)
                #     if isinstance(data_test, dict) and 'questions' in data_test:
                #         for question in data_test['questions']:
                #             # print(question)
                #             test['questions'].append(question)
                #     else:
                #         test['questions'].append(data_test)
                #         print("data_test is not a dictionary or does not contain 'questions' key. therefore added to test directly as a question")
                # except Exception as e:
                #     print("Error:", str(e))
                
                res += data
                res += "\n" + "<hr>" + "\n"
                logging.info("INFO : Response: " + data)
                # for question in test['questions']:
                #     question_patterns = [r"Question \d+:", r"Question:"]
                #     answer_patterns = [r"ANSWER", r"ANS", r"ANSWEROPTION", r"Answer:"]
                #     solution_patterns = [r"Solution:"]
                    
                #     question["question"] = clean_text(question["question"], question_patterns)
                #     question["answer"] = clean_text(question["answer"], answer_patterns)
                #     question["solution"] = clean_text(question["solution"], solution_patterns)
                    
                #     option_patterns = [r"Option [A-Z]:", r"^\(\d+\)|^\([A-Z]\)", r"\([a-z]\):",r"\([a-z]\)",r"\([A-Z]\)"]
                #     for i, option in enumerate(question["options"]):
                #         question["options"][i] = clean_text(option, option_patterns)
                #         # print(question["options"][i])
            except Exception as e:
                print("Error while getting GPT Response: "+str(e))
                if once:
                    once = False
                    logging.info("trying again......")
                    data = getGPTResponse(data_,para_number_for_prompt_role,total_para,True)
    # Log the result
    api_to_send_current_affairs = "https://p1.edurev.in/Tools/CreateCurrentAffairsDocument"
    # details for weekly CA
    # updated for july
    courseId = "12112"
    subCourseId = "86752"
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
    with open("/home/er-ubuntu-1/webScrapping/api_result_json/weeklyCA.json", "w") as outfile:
        json.dump(result, outfile)
    send_current_affairs = requests.post(api_to_send_current_affairs, json=result)
    print(send_current_affairs.status_code)
    if send_current_affairs.status_code == 200:
        print("Current Affairs sent successfully!")
        logging.info("************ weekly Current Affairs sent successfully! *****************")
        return jsonify({'Message':"weekly Current Affairs Sent!!!!!!!!!!!  ->   Check Your Mail Please"}), 200
    else:
        return jsonify({'Message':"Error While Sending weekly Current Affairs !!!!!!!  ->   Create Yourself For Today"}), 400
        

    

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
    para_number_for_prompt_role = 0
    total_para = len(random_paragraphs)
    
    for paragraph in random_paragraphs:
        if len(paragraph) > 10:
            
            logging.info("INFO : UserPrompt: " + paragraph)
            once = True
            try:
                data  = getGPTResponse(paragraph,para_number_for_prompt_role,total_para)
                # para_number_for_prompt_role+=1
                # # data  = getGPTResponse(paragraph)
                # try:
                #     print("Type of data_test:", type(data_test))
                #     if type(data_test) == str:
                #         data_test = json.loads(data_test)
                #         print('converted to json')                    
                        

                #     print("Content of data_test:", data_test)
                #     if isinstance(data_test, dict) and 'questions' in data_test:
                #         for question in data_test['questions']:
                #             # print(question)
                #             test['questions'].append(question)
                #     else:
                #         test['questions'].append(data_test)
                #         print("data_test is not a dictionary or does not contain 'questions' key. therefore added to test directly as a question")
                # except Exception as e:
                #     print("Error:", str(e))
                
                res += data
                res += "\n" + "<hr>" + "\n"
                logging.info("INFO : Response: " + data)
                # for question in test['questions']:
                #     question_patterns = [r"Question \d+:", r"Question:"]
                #     answer_patterns = [r"ANSWER", r"ANS", r"ANSWEROPTION", r"Answer:"]
                #     solution_patterns = [r"Solution:"]
                    
                #     question["question"] = clean_text(question["question"], question_patterns)
                #     question["answer"] = clean_text(question["answer"], answer_patterns)
                #     question["solution"] = clean_text(question["solution"], solution_patterns)
                    
                #     option_patterns = [r"Option [A-Z]:", r"^\(\d+\)|^\([A-Z]\)", r"\([a-z]\):",r"\([a-z]\)",r"\([A-Z]\)"]
                #     for i, option in enumerate(question["options"]):
                #         question["options"][i] = clean_text(option, option_patterns)
                #         # print(question["options"][i])
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
    api_to_send_current_affairs = "https://p1.edurev.in/Tools/CreateCurrentAffairsDocument"
    # details for daily CA  
    courseId = "12112"
    subCourseId = "86529"
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
        


def sanitize_filename(filename):
    # Remove invalid characters
    return re.sub(r'[<>:"/\\|?*\n]', '', filename)

def download_images(query):
    # IMAGES FROM GOOGLE
    sanitized_query = sanitize_filename(query)
    image_links = []
    google_crawler = GoogleImageCrawler(storage={'root_dir': '/home/er-ubuntu-1/webScrapping/googleImagesDownload/'})
    google_crawler.crawl(keyword=sanitized_query, max_num=2)
    for filename in os.listdir('/home/er-ubuntu-1/webScrapping/googleImagesDownload/'):
        # if filename.endswith('.jpg'):
        # convert to base64 each image 
        base_64_image = base64.b64encode(open(f'/home/er-ubuntu-1/webScrapping/googleImagesDownload/{filename}', 'rb').read())
        base64_image = "data:image/jpeg;base64," + base_64_image.decode("utf-8")
        os.remove(f'/home/er-ubuntu-1/webScrapping/googleImagesDownload/{filename}')
        # image_name = str(uuid.uuid4()) + ".jpg"
        # os.rename(f'/home/er-ubuntu-1/webScrapping/googleImagesDownload/{filename}', f'/var/www/html/images/{image_name}')
        # image_path = f"{Public_IP}{image_name}"
        image_links.append(base64_image)
    # IMAGES FROM FREEPIK
    url_to_register = "https://www.freepik.com/pikaso/api/text-to-image/create-request?lang=en&cacheBuster=2"

    Cookie = ("XSRF-TOKEN=eyJpdiI6IndJZ0JsMm5FRlJuTFNEcmIrUUFIUmc9PSIsInZhbHVlIjoiL1BvYzBsOURuYkpWWnVpNWpmbzRrb3N5bFpieVRySi9zMFg0eXd0SVlFMFk3YXlQclhPUWJpREZXc0JDZTU3MGlZMVU5Wm1XL1hLSjRtMkZOdEpQWjM5OXg4Q0psTW5heTlOTG1tZ3Z5enJCa29CWCtsNjRZNHVNZTI5eXM0MXUiLCJtYWMiOiIzZjJjODY2OGMyZWFjNzhjMzlkODRkOTcyZGE4YzgyMTcwMTdkMGZiNWE3NjI1OWFjN2UzZmZiM2RiNmY5YzA5IiwidGFnIjoiIn0%3D; pikaso_session=eyJpdiI6ImEyL3NIYmtOZGJsNHVkbTlDU3A2Umc9PSIsInZhbHVlIjoibWEwdUJEaVRrRDE0eEZsQmc0cmUrWXFXeXQzRFJDRy9XTHFmbFQ1a1hqZkxwMjJXc2FzMUdBWnRkNFdKNlBIMks2eFNzYi9TMGhLaVVWR1d3aFd1V0c1TGphY3I1eGNzeXkycnlvVE9EWGFtenUxdEEyQnBKaG5GOHIxb0VYd3MiLCJtYWMiOiIxOTk0MThmZjgyZGYyMTQzMTMxMzlkMjgxMzFkMjI0ODcxYzk4NDFmYzcwOTM0YTQyZTVlZDZkZDQzYWY2MjkwIiwidGFnIjoiIn0%3D; _gcl_au=1.1.730307295.1718188112; ads-tag=b; _ga=GA1.1.687132118.1718188113; _cs_ex=1709818470; _cs_c=0; OptanonAlertBoxClosed=2024-06-12T10:28:33.670Z; GR_TOKEN=eyJhbGciOiJSUzI1NiIsImtpZCI6ImRmOGIxNTFiY2Q5MGQ1YjMwMjBlNTNhMzYyZTRiMzA3NTYzMzdhNjEiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSGFyZGlrIEppbmRhbCIsInBpY3R1cmUiOiJodHRwczovL2F2YXRhci5jZG5way5uZXQvNDk2MTY0MjItMjExMTI4MDgwMTAwLmpwZyIsImFjY291bnRzX3VzZXJfaWQiOjQ5NjE2NDIyLCJzY29wZXMiOiJmcmVlcGlrL2ltYWdlcyBmcmVlcGlrL3ZpZGVvcyBmbGF0aWNvbi9wbmcgZnJlZXBpay9pbWFnZXMvcHJlbWl1bSBmcmVlcGlrL3ZpZGVvcy9wcmVtaXVtIGZsYXRpY29uL3N2ZyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9mYy1wcm9maWxlLXByby1yZXYxIiwiYXVkIjoiZmMtcHJvZmlsZS1wcm8tcmV2MSIsImF1dGhfdGltZSI6MTcxODE4OTQzMCwidXNlcl9pZCI6Ijg1ZGI4Nzk1YWUyODRjZGI4MDM0MTJkZDdhN2ExODE1Iiwic3ViIjoiODVkYjg3OTVhZTI4NGNkYjgwMzQxMmRkN2E3YTE4MTUiLCJpYXQiOjE3MTgxODk0MzAsImV4cCI6MTcxODE5MzAzMCwiZW1haWwiOiJoYXJkaWtqaW5kYWxAZWR1cmV2LmluIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDc0Nzg1ODM5MjIxMTU5MzI2NDMiXSwiZW1haWwiOlsiaGFyZGlramluZGFsQGVkdXJldi5pbiJdfSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.WMCn_lXRzUYfrvZVasIvQxh8c75f9qu73qPcIYGcoEteVa0mOljTlmaJNIIqb8xUjv9lZmj-Lmhx03aaP5i3ejZgKPSEM-JySj8bWbgSboVJXzRLOr5FX-mhRaWxWujkVqnbLaukLjzOQ7fjzK2v6g2uxiaXvnsrEpaCGwRiZXqTj5gHxyAlmAlWyW73VZxOxOVljqVVEEsMMgl8IG6GaDLY02MktWbm81KzfDex2pWqG7cXBSPgQTRRdh6LnAob7qFPHdsi81LeDQ198FSjPs6qX3yVjO8FAsP2kV-pfES0CjOrcFthlRyaTi3PInaWb_CfDAS83g2wizzYgZdN1Q; GR_REFRESH=AMf-vBzyLZC1yAVp5vgCvG-W6Te7RdJdUukraJmXfhdud2VHg-kWqs-focaEeFKZJi-l1BCaMWCo2pDBu_iQAEnlXwv1gCZDtr6Xd86Y3OqBUf_CxXhLNy3kmaQzII8zIf-4ON1FreB-PQI4D93BkPKZxFJEvwUKzdAjAdLS5htmkqaeCxQAMFQBDaWEzlRaHCCzkLYAxZGt; _fc=FC.700669b7-addc-6731-f954-0499f36f49ee; _fcid=FC.700669b7-addc-6731-f954-0499f36f49ee; FP_MBL=1; GRID=49616422; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Jun+12+2024+16%3A21%3A57+GMT%2B0530+(India+Standard+Time)&version=202401.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CC0005%3A1&geolocation=IN%3BCH&AwaitingReconsent=false; ABTastySession=mrasn=&lp=https%253A%252F%252Fwww.freepik.com%252Fapi; ABTasty=uid=ww04er0x8zq86v80&fst=1718188112547&pst=-1&cst=1718188112547&ns=1&pvt=8&pvis=8&th=; csrf_freepik=b90d65d74b8ee8fb02b5ea92ed0d277c; _hjSessionUser_1331604=eyJpZCI6IjA4MWYyMGFkLTQ2MmQtNWUxZC04M2QwLTc4MzVlYTVkMTA5ZiIsImNyZWF0ZWQiOjE3MTgxODk1MTg1MzYsImV4aXN0aW5nIjpmYWxzZX0=; _hjSession_1331604=eyJpZCI6IjA4Yjk0YzMyLTRjYzMtNGY2ZC04NmRlLWQwM2E4OWViNTM2ZCIsImMiOjE3MTgxODk1MTg1MzgsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=; _hjHasCachedUserAttributes=true; __gads=ID=db56d1d0d311f2d1:T=1718189520:RT=1718189520:S=ALNI_MZDSV6XCBAfOLakpP2qMUdeIiNW0A; __gpi=UID=00000e48ac1ca705:T=1718189520:RT=1718189520:S=ALNI_MY7BoTr9OIVSJvYZANl7RQ2_PL-mQ; __eoi=ID=6fda754bad090ba2:T=1718189520:RT=1718189520:S=AA-AfjblwLbuydwQRMLRirVsVBXN; _cc_id=445b0078bf58440aa386dd6e44b74197; panoramaId_expiry=1718275921667; _au_1d=AU1D-0100-001718189523-JFUE3VRD-FISJ; cto_bundle=E3rCol91VUg1SHM3WFpYeGIxSm05Qnk1Vm1qZ3B4MDNWVHZUaUtvZHJ2Z2VRJTJGYXR2OEZBRHlZOHV3Tmk0RFA5bjVGbm9KSENCTlJDU0VjdE9kSmRkSiUyRkxqSWU0TkNSUjJBTlBCaEJmMXEyRlR2N2R3ZGJOZkJ3VEdhYXR0RnIlMkIlMkZ3MjBrcyUyRkt0WXp1RXZxeWZ6YTFWRDk1STFnanRIVUxRaHdkNGdFenMyYktKWlFBMFM2S3IzdXpTUGtTdzVKYzJtQVQ0c1JCMTkwaFpxU3FJS1o4QlZuUmJ0JTJGYXJvMHVnR2twY1FqaktvJTJCQnclMkZsNCUzRA; ab.storage.userId.35bcbbc0-d0b5-4e6c-9926-dfe1d0cd06ab=g%3A49616422%7Ce%3Aundefined%7Cc%3A1718189526058%7Cl%3A1718189526062; ab.storage.deviceId.35bcbbc0-d0b5-4e6c-9926-dfe1d0cd06ab=g%3A3a8f2c84-9038-32c2-7ad0-29a065430b1f%7Ce%3Aundefined%7Cc%3A1718189526063%7Cl%3A1718189526063; ab.storage.sessionId.35bcbbc0-d0b5-4e6c-9926-dfe1d0cd06ab=g%3Ab24e5449-4676-d581-b316-1c8ecbb7e67d%7Ce%3A1718225595036%7Cc%3A1718189526061%7Cl%3A1718189595036; _ga_18B6QPTJPC=GS1.1.1718189526.1.1.1718189595.58.0.0; ph_phc_Rc6y1yvZwwwR09Pl9NtKBo5gzpxr1Ei4Bdbg3kC1Ihz_posthog=%7B%22distinct_id%22%3A%22583477%22%2C%22%24sesid%22%3A%5B1718189604802%2C%2201900c13-894c-7a18-acf9-a28463a1e0c1%22%2C1718189525324%5D%2C%22%24epp%22%3Atrue%7D; _ga_QWX66025LC=GS1.1.1718188112.1.1.1718189604.49.0.0")
    data = {
        "prompt": query,
        "layout_reference_image": None,
        "width": 1216,
        "height": 832
    }
    headers = {
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cookie":Cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "X-Xsrf-Token": "eyJpdiI6IjIzbGNOSVZpZElzUWp2UW5iTlBEOWc9PSIsInZhbHVlIjoiY3FZb1JvU0xDK2VmL1RYVmhYeWluTVdNRGpFY25GMk5zeEhURzF2Z0paNnZrdC8yMkwyU1lEL2RDMDZEYklEUWVDUGQwNkRYZjVZUnlKb0IwVjZhNGlsWS9DZHFxb291OE1Fbk5odWZyUmtNVUtHSnFKUmxXM1BSWVM1T3hCQzUiLCJtYWMiOiIyZjgzNzFmZjUxYmM2YjFjNzgyMjdhNjdkYTE2MDRiYzE1NWU4MTkwZTE1MmQzOGJkYzQ1MGE2MzhlZmFlN2JkIiwidGFnIjoiIn0="
    }
    response = requests.post(url_to_register, headers=headers, json = data)
    # print(response)
    id_ = 0
    if response.status_code == 200:
        response_data = response.json()
        if "id" in response_data:
            id_ = response_data["id"]


    url_to_fetch_images = "https://www.freepik.com/pikaso/api/render"
    for i in range(1, 6):
        seed = random.randint(10000, 99999)
        
        data = {
            "prompt": query,
            "permuted_prompt": query,
            "height": 832,
            "width": 1216,
            "num_inference_steps": 8,
            "guidance_scale": 1.5,
            "seed": seed,
            "negative_prompt": "",
            "seed_image": "",
            "sequence": i,
            "image_request_id": id_,
            "should_save": True,
            "selected_styles": {},
            "aspect_ratio": "3:2",
            "tool": "text-to-image",
            "experiment": "8steps-lightning-cfg1-5",
            "mode": "realtime",
            "style_reference_image_strength": 1,
            "layout_reference_image_strength": 1,
            "user_id": 583477
        }
        response = requests.post(url_to_fetch_images, headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            if "results" in response_data and "output_image" in response_data["results"]:
                base64_image = response_data["results"]["output_image"][0]
                base64_image = "data:image/jpeg;base64,"+base64_image
                # print("Base64 Image Data:", base64_image)
                # 11 july 2024 sending base 64 directly to the output 
                # image_data = base64.b64decode(base64_image)
                # image_name = str(uuid.uuid4()) + ".jpg"
                # with open(f'/var/www/html/images/{image_name}', 'wb') as f:
                #     f.write(image_data)
                # image_path = f"{Public_IP}{image_name}"
                image_links.append(base64_image)
            else:
                print("Image data not found in the response.")
        else:
            print("Failed to fetch data. Status code:", response.status_code)
    # UNSPLASH PICTURES
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
                    image_links.append(size['uri'])
                    break
            
            i += 1

    return image_links

@app.route('/download_images', methods=['POST'])
def download_images_endpoint():
    data = request.json
    query = data.get('query')
    image_links = []

    if query:
        image_links = download_images(query)

    return jsonify({'image_links': image_links}), 200
@app.route('/missedCalls', methods=['POST'])
def saveMissCalls():
    # print(request)
    phoneNo = request.args.get('phone_no')
    # print(phoneNo)
    if not os.path.exists('/home/er-ubuntu-1/webScrapping/missedCalls.json'):
        with open('/home/er-ubuntu-1/webScrapping/api_result_json/missedCalls.json', 'w') as f:
            json.dump([], f)
    with open('/home/er-ubuntu-1/webScrapping/api_result_json/missedCalls.json', 'r') as f:
        phoneNumbers = json.load(f)
    if phoneNo not in phoneNumbers:
        phoneNumbers.append(phoneNo)
    with open('/home/er-ubuntu-1/webScrapping/api_result_json/missedCalls.json', 'w') as f:
        json.dump(phoneNumbers, f)
    return "number saved"
@app.route('/createSeparator', methods=['POST'])
def createSeparator():
    req = request.json
    data = req.get('data')
    # if data:
    #     with open('/home/er-ubuntu-1/webScrapping/api_result_json/separator.json', 'w') as f:
    #         json.dump(data, f)
    # check if there i any html in data using soup
    soup = BeautifulSoup(data, 'html.parser')
    processed_texts = set()
    text_list = []
    previous_content_length = 0
    first = True
    output = ""

    if soup.find_all('div') or soup.find_all("p"):
        # html present /
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
    return {"data":output}

    
import schedule
import time
import subprocess
from flask import send_file
from flask import request


@app.route('/')
def hello_world():
    return 'Hello World'


if __name__ == '__main__':
    # scrape_websites_current_affair()
    # schedule.every().day.at("11:30").do(scrape_websites_current_affair)
    app.run(host="0.0.0.0", port=81)
