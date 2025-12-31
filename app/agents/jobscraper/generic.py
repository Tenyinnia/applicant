# # app/services/scraper/generic.py

# import random
# import time
# import logging
# from dataclasses import dataclass
# from datetime import datetime, timezone, timedelta
# from typing import Optional, Dict, List
# from urllib.parse import urljoin
# from .job_boards 
# import requests
# from bs4 import BeautifulSoup

# logger = logging.getLogger(__name__)

# # =========================
# # PROXY + HEADERS
# # =========================

# PROXIES = [
#     "http://user:pass@proxy1:port",
#     "http://user:pass@proxy2:port",
#     "http://user:pass@proxy3:port",
# ]

# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/120.0.0.0 Safari/537.36"
#     ),
#     "Accept-Language": "en-US,en;q=0.9",
#     "Referer": "https://google.com",
# }

# # =========================
# # PROXY SESSION
# # =========================

# class ProxySession:
#     """
#     One proxy per scraping cycle
#     """
#     def __init__(self):
#         self.proxy = random.choice(PROXIES)
#         self.session = requests.Session()
#         self.session.headers.update(HEADERS)
#         self.session.proxies = {
#             "http": self.proxy,
#             "https": self.proxy,
#         }

#     def get(self, url: str, **kwargs):
#         return self.session.get(url, timeout=30, **kwargs)

# # =========================
# # JOB WEBSITES (V1)
# # =========================

# JOB_WEBSITES = [
#     "https://weworkremotely.com",
#     "https://remoteok.com",
#     "https://www.indeed.com",
#     "https://www.glassdoor.com",
#     "https://www.totaljobs.com",
#     "https://www.reed.co.uk",
#     # ⚠️ Add more gradually
# ]

# # =========================
# # UTILS
# # =========================

# def network_ok() -> bool:
#     try:
#         import socket
#         socket.gethostbyname("google.com")
#         return True
#     except:
#         return False

# # =========================
# # SCRAPER AGENT
# # =========================

# def scrape_cycle() -> Dict[str, str]:
#     """
#     One scraping cycle (safe for 5-minute APScheduler)
#     """
#     if not network_ok():
#         logger.warning("Network unavailable — skipping cycle")
#         return {}

#     ps = ProxySession()  # ONE proxy per cycle
#     results: Dict[str, str] = {}

#     logger.info(f"Using proxy: {ps.proxy}")

#     for url in JOB_WEBSITES:
#         try:
#             logger.info(f"Scraping {url}")
#             response = ps.get(url)
#             response.raise_for_status()

#             html_size = len(response.text)
#             results[url] = f"OK ({html_size} chars)"

#             # Soft delay (important)
#             time.sleep(random.uniform(2.5, 5.0))

#         except requests.exceptions.RequestException as e:
#             logger.warning(f"Failed {url}: {e}")
#             results[url] = f"ERROR: {e}"

#     return results

# def extract_posted_at(block) -> datetime:
#     # Try <time datetime="...">
#     time_tag = block.select_one("time")
#     if time_tag and time_tag.get("datetime"):
#         try:
#             return datetime.fromisoformat(time_tag["datetime"])
#         except:
#             pass

#     # Try regex for "2 days ago", "Posted 1 week ago", etc.
#     import re
#     text = block.get_text(" ", strip=True)
#     match = re.search(r'(\d+)\s+(day|week|month)s?\s+ago', text, re.I)
#     if match:
#         num = int(match.group(1))
#         unit = match.group(2).lower()
#         delta = {"day": 1, "week": 7, "month": 30}.get(unit, 1)
#         return datetime.utcnow() - timedelta(days=num * delta)

#     return datetime.utcnow()

# def scrape_site(cfg: SiteConfig, max_pages: int = 5) -> List[Dict]:
#     jobs = []
#     page = 1
#     cutoff = datetime.utcnow() - timedelta(days=14)

#     while page <= max_pages:
#         url = cfg.base_url
#         if cfg.paginate_param:
#             url += cfg.paginate_param.format(page=page)

#         r = requests.get(url, headers=cfg.headers or HEADERS, timeout=15)
#         r.raise_for_status()
#         soup = BeautifulSoup(r.text, "lxml")

#         blocks = soup.select(cfg.list_selector)
#         if not blocks:
#             break

#         for blk in blocks:
#             title = _txt(blk.select_one(cfg.title_selector))
#             company = _txt(blk.select_one(cfg.company_selector))
#             location = _txt(blk.select_one(cfg.location_selector)) if cfg.location_selector else None
#             desc = _txt(blk.select_one(cfg.desc_selector)) if cfg.desc_selector else ""
#             rel_link = blk.select_one(cfg.link_selector)["href"]
#             abs_link = urljoin(url, rel_link)

#             posted_at = extract_posted_at(blk) or datetime.utcnow()
#             if posted_at < cutoff:
#                 continue  # Skip old jobs

#             jobs.append({
#                 "external_id": rel_link.split("/")[-1],
#                 "title": title,
#                 "company": company,
#                 "location": location,
#                 "description": desc,
#                 "url": abs_link,
#                 "board": cfg.name,
#                 "posted_at": posted_at,
#                 "raw_payload": {"block": str(blk)},
#             })
#         page += 1
#     return jobs

# import scrapy

# class QuotesSpider(scrapy.Spider):
#     name = "quotes"

#     def start_requests(self):
#         urls = [
#             'https://quotes.toscrape.com/page/1/',
#             'https://quotes.toscrape.com/page/2/',
#         ]
#         for url in urls:
#             yield scrapy.Request(url=url, meta={'sops_country': 'uk'}, callback=self.parse)

#     def parse(self, response):
#         pass