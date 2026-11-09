import requests
from datetime import datetime

url = "http://127.0.0.1:8000/api/"
data = {"username": "me", "password": "1"}

user={
    "username": "mejjj",
    "email": "mejjj@mail.com",
    "password1": "Ah123456",
    "password2": "Ah123456",
    "first_name": "hus",
    "last_name": "taha",
    "is_staff": True,
    "is_active": True
}
def login():
    try:
        response = requests.post(f'{url}users/auth/logins/', json=data)
        token=response.json().get('access')
        refresh = {"refresh":response.json().get('refresh')}
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    return token,refresh

#  caal login function
log= login()
token=log[0]
refresh=log[1]
print("Token",token)
print("Refresh",refresh)

def get_active_user():
    try:
        response = requests.get(f'{url}users/user/', headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        print("User",response.json())
    except requests.exceptions.HTTPError as err:
        print(err)

print("Active User:",get_active_user())       
        
def get_all_users():
    try:
        response = requests.get(f'{url}users/auth/users/', headers={"Authorization": f"Bearer {token}"})    
        response.raise_for_status()
        
        print("All Users",response.json())
    except requests.exceptions.HTTPError as err:
        print(err)
        
# print(get_all_users)
         
def refresh():
    try:
        response = requests.post(f'{url}users/auth/token/refresh/', json=refresh)
        print("Refresh",response.json())
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)


def logout():
    try:
        response = requests.post(f'{url}users/auth/logout/', json=token)
        print("Log Out ",response.json())
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        
    
def regiserUser():
    try:
        response = requests.post(f'{url}users/user/', json=data)
        print(response)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    return token,refresh
   

print("regiserUser",regiserUser())   


timestamp = 1739555382

def convert_time_stamp_to_date(timestamp):
    date_object = datetime.fromtimestamp(timestamp)
    return date_object, date_object.strftime("%Y%m%d")


date_object, date_as_numbers = convert_time_stamp_to_date(timestamp)
# print("Date Object", date_object)
# print("Date As Numbers", date_as_numbers)


def convert_date_to_timestamp(date):
    # تحويل السلسلة النصية إلى كائن datetime
    date_object = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    return int(date_object.timestamp())

# التاريخ والوقت كسلسلة نصية
date_string = '2025-02-14 22:11:30'
gettimstemb = convert_date_to_timestamp(date_string)
print("الطابع الزمني:", gettimstemb)




import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_login():
    client = APIClient()
    response = client.post("/api/auth/login/", {"username": "me", "password": "1"}, format="json")
    assert response.status_code == 200


# @pytest.mark.django_db
