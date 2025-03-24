
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
# def handle_question_component(component):
#             # Find all buttons inside the question component
#             buttons = component.find_all( "button")
#             print(buttons)
            
#             # Click all buttons
#             for button in buttons:
#                 button.click()

#             # Find the "Check Answer" button and click it
#             check_answer_button = component.find_element(By.XPATH, "//button[@aria-label='Check Answer Button']")
#             check_answer_button.click()
def getScrollerTest(url):
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
    # Get page source after JavaScript execution
    if "https://questions.examside.com" in url:
        # Process question components
        
        question_components = driver.find_elements(By.CSS_SELECTOR, ".question-component")

        # Loop through each question component
        for question_component in question_components:
            # Find the "Check Answer" button within the current question component
            check_answer_button = question_component.find_element(By.CSS_SELECTOR, 'button[aria-label="Check Answer Button"]')
            
            # Click the "Check Answer" button
            check_answer_button.click()
        # for component in question_components:
            # handle_question_component(component)
    html = driver.execute_script("return document.documentElement.outerHTML")
    # html = driver.page_source
    # print(html)
    driver.quit()  # Close the browser
    soup = BeautifulSoup(html, 'html.parser')
    # with open('scroller.html', 'w') as f:
    #     f.write(soup.prettify())
    # print(soup)

    formatted_questions = []
    if 'www.mockers.in/' in url:
        question_div = soup.find('ul', class_='ques-list')
        questions = question_div.find_all('li')
        for question in questions:
            question_text = question.find('div', class_='qsn-here').text.strip()

            options = question.find_all('div', class_='form-group')
            option_texts = [opt.find('h6').text.strip() for opt in options]

            correct_option = question.find('label', class_='thisIsCorrect').find('span',class_="optionIndex").text.strip()
            answer = f'Option {correct_option}: {option_texts[ord(correct_option) - ord("A")]}'

            solution_text = question.find('div', class_='qn-solution').text.strip()
            solution_text = solution_text.replace('Solutions', '')

            formatted_question = f"Question:\n{question_text}\n"
            formatted_options = "\n".join([f"Option {chr(ord('A') + i)}: {option_texts[i]}" for i in range(len(option_texts))])
            formatted_answer = f"Answer: {answer}\n"
            formatted_solution = f"\nSolution:\n{solution_text}"

            formatted_output = formatted_question + formatted_options + formatted_answer + formatted_solution
            formatted_questions.append(formatted_output)
        for i, formatted_question in enumerate(formatted_questions, start=1):
            print(f"Question {i}:\n{formatted_question}\n")
    # elif "https://questions.examside.com" in url:
    #     OPTIONS = soup.find('div', class_='options')
    #     question_divs = soup.find('div', class_='question-component')
    #     for questions in question_divs:
    #         question_div = questions.find('div', class_='question')
    #         question_text = ""
    #         for child in question_div.descendants:
    #             if child.name in ['p','img']:
    #                 if child.name == 'img':
    #                     question_text += str(child)
    #                 else:
    #                     question_text += child.text
    #         # print(question_text)
    #         print(OPTIONS)
    #         options = questions.find_all('div', class_='options')
    #         formatted_options = [f"Option {opt.find('div', class_='shrink-0').text}: {opt.find('div', class_='grow').text}" for opt in options]
    #         print(formatted_options)
    #         correct_option = questions.find('div', class_='grow question', text=True).text
    #         answer = f"Answer: {correct_option}"

    #         print("Question:")
    #         print(question_text)
    #         print("\nOptions:")
    #         for opt in formatted_options:
    #             print(opt)
    #         print("\n" + answer)
        

    return ""
url = "https://www.mockers.in/test-solution1/test-575422"
# url = "https://questions.examside.com/past-years/gate/question/pthe-current-i-in-the-circuit-shown-is-p-pi-gate-ece-network-theory-network-elements-8cndce2rxbh0j3mc#google_vignette"
# def createScrollerTest(url):
#     # data = request.json
#     # url = data.get("url")
#     if not url:
#         return jsonify({'error': 'text is required'}), 400
#     # try:
#     output_text = getScrollerTest(url)
#         # output_text = scrapeExcel(text)

#     #     return jsonify({'content': output_text}), 200
#     # except Exception as e:
#     #     print(e)
#     #     return jsonify({'content': "Error: "+str(e)}), 500
getScrollerTest(url)
