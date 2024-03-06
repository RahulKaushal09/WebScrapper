from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, Comment
import re


app = Flask(__name__)


def scrape_text(text):
    # Setup Selenium WebDriver

    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(text, 'html.parser')

    tags_to_remove = ['footer', 'option', 'header', 'style', 'form',
                      'label', 'input', 'script', 'button']
    for tag in tags_to_remove:
        for element in soup.find_all(tag):
            element.decompose()  # Remove the tag and its content
    for style in soup.find_all('style'):
        style.extract()
    # for style in soup.find_all('style'):
    #     style.extract()
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
    empty_span_tags = soup.find_all('span', class_=True)
    for tag in empty_span_tags:
        if not tag.text.strip():
            tag.decompose()
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
    for tag in soup.descendants:
        if tag.name in ['h2']:
            h2_tags += 1
    if (h2_tags > 4):
        for tag in soup.descendants:
            if tag.name in ['p', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li']:
                text = tag.get_text(strip=True)
                if text and text not in processed_texts:
                    # Remove extra spaces using regex
                    text = re.sub(r'\s+', ' ', text)
                    processed_texts.add(text)
                    text = "<"+tag.name+">"+text+"</"+tag.name+">"
                    if (tag.name == 'h2'):
                        if first == False:
                            text = "\n ********** \n"+text
                        else:

                            first = False

                    text_list.append(text)
                    if (tag.name == 'h2'):
                        text_list.append("\n ")

    else:
        count_p = 0
        for tag in soup.descendants:
            if tag.name in ['p', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li']:
                text = tag.get_text(strip=True)
                if text and text not in processed_texts:
                    # Remove extra spaces using regex
                    text = re.sub(r'\s+', ' ', text)
                    processed_texts.add(text)
                    text = "<"+tag.name+">"+text+"</"+tag.name+">"
                    if (tag.name == 'p'):
                        count_p += 1
                        if (count_p == 4):
                            count_p = 0
                            text = text + "\n ********** \n"

                    text_list.append(text)
                    if (tag.name == 'h2'):
                        text_list.append("\n ")

    # Write extracted text to the output file
    result = ""
    for text in text_list:
        result += text + '\n'
    result_in_parts = result.split("**********")
    output = ""
    first = True
    for text in result_in_parts:
        if (len(text) != 0):
            if (first):
                first = False
                output += text
            else:
                if (len(text) < 300):
                    output += text
                else:

                    output += "\n ********** \n"+text
    return output


def scrape_website(url):
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
    # Wait for JavaScript to render. Adjust the time as necessary.
    driver.implicitly_wait(10)

    # Get page source after JavaScript execution
    html = driver.page_source
    driver.quit()  # Close the browser

    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(html, 'html.parser')
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()
    for style in soup.find_all('style'):
        style.extract()
    for nav in soup.find_all('nav'):
        nav.extract()
    # for header in soup.find_all('header'):
    #     header.extract()
    header_tags = soup.find_all('header')
    for tag in header_tags:
        tag.clear()
    tags_to_remove = ['footer','ins','iframe','nav','aside','link','meta', 'option', 'header','style', 'form',
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
    empty_span_tags = soup.find_all('span', class_=True)
    for tag in empty_span_tags:
        if not tag.text.strip():
            tag.decompose()
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
    for tag in soup.descendants:
        if tag.name in ['h2']:
            h2_tags += 1
    # try:
    if (h2_tags > 4):
        for tag in soup.descendants:
            if tag.name in ['p', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li']:
                text = tag.get_text(strip=True)
                if text and text not in processed_texts:
                    # Remove extra spaces using regex
                    text = re.sub(r'\s+', ' ', text)
                    processed_texts.add(text)
                    text = "<"+tag.name+">"+text+"</"+tag.name+">"
                    if (tag.name == 'h2'):
                        if first == False:
                            # first = 1
                            text = "\n ********** \n"+text
                        else:

                            first = False

                    text_list.append(text)
                    if (tag.name == 'h2'):
                        text_list.append("\n ")
                    
            # elif isinstance(tag, str):
            #     text = re.sub(r'\s+', ' ', tag).strip()
            #     processed_texts.add(text)
            #     count_str += 1
            #     if (count_str == 4):
            #         count_str = 0
            #         text = text + "\n ********** \n"
            #     text_list.append(text)

    else:
        # count_p = 0
        count_str =0
        for tag in soup.descendants:
            if tag.name in ['p', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li']:
                text = tag.get_text(strip=True)
                if text and text not in processed_texts:
                    # Remove extra spaces using regex
                    text = re.sub(r'\s+', ' ', text)
                    processed_texts.add(text)
                    text = "<"+tag.name+">"+text+"</"+tag.name+">"
                    if (tag.name == 'p'):
                        count_p += 1
                        if (count_p == 4):
                            count_p = 0
                            text = text + "\n ********** \n"

                    text_list.append(text)
                    if (tag.name == 'h2'):
                        # text = text +'\n'
                        text_list.append("\n ")
            # elif isinstance(tag, str):
            #     text = re.sub(r'\s+', ' ', tag).strip()
            #     processed_texts.add(text)
            #     count_str += 1
            #     if (count_str == 4):
            #         count_str = 0
            #         text = text + "\n ********** \n"
            #     text_list.append(text)
            

    # Write extracted text to the output file
    result = ""
    for text in text_list:
        result += text + '\n'
    print(result)
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

    


@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')
    # url = "view-source:"+url

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        output_text = scrape_website(url)
        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error: "+str(e)}), 500


@app.route('/textToScrape', methods=['POST'])
def scrapeText():
    data = request.json
    text = data.get("data")
    if not text:
        return jsonify({'error': 'text is required'}), 400
    try:
        output_text = scrape_text(text)
        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error: "+str(e)}), 500


@app.route('/')
def hello_world():
    return 'Hello World'


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=81)
