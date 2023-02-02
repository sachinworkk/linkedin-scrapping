import os
import json
import requests

from urls import urls

from flask_cors import CORS
from flask import Flask,request

from time import sleep
from selenium import webdriver
from dotenv import load_dotenv
from nested_lookup import nested_lookup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


load_dotenv()

app = Flask(__name__)

CORS(app)

@app.route('/login',methods=['POST'])
def login():
    request_data = request.get_json()
    email = request_data['email']
    password = request_data['password']

    return selenium_login(email,password)

def selenium_login(email,password):
    options = Options()
    options.headless = False
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)

    driver.maximize_window()
    driver.get(os.environ.get("URL"))

    email_element = driver.find_element(By.ID,"session_key")
    password_element = driver.find_element(By.ID,"session_password")

    signIn = driver.find_element(By.CLASS_NAME,"sign-in-form__submit-button")

    email_element.send_keys(email)

    sleep(4)

    password_element.send_keys(password)

    sleep(5)
    signIn.click()

    li_at = ''
    jsession_id = ''

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "voyager-feed"))
        )

        li_at=driver.get_cookie('li_at')
        jsession_id = driver.get_cookie("JSESSIONID")

        return {'liAt':li_at,'jSessionId':jsession_id}
    except: # pylint: disable=bare-except
        return {'message':'There was a problem while login in'}

@app.route("/scrap",methods = ['POST'])
def scrap():
    if request.method == 'POST':
        request_data = request.get_json()
   
        liAt = json.loads(request_data['liAt'])
        companyId = request_data['organization']
        searchQueryParams = request_data['profession']
        jSessionId = json.loads(request_data['jSessionId'])
        pageNumber = request_data['pageNumber']

        response = selenium_scrap(liAt,jSessionId,companyId,searchQueryParams,pageNumber)
        return response

def selenium_scrap(li_at,jsession_id,company_id='466027',search_query_params='project%20manager',page_number='0'):
    headers = {"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
            }

    company_link = urls["EMPLOYEE_LIST"].format(companyId=company_id,searchQueryParams=search_query_params,pageNumber=page_number)

    with requests.session() as s:
        s.cookies['li_at'] = li_at.get('value')
        s.cookies["JSESSIONID"] = jsession_id.get('value')
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
   

    if len(imageURL) == 0:
        imageURL.append('')
       
    return {'profession':profession[0]['text'],'location':location[0]['text'],'name':name[0]['text'],'imageURL':imageURL[0]}

def get_formatted_employee_list(linkedInEmployeeResponse):  
    results = nested_lookup('results',linkedInEmployeeResponse)
    pagination = nested_lookup('paging',linkedInEmployeeResponse)

    return {"employees":list(map(get_employee , results[0])),"pagination": pagination[0]}



if __name__ == "__main__":
    app.run(debug=True)

