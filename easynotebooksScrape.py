import requests
from bs4 import BeautifulSoup


async def easynotebooks_get_product_images(product_code):
    # Construct the search URL
    url = f"https://www.easynotebooks.de/search?sSearch={product_code}"

    # Send a GET request to the website
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
        return []

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the image slider div
    image_slider = soup.find('div', class_='image-slider--slide')

    if not image_slider:
        print("No image slider found for this product.")
        return []

    # Find all img tags with srcset attribute within the slider
    img_tags = image_slider.find_all('img', {'srcset': True})

    # Extract all srcset URLs
    image_urls = [img['srcset'] for img in img_tags]

    return image_urls