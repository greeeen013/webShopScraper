import requests
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup


def fourcrom_get_product_images(PNumber):
    # Load environment variables
    load_dotenv()

    # Debug print
    print(f"\n=== Starting process for PNumber: {PNumber} ===")

    # Create session to maintain cookies
    session = requests.Session()

    # Login data
    login_data = {
        'Usersystem-username': os.getenv('FOURCOM_USERNAME'),
        'Usersystem-password': os.getenv('FOURCOM_PASSWORD'),
        'Usersystem-userlogin': '1',
        'loginsource': 'wp'
    }

    # Login cookies
    cookies = {
        'PHPSESSID': os.getenv('PHPSESSID', 'lo88b8tulgoein2dqa6caa75ct'),
        'SRVNAME': os.getenv('SRVNAME', 'web01'),
        'adminLanguage': os.getenv('ADMIN_LANGUAGE', 'da'),
        'tcmspreviousurl': os.getenv('PREVIOUS_URL', '/forside'),
    }

    # Headers
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }

    # 1. Perform login
    print("\n[1/3] Attempting login...")
    login_url = 'https://shop-en.fourcom.dk/'
    login_response = session.post(login_url, cookies=cookies, headers=headers, data=login_data)

    print(f"Login status: {login_response.status_code}")
    print(f"Login response URL: {login_response.url}")

    if login_response.status_code != 200:
        print("!! Login failed !!")
        print(f"Response text start: {login_response.text[:200]}...")
        return {"error": f"Login failed with status {login_response.status_code}"}

    # 2. Search for the product
    print("\n[2/3] Searching for product...")
    search_url = f'https://shop.fourcom.dk/produktsoegning?ItemSearchPage-limit=100&ItemSearchPage-output-categories=1&ItemSearchPage-text={PNumber}'
    search_response = session.get(search_url, headers=headers)

    print(f"Search status: {search_response.status_code}")
    print(f"Search URL: {search_response.url}")
    print(f"First 500 chars of response:\n{search_response.text}...\n")

    if search_response.status_code != 200:
        print("!! Search failed !!")
        return {"error": f"Search failed with status {search_response.status_code}"}

    # 3. Parse the HTML to find image links
    print("[3/3] Parsing HTML for images...")
    soup = BeautifulSoup(search_response.text, 'html.parser')
    thumbs_div = soup.find('div', class_='thumbs')

    if not thumbs_div:
        print("!! No thumbs div found !!")
        print("Looking for other diagnostic elements...")

        # Check for common error elements
        error_div = soup.find('div', class_='error')
        if error_div:
            print(f"Error message found: {error_div.get_text(strip=True)}")

        # Check if we got redirected to login
        if "login" in search_response.url.lower():
            print("!! Appears to be redirected to login page !!")

        return {"error": "No product images found", "debug": {"response_sample": search_response.text[:500]}}

    # Extract all image links
    image_links = []
    gallery_links = thumbs_div.find_all('a', {'data-fancybox': 'gallery'})
    print(f"Found {len(gallery_links)} gallery links")

    for a_tag in gallery_links:
        if 'href' in a_tag.attrs:
            image_links.append(a_tag['href'])
            print(f"Found image: {a_tag['href']}")

    if not image_links:
        print("!! No images found in thumbs div !!")
        return {"error": "No images found in thumbs div", "debug": {"thumbs_div_content": str(thumbs_div)[:200]}}

    print(f"\n=== Success! Found {len(image_links)} images ===")
    return image_links


# Example usage:
if __name__ == "__main__":
    product_code = "SM-A566BZKAEUE"
    print(f"\nTesting with product code: {product_code}")
    images = get_product_images(product_code)

    print("\nFinal result:")
    print(images)