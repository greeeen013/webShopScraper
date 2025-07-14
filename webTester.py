import requests

def test_multiple_urls(urls):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"{url} -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"{url} -> ❌ Error: {type(e).__name__}")

# --- PŘÍKLAD POUŽITÍ ---
if __name__ == "__main__":
    urls_to_test = [
        "https://shop.api.de/search/352959",
        "https://directdeal.me/search?search=750709000",
        "https://en.fourcom.dk",
        "https://www.octo24.com/result.php?keywords=0830343003075",
        "https://www.easynotebooks.de/search?sSearch=IT0.005.050.675.1",
        "https://www.notebooksbilliger.de/produkte/A%2520455306",
        "https://it-planet.com/de/p/hp-v5c21aaabb-247918.html"
    ]

    test_multiple_urls(urls_to_test)
