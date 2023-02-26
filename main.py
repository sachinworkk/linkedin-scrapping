"""
Project modules.
"""
import os
import json
import re

from time import sleep

import urllib.parse

import requests

from flask_cors import CORS
from flask import Flask, request

from dotenv import load_dotenv

from nested_lookup import nested_lookup

from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import array

from urls import urls


load_dotenv()

app = Flask(__name__)

CORS(app)

options = Options()
options.headless = True
options.add_experimental_option("detach", True)


driver = None


@app.route('/login', methods=['POST'])
def login():
    """
    It takes in a user's email and password,
    and returns a JSON object containing
    the login session and token
    """
    request_data = request.get_json()
    email = request_data['email']
    password = request_data['password']

    return selenium_login(email, password)


def selenium_login(email, password):
    """
    It opens a chrome browser, navigates to the
    LinkedIn login page, enters the email and password,
    clicks the sign in button, and returns the user logged in cookies
    """
    global driver
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    driver.get(os.environ.get("URL"))

    email_element = driver.find_element(By.ID, "session_key")
    password_element = driver.find_element(By.ID, "session_password")

    sign_in = driver.find_element(By.CLASS_NAME, "sign-in-form__submit-button")

    email_element.send_keys(email)

    sleep(1)

    password_element.send_keys(password)

    sleep(2)
    sign_in.click()

    li_at = ''
    jsession_id = ''

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "voyager-feed"))
        )

        li_at = driver.get_cookie('li_at')
        jsession_id = driver.get_cookie("JSESSIONID")

        return {'liAt': li_at, 'jSessionId': jsession_id}
    except:  # pylint: disable=bare-except
        return {'message': 'There was a problem while login in'}


@app.route('/logout', methods=['DELETE'])
def selenium_logout():
    """
    The function clicks on the profile button in the top right corner of the page
    To Do: Automate clicking on logout button
    """
    try:
        global driver

        driver.quit()

        return {'liAt': '', 'jSessionId': '',
                'message': 'User logged out successfully'}
    except:  # pylint: disable=bare-except
        return {'message': 'There was a problem while login in'}


@app.route("/scrap", methods=['POST'])
def scrap():
    """
    It returns a list of employee data
    """
    if request.method == 'POST':
        request_data = request.get_json()
        li_at = json.loads(request.headers['liAt'])
        company_id = request_data['organization']
        search_query_params = request_data['profession']
        jsession_id = json.loads(request.headers['jSessionId'])
        page_number = request_data['pageNumber']

        response = selenium_scrap(
            li_at, jsession_id, company_id, search_query_params, page_number)
        return response


@app.route("/scrap/<employee_id>", methods=['POST'])
def scrapUserInfo(employee_id):
    """
    It takes an employee id as input, and returns
    employee's name, title,location, and a list of skills

    :param employee_id: The employee id of the employee
    whose details you want to fetch
    :return: A dictionary with the employee's information.
    """
    if request.method == 'POST':
        global driver

        li_at = json.loads(request.headers['liAt'])
        jsession_id = json.loads(request.headers['jSessionId'])

        # To Do: Scrap experience in the future.
        # driver.get(request_data['navigationURL'])

        # # try:
        # WebDriverWait(driver, 30).until(
        #     EC.presence_of_element_located(
        #         (By.ID, "experience"))
        # )

        # experience_element = driver.find_element(By.ID, "experience")

        # except:  # pylint: disable=bare-except
        #     return {'message': 'There was a problem scrapping project'}

        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        }

        employee_link = urls["EMPLOYEE_DETAIL"].format(employeeId=employee_id)
        with requests.session() as s:
            s.cookies['li_at'] = li_at.get('value')
            s.cookies["JSESSIONID"] = jsession_id.get('value')
            s.headers = headers
            s.headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')
            response = s.get(employee_link)
            response_dict = response.json()
            return get_formatted_employee_detail(response_dict)


@app.route("/companies", methods=['POST'])
def get_company_list():
    """
    It takes a company name as input, and returns a list of companies that match the input
    :return: A list of dictionaries.
    """

    if request.method == 'POST':
        global driver
        request_data = request.get_json()

        li_at = json.loads(request.headers['liAt'])
        jsession_id = json.loads(request.headers['jSessionId'])
        company_query_param = request_data['companySearchQueryParam']

        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36", }

        company_link = urls["LAZY_LOAD_COMPANY_LIST"].format(
            companyQuery=company_query_param)
        with requests.session() as s:
            s.cookies['li_at'] = li_at.get('value')
            s.cookies["JSESSIONID"] = jsession_id.get('value')
            s.headers = headers
            s.headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')
            response = s.get(company_link)
            response_dict = response.json()
            return get_formatted_company_list(response_dict)


def get_formatted_company_list(linked_in_companies_response):
    return {
        "companies": list(map(get_company_info, linked_in_companies_response['data']
                              ['searchDashTypeaheadByGlobalTypeahead']['elements']))
    }


def selenium_scrap(li_at, jsession_id, company_id='466027',
                   search_query_params='project%20manager', page_number='0'):
    """
    It requests linkedin for company's employee
    """
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36", }

    company_link = urls["EMPLOYEE_LIST"].format(
        companyId=company_id, searchQueryParams=search_query_params, pageNumber=page_number)

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
    It returns an employee data
    """
    image_url = nested_lookup('fileIdentifyingUrlPathSegment', employee)
    profession = nested_lookup('primarySubtitle', employee)
    location = nested_lookup('secondarySubtitle', employee)
    navigation_url = nested_lookup('url', employee)
    badge_text = nested_lookup('badgeText', employee)
    entity_urn = nested_lookup('entityUrn', employee)
    lazy_loaded_actions_urn = nested_lookup('lazyLoadedActionsUrn', employee)

    try:
        employee_id = navigation_url[0].split("/in/")[1].split("?")[0]
    except IndexError:
        employee_id = ''

    name = nested_lookup('title', employee)

    if len(image_url) == 0:
        image_url.append('')

    return {'profession': profession[0]['text'],
            'location': location[0]['text'],
            'name': name[0]['text'], 'imageURL': image_url[0],
            'navigationURL': navigation_url[0], 'employeeId': employee_id,
            'connection': badge_text[0]['accessibilityText'],
            'inviteeProfileUrn': entity_urn[1],
            "lazyLoadedActionsUrns": lazy_loaded_actions_urn[0],
            }


def extract_company_id(company_urn):
    """
    It takes a string, and if it matches a certain pattern, it returns the part of the string that
    matched the pattern

    :param company_urn: The URN of the company you want to get the data for
    :return: The company ID
    """
    if company_urn is None:
        return None

    pattern = r':(\d+)$'
    match = re.search(pattern, company_urn)

    if match:
        return match.group(1)
    else:
        return None


def get_company_info(linked_in_company_response):
    """
    It takes the response from the LinkedIn API and extracts the company name and ID

    :param linked_in_company_response: This is the response from the LinkedIn API
    :return: A dictionary with the text and trackingUrn of the company.
    """
    text = nested_lookup('text', linked_in_company_response)
    trackingUrn = array.get_item(nested_lookup(
        'trackingUrn', linked_in_company_response), 0, '')

    return {'text': text, 'trackingUrn': extract_company_id(trackingUrn)}


def get_formatted_employee_list(linked_in_employee_response):
    """
    It takes the response from the LinkedIn API and
    returns a list of employees with required
    information
    """
    results = nested_lookup('results', linked_in_employee_response)
    pagination = nested_lookup('paging', linked_in_employee_response)
    return {"employees": list(map(get_employee, results[0])),
            "pagination": pagination[0]}


def get_formatted_employee_detail(linked_in_employee_response):
    """
    It takes a response from the LinkedIn API and returns employee's
    phone number and email address.   
    :param linked_in_employee_response: This is the response from the linked in API
    :return: A dictionary with the number and email address of the employee.
    """
    number = nested_lookup('number', linked_in_employee_response['elements'])
    email = nested_lookup(
        'emailAddress', linked_in_employee_response['elements'])

    return {"number": array.get_item(number, 0, ''),
            "email": array.get_item(email, 1, '')}


@app.route('/send-invite', methods=['POST'])
def send_invite():
    """
    It takes a JSON object with the following keys:

    - liAt
    - jSessionId
    - inviteeProfileUrn

    And sends an invite to the inviteeProfileUrn
    """
    if request.method == 'POST':
        request_data = request.get_json()

        invitation_link = urls["INVITATION_LINK"]

        li_at = json.loads(request.headers['liAt'])
        jsession_id = json.loads(request.headers['jSessionId'])
        invitee_profile_urn = request_data['inviteeProfileUrn']

        with requests.session() as s:
            s.cookies['li_at'] = li_at.get('value')
            s.cookies["JSESSIONID"] = jsession_id.get('value')

            s.headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')
            response = s.post(invitation_link,
                              data=json.dumps
                              ({'inviteeProfileUrn': invitee_profile_urn}))
            response_dict = response.json()
            return response_dict


@app.route("/lazy-load-employee-status", methods=['POST'])
def lazy_load_employee_status():
    """
    It returns a list of employee data
    """
    if request.method == 'POST':
        request_data = request.get_json()
        li_at = json.loads(request.headers['liAt'])
        jsession_id = json.loads(request.headers['jSessionId'])
        lazy_loaded_actions_urns = request_data['lazyLoadedActionsUrns']

        response = get_lazy_load_employee_status(
            li_at, jsession_id, lazy_loaded_actions_urns)
        return response


def get_lazy_load_employee_status(li_at, jsession_id,
                                  lazy_loaded_actions_urns):
    """
    It takes a list of URNs, and returns a dictionary
    of URNs and their corresponding employee status

    :param li_at: This is the cookie that is used to authenticate the user
    :param jsession_id: This is the cookie that
    is set when you log in to LinkedIn
    :param lazy_loaded_actions_urns: This is a
    list of URNs that you want to get the employee status for
    :return: A dictionary with the key "membersStatus"
    and the value is a list of dictionaries.
    """
    url_encoded = ','.join(urllib.parse.quote(element, safe='')
                           for element in lazy_loaded_actions_urns)

    lazy_load_employee_status_link = urls["LAZY_LOAD_EMPLOYEE_DETAIL"].format(
        lazyLoadingUserIds=url_encoded
    )

    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
    }

    with requests.session() as s:
        s.cookies['li_at'] = li_at.get('value')
        s.cookies["JSESSIONID"] = jsession_id.get('value')
        s.headers = headers
        s.headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')
        response = s.get(lazy_load_employee_status_link)
        response_dict = response.json()
        results = response_dict['results']

        return {"membersStatus": nested_lookup('memberRelationship', results)}


if __name__ == "__main__":
    app.run(debug=True)
