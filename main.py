import requests
from time import sleep
from flask import Flask ,render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__,template_folder='template')


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/scrap",methods = ['POST'])
def run_automation():
    if request.method == 'POST':
        response = selenium_code()
        return response

def selenium_code():
    options = Options()
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)

    driver.maximize_window()
    driver.get(os.environ.get("URL"))

    email = driver.find_element(By.ID,"session_key")
    password = driver.find_element(By.ID,"session_password")

    signIn = driver.find_element(By.CLASS_NAME,"sign-in-form__submit-button")

    email.send_keys(os.environ.get("EMAIL"))

    sleep(4)

    password.send_keys(os.environ.get("PASSWORD"))

    sleep(5)
    signIn.click()

    li_at = ''
    jsessionId = ''

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "voyager-feed"))
        )

        li_at=driver.get_cookie('li_at')
        jsessionId = driver.get_cookie("JSESSIONID")
    except:
        print("An exception occurred")



    headers = {"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
            }

    company_link = 'https://www.linkedin.com/voyager/api/search/dash/clusters?decorationId=com.linkedin.voyager.dash.deco.search.SearchClusterCollection-175&origin=FACETED_SEARCH&q=all&query=(flagshipSearchIntent:SEARCH_SRP,queryParameters:(currentCompany:List(10117050),resultType:List(PEOPLE),title:List(project%20manager)),includeFiltersInResponse:false)&start=5'

    with requests.session() as s:
        s.cookies['li_at'] = li_at.get('value')
        s.cookies["JSESSIONID"] = jsessionId.get('value')
        s.headers = headers
        s.headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')
        response = s.get(company_link)
        response_dict = response.json()
        return response_dict


if __name__ == "__main__":
    app.run(debug=True)

