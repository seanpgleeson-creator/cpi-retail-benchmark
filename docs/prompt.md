# CPI Data MVP

Tue, 30 Sept 25

**System / Developer message (goals & guardrails)** You are an experienced Python engineer building an MVP that benchmarks Target.com milk prices against BLS CPI milk data. Produce production-quality, well-commented code and a runnable README. Use **Python 3.11**, **Playwright (Chromium)** for scraping, **Requests** for APIs, and **SQLite** (via SQLAlchemy) for storage. Favor small focused modules with clear interfaces and unit tests (pytest). Include a .env.example.

**Hard requirements**

- **BLS module**
  - Functions to pull:
    - CPI-U Milk index (series id strings passed in; default CUUR0000SEFJ01 (NSA), CUSR0000SEFJ01 (SA)).
    - Average price series APU0000709112 (Milk, whole, per gallon).
  - Use BLS public API JSON; store to bls_series and bls_observations.
  - Helper to compute MoM and YoY % changes and a rebased index (base=100 at the first observation in DB).
- **Target scraper**
  - Playwright script that:
    - Accepts zip_code (default: **55331**), and a list of search/category URLs.
    - Sets location on Target (store/fulfillment) to the ZIP (via UI steps or query params).
    - Queries “milk” and the dairy category and filters for gallon (128 fl oz) and ½-gallon (normalize to gallon).
    - Captures: title, brand, size_qty, size_unit, price, unit_price_per_gal, url, product_id/TCIN if available, availability.
    - Rate-limits; random waits/jitter; user-agent rotation; retries; robust selectors.
    - Writes/updates products and appends to prices with observed_at timestamp.
  - **Normalization**: Implement a simple size/unit parser (oz, fl oz, qt, gal) and convert to **$/gallon**.
- **Basket builder**
  - Monthly task:
    - From the latest scrape, pick a **fixed basket** for the month: at least 2 SKUs (store brand + national brand) that are in stock and gallon-equivalent. Save to baskets + basket_items.
    - Freeze that list for the month (no churn).
- **Computation & Compare**
  - Compute **Target Milk average $/gal** for the basket (equal weights), MoM and YoY.
  - Pull latest BLS observations for APU0000709112 and/or CU*SEFJ01, compute MoM/YoY.
  - Output comparison: Δ(Target) vs Δ(BLS) with labels {Above, Inline (±0.2pp), Below}.
- **CLI & Reports**
  - python app.py scrape --zip 55331
  - python app.py build-basket --month 2025-09
  - python app.py bls-pull
  - python app.py compare --month 2025-09
  - python app.py export --month 2025-09 --out results_2025-09.csv
- **Scheduling**
  - Provide a tasks.yaml with suggested cron schedules:
    - End-of-month scrape window (e.g., last 3 days + last day).
    - CPI release morning scrape + bls-pull + compare (BLS release times are on the CPI calendar).
- **Testing**
  - Unit tests for: unit parsing, $/gal normalization, MoM/YoY math, BLS client pagination/schemas.
- **Documentation**
  - README.md with setup (Playwright install), environment variables, series IDs table, usage examples, and caveats on robots.txt/ToS.

**Project layout**

/cpi-retail-benchmark app.py /bls_client/ **init**.py api.py # GET series, validate, persist compute.py # MoM/YoY, rebase /scrapers/target/ **init**.py milk_scraper.py # Playwright flows + parsers normalize.py # size parsing + gallon conversion /db/ models.py # SQLAlchemy schema.sql /basket/ builder.py compute.py /reports/ compare.py export.py /tests/ test_normalize.py test_compute.py test_bls.py README.md .env.example requirements.txt tasks.yaml

**Implementation details**

- **Requirements**: playwright, requests, pydantic, sqlalchemy, python-dotenv, tenacity, pytest, pytz, dateparser.
- **Env vars**: BLS_API_KEY (optional), ZIP_CODE, HEADLESS=true, SCRAPE_MAX_PAGES=5, SCRAPE_DELAY_RANGE_MS=500-1500.
- **BLS defaults**:
  - Index (Milk): CUUR0000SEFJ01 (NSA), and optionally CUSR0000SEFJ01 (SA).
  - Average Price (Milk, whole, per gal): APU0000709112.
  - (Document series-ID conventions in README; allow overrides via CLI.) Bureau of Labor Statistics+1
- **Normalization**:
  - Regex for sizes (e.g., (\d+(\.\d+)?)\s*(fl\s*oz|oz|qt|pt|gal|gallon|ml|l)) → convert to gallons (1 gal=128 fl oz; 1 qt=32 fl oz; 1 L≈33.814 fl oz). Compute unit_price_per_gal= price / gallons.
- **Basket selection policy** (MVP):
  - Keep 2–4 SKUs: _Good & Gather Whole Milk 1 Gal_, plus one national brand _1 Gal_. If 1 gal unavailable, include 2× ½-gal normalized. Freeze list for the month.
- **Comparison logic**:
  - For month _m_:
    - Target: avg_price_gal[m], compute mom=(m/m-1 - 1), yoy=(m/m-12 - 1).
    - BLS: pull same month for APU0000709112 and/or CUUR0000SEFJ01, compute MoM/YoY.
    - Verdict thresholds: abs(TargetΔ - BLSΔ) <= 0.2pp => "Inline", else above/below.

**Non-functional**

- Respect **robots.txt/ToS** and add throttle, backoff, and a --dry-run flag. If scraping is blocked, print guidance to switch to licensed data providers. scrapeops.io+1

**Deliverables**

- Fully running CLI, example output CSV, and a sample monthly report printed to stdout like:

Month: 2025-09, ZIP: 55331 Target Milk Avg $/gal: 3.99 (MoM +0.7%, YoY -1.2%) BLS Avg $/gal (APU0000709112): 4.17 (MoM +0.2%, YoY +3.7%) Verdict: Target ABOVE BLS by +0.5pp (MoM)

##