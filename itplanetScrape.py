import requests
from bs4 import BeautifulSoup


def itplanet_get_product_image(product_code):
    # Step 1: Search for the product
    search_url = f"https://it-planet.com/de/search?sSearch={product_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Get search results page
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Step 2: Find the first product box
        listing_div = soup.find('div', class_='listing')
        if not listing_div:
            print("No listing div found on search page.")
            return None

        first_product = listing_div.find('div', class_='product--box box--minimal hover-actions')
        if not first_product:
            print("No product boxes found in listing.")
            return None

        # Find the product link
        product_link_tag = first_product.find('a', class_='product--image')
        if not product_link_tag or not product_link_tag.get('href'):
            print("No product link found in product box.")
            return None

        product_url = product_link_tag['href']

        # Step 3: Follow the product link
        product_response = requests.get(product_url, headers=headers)
        product_response.raise_for_status()

        product_soup = BeautifulSoup(product_response.text, 'html.parser')

        # Step 4: Find the image in the product page
        image_box = product_soup.find('div', class_='image--box image-slider--item')
        if not image_box:
            print("No image box found on product page.")
            return None

        img_tag = image_box.find('img', {'srcset': True})
        if not img_tag:
            print("No image with srcset found in image box.")
            return None

        # Extract just the first URL from srcset
        srcset = img_tag['srcset']
        first_url = srcset.split(',')[0].strip()

        return first_url

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Example usage
product_code = "CK3XAC4K001W4100"
image_url = itplanet_get_product_image(product_code)

if image_url:
    print(f"Found image URL for product {product_code}:")
    print(image_url)
else:
    print(f"No image found for product {product_code}")