from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
# HTML content with your MathML
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>MathML Rendering</title>
</head>
<body>
    <span class="math-tex">
        <span class="MathJax_Preview" style="color: inherit;"></span>
        <span class="MathJax" data-mathml='&lt;math xmlns="http://www.w3.org/1998/Math/MathML"&gt;&lt;mfrac&gt;&lt;mrow class="MJX-TeXAtom-ORD"&gt;&lt;mn&gt;23&lt;/mn&gt;&lt;/mrow&gt;&lt;mrow class="MJX-TeXAtom-ORD"&gt;&lt;mn&gt;6&lt;/mn&gt;&lt;/mrow&gt;&lt;/mfrac&gt;&lt;/math&gt;' id="MathJax-Element-132-Frame" role="presentation" style="position: relative;" tabindex="0">
            <span class="MJX_Assistive_MathML" role="presentation">
                <math xmlns="http://www.w3.org/1998/Math/MathML">
                    <mfrac>
                        <mrow class="MJX-TeXAtom-ORD"><mn>23</mn></mrow>
                        <mrow class="MJX-TeXAtom-ORD"><mn>6</mn></mrow>
                    </mfrac>
                </math>
            </span>
        </span>
    </span>
</body>

</html>
"""

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")

# Set path to chromedriver as needed
driver = webdriver.Chrome(options=chrome_options)

# Load HTML content
driver.get("data:text/html;charset=utf-8,{html}".format(html=html_content))
time.sleep(2)
# Save screenshot of the page
driver.save_screenshot('math_equation.png')

# Clean up (close the browser)
driver.quit()
