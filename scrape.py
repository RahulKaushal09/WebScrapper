from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, Comment
import re
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import uuid


web_path = "http://example.com/images/"
output_dir = "assets/images"
app = Flask(__name__)

# def latex_to_image_base64(latex_str):
#     fig = plt.figure()
#     fig.text(0, 0, latex_str, fontsize=14)
#     plt.axis('off')
#     buf = BytesIO()
#     plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
#     plt.close(fig)
#     img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
#     return img_base64

def simplify_latex_limits(latex_code):
    # Replace the verbose limit syntax with the conventional syntax
    simplified_code = latex_code.replace(r"\mathop {\lim }\limits", r"\lim")
    
    # Additional cleanup if necessary, for example removing extra spaces or handling other cases
    
    return simplified_code
def latex_to_image(latex_code,output_dir):
    latex_code = simplify_latex_limits(latex_code)
    fig_width = len(latex_code) * 0.001  # Adjust the multiplier as needed
    fig_height = 1.0  # Fixed height
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')
    ax.text(0.5, 0.5, f"${latex_code}$", size=16, ha='center', va='center')
    filename = str(uuid.uuid4()) + ".png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, format='png', bbox_inches='tight', pad_inches=0.0)
    plt.close()
    return filename

    # ax.text(0.5, 0.5, r"$%s$" % latex_code, size=30, ha='center')
    # buffer = BytesIO()
    # plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0.0)
    # plt.savefig('output'+str(i)+'.png', format='png', bbox_inches='tight', pad_inches=0.0)
    # plt.close()
    # buffer.seek(0)
    # # print(latex_code)
    # image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    # return image_base64
    
def scrape_text(text):
    # Setup Selenium WebDriver

    soup = BeautifulSoup(text, 'html.parser')
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()
    for style in soup.find_all('style'):
        style.extract()
    for nav in soup.find_all('nav'):
        nav.extract()
    # for header in soup.find_all('header'):
    #     header.extract()
    # images =""
    latex_expressions = soup.find_all('script', type='math/tex')
    images = []
    i=0
    
    for expr in latex_expressions:
        latex = expr.string.strip()  # Get the LaTeX expression
        # print(latex)
        i+=1
        filename = latex_to_image(latex, output_dir)
        img_url = web_path + filename  # Convert LaTeX to base64-encoded image
        img_url = web_path + filename
        img_tag = soup.new_tag('img')
        img_tag['src'] = f'data:image/png;base64,{img_data_base64}'
        # img_tag['style'] = 'width:300px;height:300px;'  # Set the width and height inline styles
        print(expr)
        images.append(img_tag)
        # images+=str(img_tag)+"\n"
        # expr.replace_with(img_tag)  # Replace the LaTeX script tag with the image tag
    elements_with_mathml = soup.find_all(lambda tag: tag.has_attr('data-mathml'))
    # print(elements_with_mathml)
    i =0
    for element in elements_with_mathml:
        # Replace the element with an image tag
        # print("hey")
        image_tag= images[i]  # Get the first image URL from the array
        # new_tag = soup.new_tag('img', src=image_url)
        element.replace_with(image_tag)
        i+=1
    
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
    # empty_span_tags = soup.find_all('span', class_=True)
    # for tag in empty_span_tags:
    #     if not tag.text.strip():
    #         tag.decompose()
    empty_p_tags = soup.find_all('p', class_=True)
    for tag in empty_p_tags:
        if not tag.text.strip():
            tag.decompose()
            
    body_tag = soup.find('body')
    if body_tag:
        body_content = body_tag.prettify()
    else:
        body_content = soup.find().prettify()

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
    # span_tags = soup.find_all('span')
    # for tag in span_tags:
    #     print(tag)
    for tag in soup.descendants:
        if tag.name in ['p','span' ,'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li']:
            if tag.name == 'span':
                print(tag)
                text = str(tag)
            else:
                text = tag.get_text(strip=True)
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
                    
                    elif(tag.name == 'p' and previous_content_length >1500):
                        text = text+"\n ********** \n"
                        previous_content_length =0 
                        first = False
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


def scrape_website(url,edurev):
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

    # Get page source after JavaScript execution
    html = driver.page_source
    # print(html)
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
    text_list = []
    latex_expressions = soup.find_all('script', type='math/tex')
    for expr in latex_expressions:
        latex = expr.string.strip()  # Get the LaTeX expression
        img_data_base64 = latex_to_image_base64(latex)  # Convert LaTeX to base64-encoded image
        img_tag = soup.new_tag('img')
        img_tag['src'] = f'data:image/png;base64,{img_data_base64}'
        # print(img_tag)
        expr.replace_with(img_tag)  # Replace the LaTeX script tag with the image tag


    if edurev == True:
        try:
            ads = soup.find_all('div', class_='cnt_ad_bnr')
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
                if tag.name in ['p','img','strong','span', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li']:
                    # print(tag)
                    if tag.name == 'img':
                        text = str(tag)
                        print(tag)
                    else:

                        text = tag.get_text(strip=True)
                        if text in processed_texts:
                            print("yes")
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
                                # if first == False:
                                # else:
                                #     first = False
                            # elif(tag.name == 'h3' and previous_content_length >1500):
                            #     text = "\n ********** \n"+text
                            #     previous_content_length =0 
                            #     first = False
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
       
    else:         

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
        previous_content_length = 0
        for tag in soup.descendants:
            if tag.name in ['h2']:
                h2_tags += 1
        # try:
        # if (h2_tags > 4):
        for tag in soup.descendants:
            if tag.name in ['p','img','strong','span', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li']:
                if tag.name == 'img':
                    text = str(tag)
                    print(tag)
                else:

                    text = tag.get_text(strip=True)
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
                            # if first == False:
                            # else:
                            #     first = False
                        # elif(tag.name == 'h3' and previous_content_length >1500):
                        #     text = "\n ********** \n"+text
                        #     previous_content_length =0 
                        #     first = False
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

    # else:
    #     # count_p = 0
    #     count_str =0
    #     for tag in soup.descendants:
    #         if tag.name in ['p', 'h1', 'h2', 'h3', 'tr', 'td' 'h4', 'h5', 'h6',  'ul', 'li']:
    #             text = tag.get_text(strip=True)
    #             if text and text not in processed_texts:
    #                 # Remove extra spaces using regex
    #                 text = re.sub(r'\s+', ' ', text)
    #                 processed_texts.add(text)
    #                 text = "<"+tag.name+">"+text+"</"+tag.name+">"
    #                 if (tag.name == 'p'):
    #                     count_p += 1
    #                     if (count_p == 4):
    #                         count_p = 0
    #                         text = text + "\n ********** \n"

    #                 text_list.append(text)
    #                 if (tag.name == 'h2'):
    #                     # text = text +'\n'
    #                     text_list.append("\n ")
    #         # elif isinstance(tag, str):
    #         #     text = re.sub(r'\s+', ' ', tag).strip()
    #         #     processed_texts.add(text)
    #         #     count_str += 1
    #         #     if (count_str == 4):
    #         #         count_str = 0
    #         #         text = text + "\n ********** \n"
    #         #     text_list.append(text)
            

    # Write extracted text to the output file
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

    


@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')
    # url = "view-source:"+url
    print(url)

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        edurev = False
        if "edurev.in" in url:
            edurev = True
        output_text = scrape_website(url,edurev)
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
        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error: "+str(e)}), 500


@app.route('/')
def hello_world():
    return 'Hello World'


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=81)
