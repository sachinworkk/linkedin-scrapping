import os
import requests
from urls import urls
from time import sleep
from selenium import webdriver
from dotenv import load_dotenv
from nested_lookup import nested_lookup
from selenium.webdriver.common.by import By
from flask import Flask ,render_template, request
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
    options.headless = False
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

    company_link = urls["EMPLOYEE_LIST"].format(companyId='10117050',searchQueryParams='project%20manager',pageNumber='5')

    with requests.session() as s:
        s.cookies['li_at'] = li_at.get('value')
        s.cookies["JSESSIONID"] = jsessionId.get('value')
        s.headers = headers
        s.headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')
        response = s.get(company_link)
        response_dict = response.json()
        return get_formatted_employee_list(response_dict)


def get_employee(employee):
    imageURL = nested_lookup('fileIdentifyingUrlPathSegment',employee)
    profession = nested_lookup('primarySubtitle',employee)
    location = nested_lookup('secondarySubtitle',employee)
    name = nested_lookup('title',employee)

    detail = {'profession':profession[0]['text'],'location':location[0]['text'],'name':name[0]['text']}

    if len(imageURL) == 0:
        imageURL.append('')
       
    return {'detail': detail,'imageURL':imageURL[0]}

def get_formatted_employee_list(linkedInEmployeeResponse):  
    results = nested_lookup('results',linkedInEmployeeResponse)

    return list(map(get_employee , results[0]))



if __name__ == "__main__":
    app.run(debug=True)

