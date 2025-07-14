import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

cookies = {
    'PHPSESSID': os.getenv('PHPSESSID', 'lo88b8tulgoein2dqa6caa75ct'),
    'SRVNAME': os.getenv('SRVNAME', 'web01'),
    'adminLanguage': os.getenv('ADMIN_LANGUAGE', 'da'),
    'tcmspreviousurl': os.getenv('PREVIOUS_URL', '/forside'),
}

headers = {
    'accept': '*/*',
    'accept-language': 'cs,en;q=0.9,de;q=0.8,da;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'dnt': '1',
    'origin': 'https://en.fourcom.dk',
    'priority': 'u=1, i',
    'referer': 'https://en.fourcom.dk/',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Opera GX";v="119"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
}

# Get credentials from environment variables
username = os.getenv('FOURCOM_USERNAME')
password = os.getenv('FOURCOM_PASSWORD')

data = {
    'Usersystem-username': username,
    'Usersystem-password': password,
    'Usersystem-userlogin': '1',
    'loginsource': 'wp'
}

response = requests.post('https://shop-en.fourcom.dk/',
                        cookies=cookies,
                        headers=headers,
                        data=data)

print(response)
print(response.text)
print(response.url)