import requests
from bs4 import BeautifulSoup
import asyncio

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
