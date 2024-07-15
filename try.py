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

def scrape_website_current_affair(url):
    # Setup Selenium WebDriver
    print(url)
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
        # formatted_date = f"{get_ordinal(today_date.day)} {today_date.strftime('%B %Y')}"  # Format like '22nd May 2024'
        # Find the link for today's date
        ul_elements = soup.find_all('ul', class_='lcp_catlist')
        result = ""
        print(ul_elements)
        for ul_element in ul_elements:
            li_elements = ul_element.find_all('li')
            for li in li_elements:
                a_element = li.find('a')
                # print(formatted_date, a_element.text)
                # if a_element and formatted_date in a_element.text:
                    # result += scrape_website_iasbaba(a_element['href'])
        return result
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
        div_elements = soup.find_all('div', class_="news-block")
        
        result = ""
        for div in div_elements:
            date_div = div.find('h1', class_="date-strip").text
            date_div = date_div[1:]
            # print(date_div)
            today_date = datetime.datetime.now()  # Format like '22 May 2024'
            # formatted_date = f"{get_ordinal(today_date.day)} {today_date.strftime('%B')}"
            # if date_div == formatted_date:
            #     articles = div.find_all('article')
            #     for article in articles:
            #         link = article.find('h2', class_ = "entry-title default-max-width").find("a")['href']
                    # result += scrape_website_civilDaily(link)
        return result
    # elif "www.civilsdaily.com" in url:
    #     # result += scrape_website_civilDaily(url)
    #     return result
    # elif "iasbaba.com" in url:
    #     # result+=scrape_website_iasbaba(url)
    #     return result
    # elif "iasgyan.in" in url:
        
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
    

url = "https://pwonlyias.com/current-affairs/issues-of-queer-community/"
print(scrape_website_current_affair(url))