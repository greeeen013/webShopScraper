import requests
from bs4 import BeautifulSoup
import asyncio


async def octo_get_product_images(product_code):
    # First stage - search page
    search_url = f"https://www.octo24.com/result.php?keywords={product_code}"
    print(f"[DEBUG] Searching product at: {search_url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Get search results
        print("[DEBUG] Fetching search results...")
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"[DEBUG] Search page status: {response.status_code}")

        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch search page, status: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find product container
        print("[DEBUG] Looking for product container...")
        product_container = soup.find('div', class_='flex_listing_container')

        if not product_container:
            print("[ERROR] No product container found on search page")
            return []

        print("[DEBUG] Found product container, looking for first product link...")
        first_product = product_container.find('div', class_='listing_item_box')

        if not first_product:
            print("[ERROR] No products found in container")
            return []

        product_link = first_product.find('a', href=True)

        if not product_link:
            print("[ERROR] No product link found")
            return []

        product_url = product_link['href']
        print(f"[DEBUG] Found product URL: {product_url}")

        # Second stage - product page
        print("[DEBUG] Fetching product page...")
        product_response = requests.get(product_url, headers=headers, timeout=10)
        print(f"[DEBUG] Product page status: {product_response.status_code}")

        if product_response.status_code != 200:
            print(f"[ERROR] Failed to fetch product page, status: {product_response.status_code}")
            return []

        product_soup = BeautifulSoup(product_response.text, 'html.parser')

        # Find image container
        print("[DEBUG] Looking for image container...")
        image_container = product_soup.find('div', class_='pd_image_container')

        if not image_container:
            print("[ERROR] No image container found on product page")
            return []

        print("[DEBUG] Found image container, extracting all images...")
        images = image_container.find_all('img', src=True)
        print(f"[DEBUG] Found {len(images)} image elements")

        image_urls = []
        for i, img in enumerate(images, 1):
            src = img['src']
            if src:
                # Handle protocol-relative URLs
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.octo24.com' + src

                image_urls.append(src)
                print(f"[DEBUG] Image {i} src: {src}")

        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in image_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        print(f"[DEBUG] Found {len(unique_urls)} unique image URLs")
        return unique_urls

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network request failed: {str(e)}")
        return []
    except Exception as e:
        print(f"[ERROR] Processing failed: {str(e)}")
        return []