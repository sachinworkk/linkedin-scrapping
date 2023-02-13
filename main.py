"""
Project modules.
"""
import os
import json

from time import sleep

import requests

from flask_cors import CORS
from flask import Flask,request

from dotenv import load_dotenv

from nested_lookup import nested_lookup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager


from urls import urls

load_dotenv()

app = Flask(__name__)

CORS(app)

@app.route('/login',methods=['POST'])
def login():
    """
    It takes in a user's email and password, and returns a JSON object containing
    the login session and token
    """
    request_data = request.get_json()
    email = request_data['email']
    password = request_data['password']

    return selenium_login(email,password)

def selenium_login(email,password):
    """
    It opens a chrome browser, navigates to the LinkedIn login page, enters the email and password,
    clicks the sign in button, and returns the user logged in cookies
    """
    options = Options()
    options.headless = False
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)

    driver.maximize_window()
    driver.get(os.environ.get("URL"))

    email_element = driver.find_element(By.ID,"session_key")
    password_element = driver.find_element(By.ID,"session_password")

    sign_in = driver.find_element(By.CLASS_NAME,"sign-in-form__submit-button")

    email_element.send_keys(email)

    sleep(4)

    password_element.send_keys(password)

    sleep(5)
    sign_in.click()

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
    """
    It requests linkedin for company's employee
    """
    if request.method == 'POST':
        request_data = request.get_json()
 
        li_at = json.loads(request_data['liAt'])
        company_id = request_data['organization']
        search_query_params = request_data['profession']
        jsession_id = json.loads(request_data['jSessionId'])
        page_number = request_data['pageNumber']

        response = selenium_scrap(li_at,jsession_id,company_id,search_query_params,page_number)
        return response

def selenium_scrap(li_at,jsession_id,company_id='466027'
,search_query_params='project%20manager',page_number='0'):
    """
    It requests linkedin for company's employee
    """
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
    """
    It returns a list of employee from deep nested json
    """
    image_url = nested_lookup('fileIdentifyingUrlPathSegment',employee)
    profession = nested_lookup('primarySubtitle',employee)
    location = nested_lookup('secondarySubtitle',employee)
    name = nested_lookup('title',employee)

    if len(image_url) == 0:
        image_url.append('')
    
    return {'profession':profession[0]['text'],'location':location[0]['text'],'name':name[0]['text'],'imageURL':image_url[0]}

def get_formatted_employee_list(linked_in_employee_response):
    """
    It takes the response from the LinkedIn API and returns a list of employees with their names,
    titles, and LinkedIn profile URLs
    """
    results = nested_lookup('results',linked_in_employee_response)
    pagination = nested_lookup('paging',linked_in_employee_response)

    return {"employees":list(map(get_employee , results[0])),"pagination": pagination[0]}



if __name__ == "__main__":
    app.run(debug=True)