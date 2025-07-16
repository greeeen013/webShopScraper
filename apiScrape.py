import requests
from bs4 import BeautifulSoup


def api_get_product_images(PNumber):
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


# Testování
if __name__ == "__main__":
    print("=== Starting test ===")
    test_pnumber = "352959"
    images = api_get_product_images(test_pnumber)
    print(images)

    print("\n=== Results ===")
    if images:
        for i, img_url in enumerate(images, 1):
            #print(f"Image {i}: {img_url}")
            print(f"{img_url};")
    else:
        print("No images found or an error occurred")