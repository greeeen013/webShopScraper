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

async def directdeal_get_product_images(product_code):
    url = f"https://directdeal.me/search?search={product_code}"
    print(f"[DEBUG] Target URL: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        print("[DEBUG] Making request with headers...")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"[DEBUG] Status code: {response.status_code}")

        # Uložme HTML do souboru pro inspekci
        #with open('debug_page.html', 'w', encoding='utf-8') as f:
        #    f.write(response.text)
        #print("[DEBUG] HTML content saved to debug_page.html")

        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Zkusme najít přímo galerii
        gallery = soup.find('div', {'id': 'tns17-mw'})
        if gallery:
            print("[DEBUG] Found gallery via ID tns17-mw")
            tns_ovh = gallery
        else:
            # 2. Zkusme najít podle třídy
            print("[DEBUG] Trying to find by class 'tns-ovh'")
            tns_ovh = soup.find('div', class_='tns-ovh')

        if not tns_ovh:
            print("[DEBUG] Fallback - searching for any image gallery container")
            # 3. Zkusme najít jakýkoli kontejner s obrázky
            possible_containers = soup.find_all(['div', 'section'], class_=lambda x: x and 'gallery' in x.lower())
            print(f"[DEBUG] Found {len(possible_containers)} potential gallery containers")
            tns_ovh = possible_containers[0] if possible_containers else None

        if not tns_ovh:
            print("[DEBUG] CRITICAL: No gallery container found at all!")
            print("[DEBUG] All div classes found:",
                  {div.get('class') for div in soup.find_all('div') if div.get('class')})
            return []

        print("[DEBUG] Found container, searching for images...")
        images = tns_ovh.find_all('img', class_=lambda x: x and 'image' in x.lower())

        if not images:
            print("[DEBUG] No images found with class filters, trying all img tags")
            images = tns_ovh.find_all('img')

        image_urls = []
        for img in images:
            src = img.get('src') or img.get('data-src') or img.get('data-full-image')
            if src:
                if src.startswith(('//', '/')):
                    src = f"https:{src}" if src.startswith('//') else f"https://directdeal.me{src}"
                image_urls.append(src)
                #print(f"[DEBUG] Found image: {src}")

        # Remove duplicates
        unique_urls = []
        seen = set()
        for url in image_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        print(f"[DEBUG] Found {len(unique_urls)} unique images")
        return unique_urls

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return []

async def api_get_product_images(PNumber):
    url = f"https://shop.api.de/product/details/{PNumber}"
    print(f"[DEBUG] Target URL: {url}")

    try:
        # Nastavení hlavičky, aby to vypadalo jako běžný prohlížeč
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        print("[DEBUG] Making HTTP request with headers...")
        response = requests.get(url, headers=headers)
        print(f"[DEBUG] HTTP Status Code: {response.status_code}")

        response.raise_for_status()

        #print(f"[DEBUG] First 500 chars of response:\n{response.text[:500]}\n...")

        soup = BeautifulSoup(response.text, 'html.parser')

        print("[DEBUG] Searching for ALL img.slick-img elements...")
        images = soup.find_all('img', class_='slick-img')
        print(f"[DEBUG] Found {len(images)} image elements")

        image_urls = []
        for i, img in enumerate(images, 1):
            src = img.get('src')
            if src:
                # Některé obrázky mohou mít relativní URL, převedeme je na absolutní
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://shop.api.de' + src

                image_urls.append(src)
                #print(f"[DEBUG] Image {i} src: {src}")
            else:
                print(f"[DEBUG] Image {i} has no src attribute")

        print(f"[DEBUG] Returning {len(image_urls)} image URLs")
        return image_urls

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return []

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

async def kosatec_get_product_images(PNumber):
    # First stage - search page
    search_url = f"https://shop.kosatec.de/factfinder/result?query={PNumber}"
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

        # Find first product link
        print("[DEBUG] Looking for product link...")
        product_container = soup.find('div', class_='cms-listing-col')
        if not product_container:
            print("[ERROR] No product container found")
            return []

        product_link = product_container.find('a', href=True)
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

        # Find image gallery
        print("[DEBUG] Looking for image gallery...")
        gallery_container = product_soup.find('div', class_='tns-inner')
        if not gallery_container:
            gallery_container = product_soup.find('div', class_='gallery-slider-container')

        if not gallery_container:
            print("[ERROR] No gallery container found")
            return []

        # Extract all image elements
        images = gallery_container.find_all('img', class_='gallery-slider-image')
        if not images:
            print("[DEBUG] No gallery images found, trying alternative approach")
            images = gallery_container.find_all('img', src=True)

        print(f"[DEBUG] Found {len(images)} image elements")

        image_urls = []
        for img in images:
            # Prefer data-full-image if available, otherwise use src
            url = img.get('data-full-image') or img.get('src')
            if url:
                # Handle protocol-relative URLs
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    url = 'https://shop.kosatec.de' + url

                image_urls.append(url)

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



if __name__ == "__main__":
    print(asyncio.run(kosatec_get_product_images(21230357)))