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

from removeWaterMark import download_image, remove_background_and_convert_to_bw
import datetime
import time
import json
# import spacy
import random
import openai 
from dotenv import load_dotenv
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
model = SentenceTransformer('all-MiniLM-L6-v2')


# web_path = "http://example.com/images/"
# output_dir = "assets/images"
app = Flask(__name__)

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
    html = driver.execute_script("return document.documentElement.outerHTML")

    # Get page source after JavaScript execution
    # html = driver.page_source
    # print(html)
    driver.quit()  # Close the browser
    html_text = convert_latex(str(html))
    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(html_text, 'html.parser')
    formatted_questions = {"questions":[]}
    if 'www.mockers.in/' in url:
        question_div = soup.find('ul', class_='ques-list')
        questions = question_div.find_all('li')
        for question in questions:
            '''
            <div class="px-3 mb-0 qsn-here">
                                    How many rectangles are there in the following figure? <br><img style="vertical-align: middle;" src="https://www.topcoaching.in/paid/external-images/rqsHG3jKHou1YLXY6XSKhOczZwlwOFpkgWfURy9O.png" width="122" height="109"> <br>The above question is testing
                                </div>'''
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
    # html = driver.page_source
    # print(html)
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
    # for header in soup.find_all('header'):
    #     header.extract()
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
            # ads = soup.find_all('div', class_='ER_Model_dnwldapp')
            # for ad in ads:
            #     ad.extract()

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
                    # print(text)
                    # if tag.name == 'h3':
                    #     # text = str(tag)
                    #     print(tag.get_text())
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
    if not url:
        return jsonify({'error': 'text is required'}), 400
    # try:
    all_questions = getScrollerTest(url)
        # output_text = scrapeExcel(text)
    return jsonify(all_questions), 200
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
locations_of_images = "/var/www/html/images/"
Public_IP = "http://52.139.218.113/images/"

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
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

    # Get page source after JavaScript execution
    # html = driver.page_source
    # print(html)
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
                    # try:
                    #     date_obj = datetime.datetime.strptime(date_text, "%B %d, %Y")
                    # except ValueError:
                    #     try:
                    #         date_obj = datetime.datetime.strptime(date_text, "%d %B %Y")
                    #     except ValueError:
                    #         try:
                    #             date_obj = datetime.datetime.strptime(date_text, "%d %B, %Y")
                    #         except ValueError:
                    #             print(f"Could not parse date: {date_text}")
                    #             continue

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
        for ul_element in ul_elements:
            li_elements = ul_element.find_all('li')
            for li in li_elements:
                a_element = li.find('a')
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
            [Subject name in p tag] // you observe the given input and pick from this list ["GS1/Geography" , "GS1/Indian Society",  "GS1/History & Culture",  "GS2/Polity", "GS2/Governance", "GS2/International Relations", "GS3/Economy", "GS3/Environment", "GS3/Science and Technology", "GS3/Defence & Security", "GS4/Ethics"] the subject name
            [Title Name] //just the heading of the content
            <strong>Source:</strong> [Source] //if given provided in input
            Why in news?
            [Content] // contain all the information about the current affairs
            "
            also you give all the data in HTML code only with proper formatting

            ''',
            "objective": prompt
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
                        'solutions': '[Solution]'
                        },
                    
                        ...
                    ]
                }
                Your goal is to ensure the JSON output is organized, educationally rigorous, and reflects a deep understanding of the content provided in the HTML. just give the json in output so not add anything else''',
            # "Role": "You are a proficient educational content creator specializing in summarizing and synthesizing complex information from PDF books into concise, comprehensible notes and test materials. Your expertise lies in extracting key theoretical concepts, providing clear definitions, and offering illustrative examples. When presenting information in a list, use only 'li' tags without 'p' tags inside them. Ensure the notes are well-organized and visually appealing, employing HTML tags for structure without using paragraph tags inside list items. Your goal is to optimize the learning experience for your audience by Explaining in Detail from the lengthy content into digestible formats while maintaining educational rigor. You are a content formatter specializing in converting text into HTML elements. Your expertise lies in structuring text into well-formatted HTML tags, including <li>, <ul>, and <p>, without using special characters like * or #. Your goal is to ensure that the HTML output is organized, visually appealing",
            "objective": prompt +'''
                Make questions in this statement type only and extract same level :
                    question : "Consider the following statements with reference to the Eurasian Whimbrel:

                    1. It is a wading bird endemic to the western margins of Europe.

                    2. It is classified as ‘Endangered’ under the IUCN Red List.

                    Which of the statements given above is/are correct?"
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
    
@app.route('/getCurrentAffairs', methods=['GET'])
def scrape_websites():
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
    logging.basicConfig(filename='currentAffairslogfile.log', level=logging.INFO)
    

    random_paragraphs = random.sample(results, min(len(results), 12))
    res = ""
    test = {
        'questions':[]
    }
    for paragraph in random_paragraphs:
        if len(paragraph) > 10:
            prompt = "\n Paraphrase the information given, elaborate and explain with examples wherever required. Give all points in bullet format with proper heading across (add li tag to html of bullet points). Make sure you do not miss any topic . Make sure not more than 2 headings have a HTML tag H7 and not more than 4 Subheadings have an HTML tag H8 otherwise make the headings bold. Make sure everything is paraphrased and in detail and keep the language easy to understand. Give response as a teacher but do not mention it. Please Do not promote any website other than EduRev and do not give references. Your response should be in HTML only and do not change the images HTML in given in HTML above. Again, always remember to never skip any image in the HTML of your response. Also, table should always be returned as table. Please keep same the headings given under <H2> tag and <H3> tag and don't paraphrase them."
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
                        print(question)
                        test['questions'].append(question)
                else:
                    print("data_test is not a dictionary or does not contain 'questions' key.")
            except Exception as e:
                print("Error:", str(e))
            
            res += data
            res += "\n" + "<hr>" + "\n"
            logging.info("INFO : Response: " + data)
    # Log the result

    return jsonify({'result': res, 'test': test}), 200
@app.route('/')
def hello_world():
    return 'Hello World'


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=81)
