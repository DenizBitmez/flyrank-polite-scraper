import os
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

CACHE_DIR = "cache"
BASE_URL = "https://books.toscrape.com/catalogue/"
FIRST_PAGE_URL = urljoin(BASE_URL, "page-1.html")

HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/DenizBitmez/flyrank-polite-scraper)"
}

def get_page_html(url, cache_filename):
    """Sayfayı önce cache'den arar, yoksa internetten çeker ve cache'ler."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, cache_filename)
    
    if os.path.exists(cache_path):
        print(f"CACHE HIT: {cache_filename}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    print(f"FETCH: Requesting live page -> {url}")
    # Nazik olmak için istekler arası bekleme kuralı (En az yarım saniye)
    time.sleep(0.5)
    
    response = requests.get(url, headers=HEADERS, timeout=5)
    if response.status_code != 200:
        raise Exception(f"Failed with status code: {response.status_code} for {url}")
    
    html_content = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return html_content

def discover_catalogue_pages():
    current_url = FIRST_PAGE_URL
    discovered_book_urls = set()
    catalogue_pages_count = 0

    # İlk 3 katalog sayfasını sırayla işleyelim
    for page_num in range(1, 4):
        cache_name = f"catalogue-page-{page_num}.html"
        html = get_page_html(current_url, cache_name)
        catalogue_pages_count += 1
        
        # Beautiful Soup ile HTML'i parse ediyoruz
        soup = BeautifulSoup(html, "html.parser")
        
        # Kitap linklerini toplama (article.product_pod içindeki h3 a etiketleri)
        books = soup.select("article.product_pod h3 a")
        for book in books:
            href = book.get("href")
            # Göreceli linkleri (relative URL) mutlak URL'ye (absolute URL) dönüştürme
            absolute_url = urljoin(current_url, href)
            discovered_book_urls.add(absolute_url)
            
        # Sitenin kendi "next" bağlantısını takip ederek sonraki sayfaya geçiş
        next_btn = soup.select_one("li.next a")
        if next_btn and page_num < 3:
            next_href = next_btn.get("href")
            current_url = urljoin(current_url, next_href)
        else:
            break

    print(f"\n--- DISCOVERY REPORT ---")
    print(f"catalogue_pages = {catalogue_pages_count}")
    print(f"discovered = {len(discovered_book_urls)}")
    print(f"unique_urls = {len(discovered_book_urls)}")
    
    return list(discovered_book_urls)

if __name__ == "__main__":
    discover_catalogue_pages()