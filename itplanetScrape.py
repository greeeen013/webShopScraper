import aiohttp
from bs4 import BeautifulSoup
import asyncio
# NEPOUZIVAT

async def itplanet_get_product_image(product_code):
    search_url = f"https://it-planet.com/de/search?sSearch={product_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Search for the product
            async with session.get(search_url, headers=headers) as response:
                response.raise_for_status()
                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')

            # Step 2: Find the first product box
            listing_div = soup.find('div', class_='listing')
            if not listing_div:
                print(f"No listing div found for {product_code}")
                return None

            first_product = listing_div.find('div', class_='product--box')
            if not first_product:
                print(f"No product boxes found for {product_code}")
                return None

            # Find the product link
            product_link_tag = first_product.find('a', class_='product--image')
            if not product_link_tag or not product_link_tag.get('href'):
                print(f"No product link found for {product_code}")
                return None

            product_url = product_link_tag['href']

            # Step 3: Follow the product link
            async with session.get(product_url, headers=headers) as product_response:
                product_response.raise_for_status()
                product_html = await product_response.text()

            product_soup = BeautifulSoup(product_html, 'html.parser')

            # Step 4: Find the image in the product page
            image_box = product_soup.find('div', class_='image--box')
            if not image_box:
                print(f"No image box found for {product_code}")
                return None

            img_tag = image_box.find('img', {'srcset': True})
            if not img_tag:
                print(f"No image with srcset found for {product_code}")
                return None

            # Extract the first URL from srcset
            srcset = img_tag['srcset']
            first_url = srcset.split(',')[0].strip().split()[0]

            return first_url

    except Exception as e:
        print(f"Error processing {product_code}: {str(e)}")
        return None


async def main():
    # Testovací produkty - nahraďte skutečnými kódy
    product_codes = ["SM-S918BZGD", "invalid_code", "SM-A546B", "SM-A336B", "SM-G991B"]

    # Spustí všech 5 požadavků současně
    tasks = [itplanet_get_product_image(code) for code in product_codes]
    results = await asyncio.gather(*tasks)

    for code, result in zip(product_codes, results):
        print(f"Product: {code} => Image: {result}")


if __name__ == "__main__":
    asyncio.run(main())