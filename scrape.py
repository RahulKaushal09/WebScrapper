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
from handleLatex import run
from handleLatex import latex_to_image
from LatexToImage import excelRun


# web_path = "http://example.com/images/"
# output_dir = "assets/images"
app = Flask(__name__)

def simplify_latex_limits(latex_code):
    # Replace the verbose limit syntax with the conventional syntax
    simplified_code = latex_code.replace(r"\mathop {\lim }\limits", r"\lim")
    
    # Additional cleanup if necessary, for example removing extra spaces or handling other cases
    
    return simplified_code
# def latex_to_image(latex_code,output_dir):
#     latex_code = simplify_latex_limits(latex_code)
#     fig_width = len(latex_code) * 0.001  # Adjust the multiplier as needed
#     fig_height = 1.0  # Fixed height
#     fig, ax = plt.subplots(figsize=(fig_width, fig_height))
#     ax.axis('off')
#     ax.text(0.5, 0.5, f"${latex_code}$", size=16, ha='center', va='center')
#     filename = str(uuid.uuid4()) + ".png"
#     filepath = os.path.join(output_dir, filename)
#     plt.savefig(filepath, format='png', bbox_inches='tight', pad_inches=0.0)
#     plt.close()
#     return filename

   
def scrape_text(text):
    # Setup Selenium WebDriver
    # latex to image 
    html_text = run(text)
  
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
    # empty_span_tags = soup.find_all('span', class_=True)
    # for tag in empty_span_tags:
    #     if not tag.text.strip():
    #         tag.decompose()
    # empty_p_tags = soup.find_all('p', class_=True)
    # for tag in empty_p_tags:
    #     if not tag.text.strip():
    #         tag.decompose()
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
    # try:
    # if (h2_tags > 4):
    # span_tags = soup.find_all('span')
    # for tag in span_tags:
    # soup.find().prettify()
    # print(soup)
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
    html_text = run(str(html))
    # Use BeautifulSoup to parse the HTML content
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
    # latex_expressions = soup.find_all('script', type='math/tex')
    # for expr in latex_expressions:
    #     latex = expr.string.strip()  # Get the LaTeX expression
    #     img_data_base64 = latex_to_image_base64(latex)  # Convert LaTeX to base64-encoded image
    #     img_tag = soup.new_tag('img')
    #     img_tag['src'] = f'data:image/png;base64,{img_data_base64}'
    #     # print(img_tag)
    #     expr.replace_with(img_tag)  # Replace the LaTeX script tag with the image tag


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
            'faqWrapper_last'
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
            'faqWrapper'
        ]

        for div_class in divs_to_remove_classes:
            div_elements = soup.find_all('div', class_=div_class)
            for div in div_elements:
                div.extract()
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
        tags_to_remove = ['footer','ins','iframe','nav','aside','link','meta', 'option','style','header',
                        'label', 'input', 'script', 'button']
        for tag in tags_to_remove:
            if 'https://www.savemyexams.com' in url :
                if tag != 'header':
                    for element in soup.find_all(tag):
                        element.decompose()  # Remove the tag and its content
            else:
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
        # 01/04/2024

        # empty_span_tags = soup.find_all('span', class_=True)
        # for tag in empty_span_tags:
        #     if not tag.text.strip():
        #         tag.decompose()
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
                    text = str(tag)

                    # print(tag)
                    text_list.append(text)
                else:
                    # if tag.name == 'h3':
                    #     # text = str(tag)
                    #     print(tag.get_text())
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
        return jsonify({'content': output_text}), 200
    except Exception as e:
        print(e)
        return jsonify({'content': "Error: "+str(e)}), 500


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


@app.route('/')
def hello_world():
    return 'Hello World'


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=81)
