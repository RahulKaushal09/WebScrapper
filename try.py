from flask import Flask, request, jsonify
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import datetime
import time
import json
# import spacy
import random
import openai 




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
            if child.string and child.string.strip() and child.string.strip() not in all_data:
                all_data += child.string.strip() + "\n"
        all_data+="**********"+"\n"
    
    # print(all_data)
    return all_data.strip()

def get_data_vija_test(url):
    cookies = "MicrosoftApplicationsTelemetryDeviceId=c2ddee41-33ac-4b7d-81bb-547d154641ee; MicrosoftApplicationsTelemetryFirstLaunchTime=2024-05-22T12:44:26.422Z; MicrosoftApplicationsTelemetryDeviceId=c2ddee41-33ac-4b7d-81bb-547d154641ee; MicrosoftApplicationsTelemetryFirstLaunchTime=2024-05-22T12:44:26.422Z; _gcl_au=1.1.216017465.1717047138; _gid=GA1.2.585973560.1717047138; next=%2Fdaily-mcq-test-detail%2F30-may-2024-mcqs-test%2F66586b994f1b743e078b2f5d%2F; _gat_gtag_UA_134436911_1=1; csrftoken=WAKY5qTDr7cEgUp8SocNZFV6TVcVghzy8HtHsaT95r7yK93xEXoSuVn0m8CrgohR; sessionid=41xl11tynsxiq7m71q38dorcax7jtwg6; _ga=GA1.1.574855248.1717047138; _ga_DTHV5PJMS3=GS1.1.1717074194.5.1.1717074250.0.0.0"
    request_headers = {
        "cookie": cookies,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "referer": "https://vajiramias.com/"
    }
    get_url = url
    response = requests.get(get_url, headers=request_headers)
    html = response.text
    print(html)
    soup = BeautifulSoup(html, 'html.parser')
    result = {
        'questions': []
    }
    question_boxes = soup.find_all('div', class_='daily_mcq_question_box')
    # print(question_boxes)
    for question_box in question_boxes:
        question_element = question_box.find('div', class_='question_text')
        question_text = question_element.text.strip()
        options = question_box.find_all('tr', class_='question_option')
        option_list = []
        for option in options:
            option_text = option.find('td', class_='option_text').text.strip()
            option_list.append(option_text)
        correct_option_div = question_box.find('tr', class_='question_option bg-light-greesn')
        correct_option = correct_option_div.find('td', class_='option_text').text.strip()
        solution_div = question_box.find('div', class_='explanation_text')
        solution_text = ''
        for child in solution_div.descendants:
            if child.string and child.string.strip():
                solution_text += child.string.strip()
        result['questions'].append({
            'question': question_text,
            'option': option_list,
            'correct_answer': correct_option,
            'solution': solution_text
        })
    print(result)
    return result
def scrape_website_vaji_test(url):
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
    question_boxes = soup.find_all('div', class_='box-body')
    
    for question_box in question_boxes:
        date_element = question_box.find('h3', class_='mcq_card_title')
        date_text = date_element.text.strip()
        date_only = date_text.split("MCQs Test")[0].strip()

        # print(date_text)
        today_date = datetime.datetime.now().strftime("%d %B %Y")
        if date_only == today_date:
            question_box_parent = question_box.find_parent('a',)
            link = question_box_parent['href']
            test_code = link.split('/')[-2]
            report_url = f"https://vajiramias.com/daily-mcq-test-report/{test_code}/"
            # print(test_code)
            
            return get_data_vija_test(report_url)
    
            
    # return result
       
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
    result = {
        'questions': []
    }
    if url == "https://www.gktoday.in":
        '''
        <div><div class="wp_quiz_question testclass"><span class="quesno">1. </span>Recently, Gitanas Nausėda has been re-elected as the President of which country?</div><div type="A" class="wp_quiz_question_options"><p> [A] Lithuania<br>[B] Luxembourg<br>[C] Croatia<br>[D] Bulgaria</p></div><p><a class="wp_basic_quiz_showans_btn" onclick="if (!window.__cfRLUnblockHandlers) return false; if(jQuery(this).hasClass('showanswer')){ jQuery(this).html('Show Answer').removeClass('showanswer'); jQuery('.ques_answer_127466').slideUp(); }else { jQuery(this).html('Hide Answer').addClass('showanswer'); jQuery('.ques_answer_127466').slideDown();}">Show Answer</a></p><div class="wp_basic_quiz_answer ques_answer_127466" style="display:none;"><div class="ques_answer"><b>Correct Answer:</b> A [Lithuania]</div><div class="answer_hint"><b>Notes:</b><br>Gitanas Nausėda, a non-partisan candidate and former bank chief economist, was re-elected as Lithuania’s president on May 26, 2024, defeating Prime Minister Ingrida Šimonytė. The initial election on May 12, 2024, saw Nausėda receiving 46% and Šimonytė 16%, leading to a run-off. Nausėda won decisively, securing his second five-year term. Prime Minister Narendra Modi congratulated him on his re-election.<p></p></div></div></div>'''
        # Find the link for today's date
        questions = soup.find_all('div', class_="wp_quiz_question testclass")
        options = soup.find_all('div', class_="wp_quiz_question_options")
        correct_answers = soup.find_all('div', class_="ques_answer")
        solutions = soup.find_all('div', class_="answer_hint").text

        for i in range(0, len(questions)):
            question = questions[i].text
            option = options[i].text
            options_text = option[i].strip().split('<br>')
            options = [text.strip()[3:] for text in options_text]
            correct_answer = correct_answers[i].text
            solution = solutions[i].text
            result['questions'].append({
                'question': question,
                'option': options,
                'correct_answer': correct_answer,
                'solution': solution
            })
            return result

                    
    elif url == "https://www.drishtiias.com":
        # div_elements = soup.find_all('div', class_="news-block")
        
        # result = ""
        # for div in div_elements:
        #     date_div = div.find('h1', class_="date-strip").text
        #     date_div = date_div[1:]
        #     # print(date_div)
        #     today_date = datetime.datetime.now()  # Format like '22 May 2024'
        #     formatted_date = f"{get_ordinal(today_date.day)} {today_date.strftime('%B')}"
        #     # print(formatted_date)
        #     if date_div == formatted_date:
        #         articles = div.find_all('article')
        #         for article in articles:
        #             link = article.find('h2', class_ = "entry-title default-max-width").find("a")['href']
        #             result += scrape_website_civilDaily(link)
        return result
    return ""       
def getGPTResponse(prompt):
    try:
        # Your user prompt as a dictionary
        user_prompt = {
            "Role": "You are a proficient educational content creator specializing in summarizing and synthesizing complex information from PDF books into concise, comprehensible notes and test materials. Your expertise lies in extracting key theoretical concepts, providing clear definitions, and offering illustrative examples. When presenting information in a list, use only 'li' tags without 'p' tags inside them. Ensure the notes are well-organized and visually appealing, employing HTML tags for structure without using paragraph tags inside list items. Your goal is to optimize the learning experience for your audience by Explaining in Detail from the lengthy content into digestible formats while maintaining educational rigor. You are a content formatter specializing in converting text into HTML elements. Your expertise lies in structuring text into well-formatted HTML tags, including <li>, <ul>, and <p>, without using special characters like * or #. Your goal is to ensure that the HTML output is organized, visually appealing",
            "objective": prompt
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
                    "content": json.dumps(user_prompt)
                }
            ],
            max_tokens=4096,
            temperature=0.7
        )

        # Print the response
        if response.choices:
            # Access the content from the response
            data_res = response.choices[0].message.content
            # print(content)
        else:
            print("No response generated.")
        data_res = str(data_res) 
        return data_res
    except Exception as e:  
        print(e)
        return jsonify({'error': 'An error occurred'}), 500
    

app = Flask(__name__)
def scrape_website_drishti(url):
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
    question_boxes = soup.find_all('ol')


    for question_box in question_boxes:
        date_element = question_box.find('li')
        date_text = date_element.text.strip()
        date_only = date_text.split(")")[0].strip()
        date_only = date_only.split("(")[1].strip()

        today_date = datetime.datetime.now()
        formatted_date = f"{get_ordinal(today_date.day)} {today_date.strftime('%B')}, {today_date.year}"
        
        
        if date_only == formatted_date:
            link = question_box.find('a')['href']
            return scrape_website_current_affair(link)
def scrape_website_gktoday_test(url):
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
    question_boxes = soup.find_all('article')

    for question_box in question_boxes:
        date_element = question_box.find('ul')
        date_text = date_element.text.strip()
        date_only = date_text.split(": ")[1].strip()
        today_date = datetime.datetime.now().strftime("%B %d, %Y")
        
        if date_only == today_date:
            link = question_box.find('a')['href']
            questions = scrape_website_current_affair(link)
# @app.route('/getCurrentAffairs', methods=['GET'])
def scrape_websites():
    websites = [
        "https://vajiramias.com/daily-mcq/2024/5/",
        # "https://www.gktoday.in/gk-current-affairs-quiz-questions-answers/",
        # "https://www.drishtiias.com/quiz/quizlist/daily-current-affairs"
    ]

    result = {
        'questions':[]
    }
    for url in websites:
        if "https://vajiramias.com/" in url:
            data = scrape_website_vaji_test(url)
            if len(data) > 0:
                for question in data['questions']:
                    result['questions'].append(question)
        elif url == "https://www.gktoday.in/gk-current-affairs-quiz-questions-answers/":
            data = scrape_website_gktoday_test(url)
            if len(data) > 0:
                for question in data['questions']:
                    result['questions'].append(question)

        elif url == "https://www.drishtiias.com/quiz/quizlist/daily-current-affairs":
            data = scrape_website_drishti(url)
            if len(data) > 0:
                result += data

    

scrape_websites()
# if __name__ == '__main__':
#     app.run()

# with open("result.json", 'w') as file:
#     json.dump(result, file)