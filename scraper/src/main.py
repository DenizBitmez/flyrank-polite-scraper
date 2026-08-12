import os
import requests

CACHE_DIR = "cache"
URL = "https://books.toscrape.com/catalogue/page-1.html"
CACHE_PATH = os.path.join(CACHE_DIR, "catalogue-page-1.html")

HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/DenizBitmez/flyrank-polite-scraper)"
}

def fetch_and_cache_first_page():
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    if os.path.exists(CACHE_PATH):
        print("CACHE HIT")
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"Response size: {len(content)} bytes")
        return content

    print("FETCH")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=5)
        
        if response.status_code != 200:
            raise Exception(f"Failed with status code: {response.status_code}")
        
        content = response.text
        
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Response size: {len(content)} bytes")
        return content

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        raise

if __name__ == "__main__":
    fetch_and_cache_first_page()