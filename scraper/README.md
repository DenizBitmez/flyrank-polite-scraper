# The Polite Scraper (FlyRank Internship Backend Track)

## Target Classification & Politeness Rules
* **Target Site:** Books to Scrape (`https://books.toscrape.com`)[cite: 1]
* **Scope:** First 3 catalogue pages (discovering 60 unique books)[cite: 1]
* **Politeness Rules:**
  * **User-Agent:** Identifies the project clearly (`FlyRankInternship-A9/1.0`)[cite: 1].
  * **Delay:** At least 500 ms wait between live requests[cite: 1].
  * **Timeout:** 5-second request timeout[cite: 1].
  * **Cache:** Local HTML caching to prevent hammering the server during development[cite: 1].
* **Robots.txt:** `no robots file found` (404 Not Found)[cite: 1].
* **Limitation:** This scraper is hardcoded for the structure of Books to Scrape sandbox and will not adapt to generic e-commerce layouts without selector updates.

"I will not reuse this code on another site without checking its rules and terms first."[cite: 1]

## Tech Stack (Python Lane)
* Python 3.10+[cite: 1]
* Requests (HTTP client)[cite: 1]
* BeautifulSoup4 (HTML parser)[cite: 1]
* Pydantic (Schema validation)[cite: 1]

## Record Schema
Each validated book record adheres to this schema:
- `title` (string, required)
- `product_url` (string/URL, required)
- `price_text` (string, required)
- `price_gbp` (float, required, > 0)
- `availability_text` (string, required)
- `rating_text` (string, optional)
- `description` (string, optional)
- `source_page` (string, required)
- `fetched_at` (string ISO timestamp, required)

## How to Run (Under 5 Minutes)

1. Clone the repository and navigate to the project folder:
   ```bash
   git clone <repository-url>
   cd scraper

```

2. Install dependencies:
```bash
pip install requests beautifulsoup4 pydantic

```


3. Run the scraper:
```bash
python src/main.py

```



## Sample Run Report (`output/run-report.json`)

```json
{
  "start_time": "2026-08-12T21:00:00Z",
  "duration_seconds": 12.5,
  "pages_fetched": 61,
  "cache_hits": 0,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}

```

## Why No Browser Was Needed

The required data is fully present in the static HTML payload returned directly by the server, meaning a headless browser like Playwright would only add unnecessary memory and CPU overhead.

## Ethics Note

Always use an official API when available. Never bypass authentication, paywalls, or strict access blocks, and collect only the data necessary for the application's purpose.
