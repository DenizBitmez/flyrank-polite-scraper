from datetime import datetime, timezone
import json
import os
import re
import time
from typing import Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError

CACHE_DIR = "cache"
OUTPUT_DIR = "output"
BASE_URL = "https://books.toscrape.com/catalogue/"
FIRST_PAGE_URL = urljoin(BASE_URL, "page-1.html")

HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/DenizBitmez/flyrank-polite-scraper)"
}


class BookRecord(BaseModel):
  title: str = Field(..., min_length=1)
  product_url: str
  price_text: str
  price_gbp: float = Field(..., gt=0)
  availability_text: str
  rating_text: Optional[str] = None
  description: Optional[str] = None
  source_page: str
  fetched_at: str


def get_page_html(url, cache_filename, metrics):
  os.makedirs(CACHE_DIR, exist_ok=True)
  cache_path = os.path.join(CACHE_DIR, cache_filename)

  if os.path.exists(cache_path):
    metrics["cache_hits"] += 1
    with open(cache_path, "r", encoding="utf-8") as f:
      return f.read()

  time.sleep(0.5)
  metrics["pages_fetched"] += 1

  max_retries = 2
  for attempt in range(1, max_retries + 1):
    try:
      response = requests.get(url, headers=HEADERS, timeout=5)

      if response.status_code in [403, 404]:
        print(f"Client Error {response.status_code} for {url}. Skipping retry.")
        metrics["failed_pages"] += 1
        return None

      if response.status_code >= 500:
        print(
            f"Server Error {response.status_code} on attempt {attempt} for"
            f" {url}."
        )
        if attempt < max_retries:
          time.sleep(1)
          continue
        else:
          metrics["failed_pages"] += 1
          return None

      if response.status_code != 200:
        metrics["failed_pages"] += 1
        return None

      html_content = response.text
      with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html_content)
      return html_content

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
      print(f"Network/Timeout error on attempt {attempt} for {url}: {e}")
      if attempt < max_retries:
        time.sleep(1)
        continue
      else:
        metrics["failed_pages"] += 1
        return None
    except Exception as e:
      print(f"Unexpected error for {url}: {e}")
      metrics["failed_pages"] += 1
      return None

  metrics["failed_pages"] += 1
  return None


def discover_catalogue_pages(metrics):
  current_url = FIRST_PAGE_URL
  discovered_books = []

  for page_num in range(1, 4):
    cache_name = f"catalogue-page-{page_num}.html"
    html = get_page_html(current_url, cache_name, metrics)
    if not html:
      continue

    soup = BeautifulSoup(html, "html.parser")
    books = soup.select("article.product_pod h3 a")
    for book in books:
      href = book.get("href")
      absolute_url = urljoin(current_url, href)
      discovered_books.append((absolute_url, current_url))

    next_btn = soup.select_one("li.next a")
    if next_btn and page_num < 3:
      next_href = next_btn.get("href")
      current_url = urljoin(current_url, next_href)
    else:
      break

  unique_books = {}
  for b_url, s_page in discovered_books:
    if b_url not in unique_books:
      unique_books[b_url] = s_page

  return unique_books


def run_scraper_pipeline():
  start_time = datetime.now(timezone.utc)
  metrics = {
      "pages_fetched": 0,
      "cache_hits": 0,
      "failed_pages": 0,
      "valid_records": 0,
      "invalid_records": 0,
  }

  unique_books = discover_catalogue_pages(metrics)

  fake_url = "https://books.toscrape.com/catalogue/this-page-does-not-exist-999.html"
  unique_books[fake_url] = "https://books.toscrape.com/catalogue/page-1.html"

  raw_records = []

  print(
      f"\nStarting to fetch detail pages for {len(unique_books)} items (including"
      " 1 intentional fake URL)..."
  )

  for idx, (book_url, source_page) in enumerate(unique_books.items(), 1):
    book_cache_name = f"book-{idx}.html"
    html = get_page_html(book_url, book_cache_name, metrics)

    if not html:
      print(f"Skipping failed or broken page: {book_url}")
      continue

    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one("div.product_main h1")
    title = title_el.get_text(strip=True) if title_el else None

    price_el = soup.select_one("div.product_main p.price_color")
    price_text = price_el.get_text(strip=True) if price_el else None

    avail_el = soup.select_one("div.product_main p.availability")
    availability_text = avail_el.get_text(strip=True) if avail_el else None

    rating_el = soup.select_one("p.star-rating")
    rating_text = None
    if rating_el and rating_el.get("class"):
      classes = rating_el.get("class")
      if len(classes) > 1:
        rating_text = classes[1]

    desc_heading = soup.select_one("#product_description")
    description = None
    if desc_heading:
      desc_p = desc_heading.find_next_sibling("p")
      if desc_p:
        description = desc_p.get_text(strip=True)

    fetched_at = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    raw_records.append({
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    })

  os.makedirs(OUTPUT_DIR, exist_ok=True)
  valid_records = []
  error_records = []
  seen_urls = set()

  for record in raw_records:
    price_val = record.get("price_text")
    price_gbp = 0.0
    if price_val:
      numeric_string = re.sub(r"[^\d.]", "", price_val)
      try:
        price_gbp = float(numeric_string)
      except ValueError:
        price_gbp = 0.0

    record["price_gbp"] = price_gbp

    canonical_url = record.get("product_url")
    if canonical_url in seen_urls:
      continue
    seen_urls.add(canonical_url)

    try:
      validated_model = BookRecord(**record)
      valid_records.append(validated_model.model_dump())
      metrics["valid_records"] += 1
    except ValidationError as e:
      error_records.append({"record": record, "errors": e.errors()})
      metrics["invalid_records"] += 1

  books_path = os.path.join(OUTPUT_DIR, "books.json")
  errors_path = os.path.join(OUTPUT_DIR, "errors.json")
  report_path = os.path.join(OUTPUT_DIR, "run-report.json")

  with open(books_path, "w", encoding="utf-8") as f:
    json.dump(valid_records, f, indent=2, ensure_ascii=False)

  with open(errors_path, "w", encoding="utf-8") as f:
    json.dump(error_records, f, indent=2, ensure_ascii=False)

  end_time = datetime.now(timezone.utc)
  duration_seconds = (end_time - start_time).total_seconds()

  run_report = {
      "start_time": start_time.isoformat(timespec="seconds").replace(
          "+00:00", "Z"
      ),
      "duration_seconds": round(duration_seconds, 2),
      "pages_fetched": metrics["pages_fetched"],
      "cache_hits": metrics["cache_hits"],
      "valid_records": metrics["valid_records"],
      "invalid_records": metrics["invalid_records"],
      "failed_pages": metrics["failed_pages"],
  }

  with open(report_path, "w", encoding="utf-8") as f:
    json.dump(run_report, f, indent=2, ensure_ascii=False)

  print(f"\n--- STAGE 5 RUN REPORT ---")
  print(json.dumps(run_report, indent=2))


if __name__ == "__main__":
  run_scraper_pipeline()