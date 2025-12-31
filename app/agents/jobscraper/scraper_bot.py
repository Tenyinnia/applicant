import requests
import json
import time
import logging
import re
import os
from bs4 import BeautifulSoup
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

from urllib.parse import urlparse, urljoin
from app.config import settings
from datetime import datetime
import concurrent.futures
import csv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UNSUPPORTED_DOMAINS = {
    "linkedin.com",
    "www.linkedin.com",
    "indeed.com",
    "www.indeed.com",
    "glassdoor.com",
    "www.glassdoor.com",
    "wellfound.com",
    
    
}

class ProxyEnhancedJobScraper:
    """Job scraper with ScrapeOps proxy integration to avoid blocks"""
    
    def __init__(self, scrapeops_api_key=None, use_proxy=True, max_workers=5):
        self.scrapeops_api_key =  settings.SCRAPEOPS_API_KEY or scrapeops_api_key
        self.use_proxy = use_proxy and self.scrapeops_api_key is not None
        self.max_workers = max_workers
        self.driver = None
        self.session = requests.Session()
        self.site_configs = {}
        self.failed_sites = []
        self.successful_sites = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Initialize session with proper headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Setup proxy configuration
        if self.use_proxy:
            self.proxy_config = self._setup_proxy_config()
            self.logger.info("🔒 ScrapeOps proxy enabled")
        else:
            self.proxy_config = None
            self.logger.warning("🚫 No proxy configured - may get blocked by some sites")
    
    def _setup_proxy_config(self):
        """Configure ScrapeOps proxy settings"""
        if not self.scrapeops_api_key:
            return None
        
        return {
            'proxy': {
                'http': f'http://scrapeops.headless_browser_mode=true:{self.scrapeops_api_key}@proxy.scrapeops.io:5353',
                'https': f'http://scrapeops.headless_browser_mode=true:{self.scrapeops_api_key}@proxy.scrapeops.io:5353',
                'no_proxy': 'localhost:127.0.0.1'
            }
        }
    
    def _setup_chrome_driver(self):
        """Setup Chrome driver with Selenium Wire for proxy support"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Additional anti-detection measures
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--proxy-server=direct://")
            chrome_options.add_argument("--proxy-bypass-list=*")
            
            # Use ChromeDriverManager to automatically download and manage ChromeDriver
            driver_options = {
                'request_storage_base_dir': '/tmp/seleniumwire',
                'request_storage_max_size': 1000,
            }
            
            if self.proxy_config:
                driver_options.update(self.proxy_config)
            
            # Create driver with proxy support
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(
                service=service,
                seleniumwire_options=driver_options,
                options=chrome_options
            )
            
            # Execute stealth scripts
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("window.chrome = {runtime: {}}")
            driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            return driver
            
        except Exception as e:
            self.logger.error(f"Chrome driver setup failed: {str(e)}")
            return None
    
    def get_comprehensive_job_websites(self):
        """Production-safe job websites (Scrapy + proxy friendly)"""
        return [
            # Major Aggregators
            
            "https://www.ziprecruiter.ie/jobs/search",
            "https://www.simplyhired.com",
            "https://talent.com",
            "https://www.adzuna.com",
            "https://www.careerjet.com",
            "https://getwork.com",

            # Tech & Startup Focused
            "https://builtin.com",

            
           "https://www.higheredjobs.com/search/today.cfm",
            "https://datasciencejobs.com/search",
            "https://www.roaddogjobs.com/search",

            # Remote Jobs (Excellent targets)
            "https://weworkremotely.com",
            "https://remoteok.com",
            "https://remote.co/remote-jobs",
            "https://4dayweek.io",
            "https://www.opentoworkremote.com",

            # Creative
            "https://dribbble.com/jobs",
            
            # Specialized Industries
            "https://www.efinancialcareers.com",
            
            "https://www.idealist.org/en/jobs",
            "https://www.devex.com/jobs/search",

            # Australia / NZ
            "https://www.seek.com.au",
            "https://www.seek.co.nz",
            "https://www.trademe.co.nz/jobs",
            "https://www.kiwihealthjobs.com",
            
            # UK & Ireland
            "https://www.reed.co.uk",
            "https://www.totaljobs.com",
            "https://www.cv-library.co.uk",
            "https://www.monster.co.uk",
            "https://www.irishjobs.ie",
            "https://www.jobs.ie",
            "https://www.s1jobs.com",

            # Canada
            "https://www.workopolis.com",

            # Asia
            "https://www.naukri.com",
            "https://www.bdjobs.com",

            # Europe (DACH + EU)
            "https://www.stepstone.de",
            "https://stellenanzeigen.de",
            "https://www.karriere.at",
            "https://www.jobs.ch",
            "https://www.pracuj.pl",
            "https://www.jobs.cz",
            "https://www.profesia.sk",
            "https://www.infojobs.net",
            "https://www.subito.it/lavoro",
            "https://www.kariera.gr",

            # Nordics
            "https://www.finn.no/job",
            "https://www.ofir.is",

            # France
            "https://www.cadremploi.fr",
            "https://www.apec.fr",

            # Middle East
            "https://www.bayt.com",
            "https://www.gulftalent.com",

            # Malta
            "https://www.keepmeposted.com.mt",

            # Visa / Relocation Friendly
            "https://www.myvisajobs.com",
            "https://h1bvisajobs.com",
            "https://visasponsor.jobs",
            "https://www.relocate.me",
            "https://www.jobbatical.com",

            # EU / Government Aggregator
            "https://eures.ec.europa.eu",
            "https://echojobs.io",
            "https://startup.jobs",
            "https://www.behance.net/joblist",
            "https://krop.com",
            "https://crunchboard.com",
        ]
        
    def inspect_with_proxy(self, url, max_retries=2, allow_fallback=True, max_pages=10):
        """
        Inspect a URL with proxy support and follow pagination links.
        Aggregates results from multiple pages.
        """
        self.logger.info(f"🔍 Inspecting {url} with proxy support")

        visited_urls = set()
        urls_to_visit = [url]
        all_results = []

        while urls_to_visit and len(visited_urls) < max_pages:
            current_url = urls_to_visit.pop(0)
            if current_url in visited_urls:
                continue

            visited_urls.add(current_url)
            self.logger.info(f"📄 Scraping page: {current_url}")

            for attempt in range(max_retries):
                try:
                    response = self.session.get(
                        current_url,
                        timeout=20,
                        proxies=self.proxy_config['proxy'] if self.use_proxy else None,
                        verify=False
                    )
                    response.raise_for_status()

                    soup = BeautifulSoup(response.content, "html.parser")
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Your existing strategies
                    strategies = [
                        self._strategy_common_class_names,
                        self._strategy_semantic_html,
                        self._strategy_itemscope_microdata,
                        self._strategy_data_attributes,
                        self._strategy_table_based,
                        self._strategy_list_based
                    ]

                    page_results = []
                    for strategy in strategies:
                        result = strategy(soup, current_url)
                        if result and result.get("total_jobs", 0) > 0:
                            result["resolved_url"] = current_url
                            page_results.append(result)

                    if page_results:
                        all_results.extend(page_results)

                    # 🔁 Detect pagination links on this page
                    pagination_links = self._extract_pagination_urls(soup, current_url)
                    for link in pagination_links:
                        if link not in visited_urls and link not in urls_to_visit:
                            urls_to_visit.append(link)

                    # Stop retry loop on success
                    break

                except Exception as e:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {current_url}: {str(e)}"
                    )
                    time.sleep(2 ** attempt)

            else:
                self.logger.warning(f"All attempts failed for {current_url}")

        # If nothing found, try fallback once
        if not all_results and allow_fallback:
            self.logger.info(f"🔄 Base URL failed, attempting fallbacks for {url}")
            fallback_result = self.inspect_with_fallback(url)
            if fallback_result:
                all_results.append(fallback_result)

        return all_results if all_results else None


    def _extract_pagination_urls(self, soup, base_url):
        """
        Find pagination links that contain ?page= or /page/ patterns
        """
        links = set()
        for a in soup.select("a[href]"):
            href = a.get("href")
            if href and re.search(r'(?:\?|/)page=\d+', href):
                full_url = urljoin(base_url, href)
                links.add(full_url)
        return sorted(links)


    
    def inspect_with_selenium_proxy(self, url):
        """Inspect website using Selenium with proxy support"""
        if not self.driver:
            self.driver = self._setup_chrome_driver()
            if not self.driver:
                return None
        
        try:
            self.logger.info(f"🌐 Loading {url} with Selenium + Proxy")
            self.driver.get(url)
            
            # Wait for page to load with multiple strategies
            wait_strategies = [
                (By.CSS_SELECTOR, "body"),
                (By.CSS_SELECTOR, "[class*='job']"),
                (By.CSS_SELECTOR, "main"),
                (By.CSS_SELECTOR, "article"),
                (By.CSS_SELECTOR, "h1, h2, h3")
            ]
            
            for strategy in wait_strategies:
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located(strategy)
                    )
                    break
                except:
                    continue
            
            # Get page source and parse
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Apply detection strategies
            strategies = [
                self._strategy_common_class_names,
                self._strategy_semantic_html,
                self._strategy_itemscope_microdata,
                self._strategy_data_attributes
            ]
            
            for strategy in strategies:
                result = strategy(soup, url)
                if result and result.get('total_jobs', 0) > 0:
                    result["js_required"] = True
                    result["proxy_used"] = self.use_proxy
                    return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Selenium proxy inspection failed for {url}: {str(e)}")
            return None
    
    def _get_alternative_user_agent(self):
        """Get alternative user agent to rotate"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        return user_agents[hash(str(time.time())) % len(user_agents)]
    
    def _strategy_common_class_names(self, soup, url):
        """Enhanced strategy with more comprehensive patterns"""
        common_patterns = [
            # Job containers
            '.job', '.jobs', '.job-listing', '.job-listings', '.position', '.positions',
            '.vacancy', '.vacancies', '.opportunity', '.opportunities', '.career', '.careers',
            '.job-item', '.job-card', '.job-result', '.job-search-result', '.listing-item',
            '.search-result', '.result-item', '.job-posting', '.job-ad', '.employment',
            
            # Remote specific
            '.remote-job', '.telecommute', '.work-from-home', '.distributed-team',
            
            # Table rows
            'tr.job', 'tr.position', 'tr[class*="job"]', 'tr[class*="position"]',
            
            # Modern frameworks and dynamic classes
            '[class*="JobCard"]', '[class*="JobItem"]', '[class*="JobListing"]',
            '[class*="job-card"]', '[class*="job-item"]', '[class*="job-listing"]',
            '[class*="position-card"]', '[class*="vacancy-card"]',
            
            # Indeed specific
            '.job_seen_beacon', '.slider_item', '.jobTitle',
            
            # LinkedIn specific
            '.jobs-search-results__list-item', '.job-card-container',
            
            # Glassdoor specific
            '.jobContainer', '.JobCard_jobCardContent',
            
            # Remote work specific
            '[class*="remote"]', '[class*="telecommute"]', '[class*="work-from-home"]'
        ]
        
        for pattern in common_patterns:
            try:
                elements = soup.select(pattern)
                if elements and len(elements) > 0:
                    result = self._analyze_job_elements(elements, url, pattern, "common_class_names")
                    if result:
                        return result
            except Exception as e:
                self.logger.debug(f"Pattern {pattern} failed: {str(e)}")
                continue
        
        return None
    
    def _strategy_semantic_html(self, soup, url):
        """Strategy: Look for semantic HTML5 elements"""
        semantic_patterns = [
            'article', 'section[class*="job"]', 'section[class*="career"]',
            'main article', 'main section', 'div[itemtype*="JobPosting"]',
            'div[typeof*="JobPosting"]', 'article[class*="job"]',
            'section[class*="position"]', 'article[class*="position"]'
        ]
        
        for pattern in semantic_patterns:
            try:
                elements = soup.select(pattern)
                if elements and len(elements) > 2:
                    result = self._analyze_job_elements(elements, url, pattern, "semantic_html")
                    if result:
                        return result
            except Exception as e:
                self.logger.debug(f"Semantic pattern {pattern} failed: {str(e)}")
                continue
        
        return None
    
    def _strategy_itemscope_microdata(self, soup, url):
        """Strategy: Look for microdata/schema.org markup"""
        microdata_patterns = [
            '[itemtype*="JobPosting"]', '[itemscope][itemtype*="JobPosting"]',
            '[typeof*="JobPosting"]', '[vocab*="schema.org"][typeof*="JobPosting"]',
            '[itemprop*="job"]', '[itemprop*="position"]'
        ]
        
        for pattern in microdata_patterns:
            try:
                elements = soup.select(pattern)
                if elements and len(elements) > 0:
                    result = self._analyze_job_elements(elements, url, pattern, "microdata")
                    if result:
                        return result
            except Exception as e:
                self.logger.debug(f"Microdata pattern {pattern} failed: {str(e)}")
                continue
        
        return None
    
    def _strategy_data_attributes(self, soup, url):
        """Strategy: Look for data attributes"""
        data_patterns = [
            '[data-job]', '[data-job-id]', '[data-position]', '[data-role]',
            '[data-testid*="job"]', '[data-test-id*="job"]', '[data-qa*="job"]',
            '[data-job-title]', '[data-company]', '[data-location]',
            '[data-id*="job"]', '[data-key*="job"]'
        ]
        
        for pattern in data_patterns:
            try:
                elements = soup.select(pattern)
                if elements and len(elements) > 0:
                    result = self._analyze_job_elements(elements, url, pattern, "data_attributes")
                    if result:
                        return result
            except Exception as e:
                self.logger.debug(f"Data attribute pattern {pattern} failed: {str(e)}")
                continue
        
        return None
    
    def _strategy_table_based(self, soup, url):
        """Strategy: Look for table-based job listings"""
        table_selectors = [
            'table.jobs-table tbody tr', 'table.job-table tbody tr',
            'table[class*="job"] tbody tr', 'table listings tbody tr',
            '.jobs-table tbody tr', '.job-table tbody tr',
            'table tbody tr[class*="job"]', 'table tbody tr[class*="position"]'
        ]
        
        for pattern in table_selectors:
            try:
                elements = soup.select(pattern)
                if elements and len(elements) > 2:
                    result = self._analyze_job_elements(elements, url, pattern, "table_based")
                    if result:
                        return result
            except Exception as e:
                self.logger.debug(f"Table pattern {pattern} failed: {str(e)}")
                continue
        
        return None
    
    def _strategy_list_based(self, soup, url):
        """Strategy: Look for list-based job listings"""
        list_selectors = [
            'ul.jobs-list li', 'ul.job-list li', 'ul.positions li',
            'ul.vacancies li', 'ol.jobs li', 'ol.job-listings li',
            '.jobs-list li', '.job-list li', '.positions-list li',
            'ul[class*="job"] li', 'ol[class*="job"] li'
        ]
        
        for pattern in list_selectors:
            try:
                elements = soup.select(pattern)
                if elements and len(elements) > 2:
                    result = self._analyze_job_elements(elements, url, pattern, "list_based")
                    if result:
                        return result
            except Exception as e:
                self.logger.debug(f"List pattern {pattern} failed: {str(e)}")
                continue
        
        return None
    
    def _analyze_job_elements(self, elements, url, container_selector, strategy):
        """Analyze job elements and extract field selectors with enhanced logic"""
        if not elements:
            return None
        
        # Analyze first few elements for patterns
        sample_elements = elements[:min(5, len(elements))]
        
        field_selectors = {
            "title": [],
            "company": [],
            "location": [],
            "salary": [],
            "job_type": [],
            "link": [],
            "description": []
        }
        
        # Enhanced field patterns
        title_patterns = [
            'h2', 'h3', 'h4', 'a', '[class*="title"]', '[class*="job-title"]', 
            '[class*="position"]', '[class*="role"]', '[class*="jobTitle"]',
            'h2 a', 'h3 a', 'h4 a', 'a h2', 'a h3'
        ]
        
        company_patterns = [
            '[class*="company"]', '[class*="employer"]', '[class*="organization"]', 
            '[class*="business"]', '[class*="firm"]', 'span.company', 'div.company',
            '[data-company]', '[itemprop="hiringOrganization"]'
        ]
        
        location_patterns = [
            '[class*="location"]', '[class*="place"]', '[class*="region"]', 
            '[class*="city"]', '[class*="state"]', '[class*="country"]',
            'span.location', 'div.location', '[data-location]', '[itemprop="jobLocation"]'
        ]
        
        salary_patterns = [
            '[class*="salary"]', '[class*="pay"]', '[class*="compensation"]', 
            '[class*="wage"]', '[class*="remuneration"]', '[class*="income"]',
            '[data-salary]', '[itemprop="baseSalary"]'
        ]
        
        link_patterns = [
            'a[href*="job"]', 'a[href*="position"]', 'a[href*="careers"]', 
            'a[href*="apply"]', 'a[href*="listing"]', 'h2 a', 'h3 a', 'h4 a',
            '[class*="apply-button"]', '[class*="view-job"]'
        ]
        
        description_patterns = [
            '[class*="description"]', '[class*="summary"]', '[class*="details"]',
            '[class*="snippet"]', '[class*="excerpt"]', 'p', 'div',
            '[itemprop="description"]', '[data-description]'
        ]
        
        for element in sample_elements:
            # Find title
            for pattern in title_patterns:
                title_elem = element.select_one(pattern)
                if title_elem and title_elem.get_text(strip=True):
                    field_selectors["title"].append(pattern)
                    break
            
            # Find company
            for pattern in company_patterns:
                company_elem = element.select_one(pattern)
                if company_elem and company_elem.get_text(strip=True):
                    field_selectors["company"].append(pattern)
                    break
            
            # Find location
            for pattern in location_patterns:
                location_elem = element.select_one(pattern)
                if location_elem and location_elem.get_text(strip=True):
                    field_selectors["location"].append(pattern)
                    break
            
            # Find salary
            for pattern in salary_patterns:
                salary_elem = element.select_one(pattern)
                if salary_elem and salary_elem.get_text(strip=True):
                    field_selectors["salary"].append(pattern)
                    break
            
            # Find link
            for pattern in link_patterns:
                link_elem = element.select_one(pattern)
                if link_elem and link_elem.get('href'):
                    field_selectors["link"].append(pattern)
                    break
            
            # Find description
            for pattern in description_patterns:
                desc_elem = element.select_one(pattern)
                if desc_elem and desc_elem.get_text(strip=True):
                    field_selectors["description"].append(pattern)
                    break
        
        # Build final selectors based on most common patterns
        result = {
            "url": url,
            "total_jobs": len(elements),
            "container_selector": container_selector,
            "strategy": strategy,
            "proxy_used": self.use_proxy,
            "selectors": {}
        }
        
        # Select most common selector for each field
        for field, patterns in field_selectors.items():
            if patterns:
                from collections import Counter
                counter = Counter(patterns)
                most_common = counter.most_common(1)[0]
                result["selectors"][field] = {
                    "selector": most_common[0],
                    "confidence": most_common[1] / len(sample_elements),
                    "example": self._get_example_text(sample_elements[0], most_common[0]) if sample_elements else None
                }
        
        return result
    
    def _get_example_text(self, element, selector):
        """Get example text from selector"""
        try:
            elem = element.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                return text[:100] + "..." if len(text) > 100 else text
        except:
            pass
        return None
    
    def generate_enhanced_siteconfig(self, url):
        """Generate enhanced siteconfig with proxy support"""
        domain = self._extract_domain(url)
        if domain in UNSUPPORTED_DOMAINS:
            self.logger.warning(f"⛔ Skipping unsupported site: {domain}")
            self.failed_sites.append(url)
            return None
        self.logger.info(f"🎯 Generating enhanced siteconfig for {url}")
        
        # Try multiple inspection methods
        inspection_result = None
        
        # Method 1: Proxy-enhanced requests
        if not inspection_result:
            inspection_result = self.inspect_with_proxy(url, allow_fallback=False)
        
        # Method 2: Selenium with proxy
        if not inspection_result and self.use_proxy:
            if not self.driver:
                self.driver = self._setup_chrome_driver()
            if self.driver:
                inspection_result = self.inspect_with_selenium_proxy(url)
        
        # Method 3: Fallback to basic requests
        if not inspection_result:
            self.logger.warning(f"Falling back to basic requests for {url}")
            inspection_result = self._fallback_inspect(url)
        
        if not inspection_result:
            self.failed_sites.append(url)
            self.logger.error(f"❌ Failed to generate siteconfig for {url}")
            return None
        
        
        
        siteconfig = {
            "domain": domain,
            "base_url": url,
            "generated_at": datetime.now().isoformat(),
            "version": "3.0",
            "proxy_config": {
                "scrapeops_enabled": self.use_proxy,
                "api_key_configured": self.scrapeops_api_key is not None
            },
            "inspection_results": inspection_result,
            "scraping_config": {
                "container_selector": inspection_result["container_selector"],
                "selectors": {},
                "js_required": inspection_result.get("js_required", False),
                "proxy_recommended": self.use_proxy,
                "strategy": inspection_result["strategy"],
                "confidence_score": 0,
                "retry_strategies": []
            },
            "metadata": {
                "total_jobs_detected": inspection_result["total_jobs"],
                "detection_method": inspection_result["strategy"],
                "proxy_used": inspection_result.get("proxy_used", False),
                "alternative_urls": self._get_alternative_urls(url),
                "regional_focus": self._detect_regional_focus(url),
                "specialization": self._detect_specialization(url),
                "blocking_risk": self._assess_blocking_risk(url)
            }
        }
        
        # Build scraping selectors with confidence scores and examples
        for field, data in inspection_result["selectors"].items():
            if isinstance(data, dict):
                siteconfig["scraping_config"]["selectors"][field] = {
                    "selector": data["selector"],
                    "confidence": data.get("confidence", 0.5),
                    "example": data.get("example"),
                    "fallback_selectors": self._generate_fallback_selectors(field)
                }
                siteconfig["scraping_config"]["confidence_score"] += data.get("confidence", 0)
        
        # Average confidence score
        if siteconfig["scraping_config"]["selectors"]:
            siteconfig["scraping_config"]["confidence_score"] /= len(siteconfig["scraping_config"]["selectors"])
        
        # Add retry strategies with proxy considerations
        siteconfig["scraping_config"]["retry_strategies"] = self._generate_enhanced_retry_strategies(url)
        
        self.successful_sites.append(url)
        self.logger.info(f"✅ Successfully generated enhanced siteconfig for {domain}")
        self.logger.info(f"   📊 Confidence: {siteconfig['scraping_config']['confidence_score']:.2f}")
        self.logger.info(f"   🔍 Strategy: {inspection_result['strategy']}")
        self.logger.info(f"   💼 Jobs detected: {inspection_result['total_jobs']}")
        
        return siteconfig
    
    def _fallback_inspect(self, url):
        """Basic fallback inspection without proxy"""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Simple job detection
            job_patterns = ['.job', '.jobs', '.position', '[class*="job"]']
            
            for pattern in job_patterns:
                elements = soup.select(pattern)
                if elements and len(elements) > 0:
                    return {
                        "url": url,
                        "total_jobs": len(elements),
                        "container_selector": pattern,
                        "strategy": "fallback_basic",
                        "proxy_used": False,
                        "selectors": {
                            "title": {"selector": "h2, h3, a", "confidence": 0.3},
                            "company": {"selector": "[class*='company']", "confidence": 0.3},
                            "location": {"selector": "[class*='location']", "confidence": 0.3}
                        }
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Fallback inspection failed for {url}: {str(e)}")
            return None
    
    def _assess_blocking_risk(self, url):
        """Assess blocking risk for a website"""
        domain = self._extract_domain(url)
        
        high_risk_indicators = [
            'indeed', 'linkedin', 'glassdoor', 'monster', 'careerbuilder'
        ]
        
        medium_risk_indicators = [
            'ziprecruiter', 'simplyhired', 'talent', 'adzuna', 'careerjet'
        ]
        
        if any(indicator in domain for indicator in high_risk_indicators):
            return "high"
        elif any(indicator in domain for indicator in medium_risk_indicators):
            return "medium"
        else:
            return "low"
    
    def _generate_enhanced_retry_strategies(self, url):
        """Generate enhanced retry strategies with proxy rotation"""
        domain = self._extract_domain(url)
        
        strategies = []
        
        # Priority-based strategies
        strategies.extend([
            {"method": "proxy_requests", "priority": 1, "requires_proxy": True},
            {"method": "session_with_headers", "priority": 2, "requires_proxy": False},
            {"method": "selenium_proxy", "priority": 3, "requires_proxy": True},
            {"method": "basic_requests", "priority": 4, "requires_proxy": False}
        ])
        
        # Domain-specific strategies
        if 'indeed' in domain:
            strategies.extend([
                {"method": "indeed_search_page", "priority": 5, "requires_proxy": True},
                {"method": "indeed_mobile_version", "priority": 6, "requires_proxy": False}
            ])
        elif 'linkedin' in domain:
            strategies.extend([
                {"method": "linkedin_public_jobs", "priority": 5, "requires_proxy": True},
                {"method": "linkedin_rss_feed", "priority": 6, "requires_proxy": False}
            ])
        elif 'glassdoor' in domain:
            strategies.extend([
                {"method": "glassdoor_api_approach", "priority": 5, "requires_proxy": True},
                {"method": "glassdoor_mobile_site", "priority": 6, "requires_proxy": False}
            ])
        
        return strategies
    
    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL safely"""
        try:
            parsed = urlparse(url)

            if parsed.netloc:
                return parsed.netloc.replace("www.", "").lower()

            if parsed.path:
                return parsed.path.split("/")[0].replace("www.", "").lower()

        except Exception:
            pass

        return "unknown"

    
    def _detect_regional_focus(self, url):
        """Detect regional focus of job website"""
        regional_indicators = {
            'australia': ['seek.com.au', '.au', 'australia'],
            'new_zealand': ['seek.co.nz', '.nz', 'kiwi', 'trademe'],
            'uk': ['.co.uk', 'reed', 'totaljobs', 'cv-library', 'monster.co.uk'],
            'ireland': ['.ie', 'irishjobs'],
            'canada': ['.gc.ca', 'workopolis', 'jobbank'],
            'india': ['naukri', '.in'],
            'bangladesh': ['bdjobs', '.bd'],
            'germany': ['stepstone', 'stellenanzeigen', 'xing', '.de'],
            'austria': ['karriere.at', '.at'],
            'switzerland': ['jobs.ch', '.ch'],
            'france': ['cadremploi', 'apec', '.fr'],
            'netherlands': ['werken.nl', 'monsterboard', '.nl'],
            'belgium': ['vdab', 'actiris', '.be'],
            'sweden': ['arbetsformedlingen', '.se'],
            'norway': ['finn.no', '.no'],
            'iceland': ['ofir.is', '.is'],
            'spain': ['infojobs', '.es'],
            'italy': ['subito.it', '.it'],
            'greece': ['kariera.gr', '.gr'],
            'poland': ['pracuj.pl', '.pl'],
            'czech': ['jobs.cz', '.cz'],
            'slovakia': ['profesia.sk', '.sk'],
            'ukraine': ['rabota.ua', '.ua'],
            'russia': ['hh.ru', '.ru'],
            'middle_east': ['bayt', 'gulftalent', 'qatarjobs', 'omantel'],
            'malta': ['keepmeposted.com.mt', '.mt'],
            'luxembourg': ['jobs.lu', '.lu']
        }
        
        url_lower = url.lower()
        for region, indicators in regional_indicators.items():
            if any(indicator in url_lower for indicator in indicators):
                return region
        
        return "global"
    
    def _detect_specialization(self, url):
        """Detect specialization of job website"""
        specializations = {
            'remote_work': ['remote', 'flexjobs', 'weworkremotely', 'remoteok', 'remote.co'],
            'tech': ['dice', 'stackoverflow', 'builtin', 'echojobs', 'crunchboard'],
            'creative': ['dribbble', 'behance', 'krop'],
            'freelance': ['upwork', 'fiverr', 'toptal'],
            'finance': ['efinancialcareers'],
            'construction': ['jobsinconstruction'],
            'education': ['higheredjobs'],
            'nonprofit': ['idealist', 'devex'],
            'aviation': ['avianation'],
            'road_transport': ['roaddogjobs'],
            'data_science': ['datasciencejobs'],
            'cybersecurity': ['cybercareers'],
            'healthcare': ['kiwihealthjobs'],
            'visa_sponsorship': ['visajobs', 'sponsorme', 'migratemate', 'visasponsor', 'eb3'],
            'relocation': ['relocate.me', 'jobbatical'],
            'startup': ['startup.jobs', 'wellfound'],
            'government': ['jobbank.gc.ca', 'eures', 'cybercareers']
        }
        
        url_lower = url.lower()
        for specialization, indicators in specializations.items():
            if any(indicator in url_lower for indicator in indicators):
                return specialization
        
        return "general"
    
    def _generate_fallback_selectors(self, field):
        """Generate fallback selectors for a field"""
        fallbacks = {
            "title": ['h2', 'h3', 'a', '[class*="title"]', '[class*="job"]'],
            "company": ['[class*="company"]', '[class*="employer"]', 'span', 'div'],
            "location": ['[class*="location"]', '[class*="place"]', 'span', 'div'],
            "salary": ['[class*="salary"]', '[class*="pay"]', '[class*="wage"]'],
            "link": ['a[href]', 'a'],
            "description": ['[class*="description"]', '[class*="summary"]', 'p', 'div']
        }
        return fallbacks.get(field, [])
    
    def _get_alternative_urls(self, url):
        domain = self._extract_domain(url)

        # Do NOT generate alternatives for major job boards
        if domain in UNSUPPORTED_DOMAINS:
            return []

        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        return [
            base,
            base + "/jobs",
            base + "/search",
            base + "/careers",
            base + "/vacancies",
            base + "/positions",
            
        ]
    def inspect_with_fallback(self, base_url):
        attempted = set()

        fallback_urls = self._get_alternative_urls(base_url)

        for url in fallback_urls:
            if url in attempted:
                continue

            attempted.add(url)
            self.logger.info(f"🔁 Trying fallback URL: {url}")

            result = self.inspect_with_proxy(url, allow_fallback=False)

            if result and result.get("total_jobs", 0) > 0:
                self.logger.info(f"✅ Jobs found at {url}")
                return result

            self.logger.warning(f"❌ No jobs at {url}, moving on")

        self.logger.error(f"🚫 All fallbacks exhausted for {base_url}")
        self.logger.info(f"➡️ Fallback sequence: {fallback_urls}")
        return None
 
    def process_sites_with_proxy(self, websites=None, max_workers=3, max_retries=2):
        if websites is None:
            websites = self.get_comprehensive_job_websites()
        
        self.logger.info(f"🚀 Processing {len(websites)} websites with proxy enhancement...")

        successful_configs = []
        failed_sites = websites.copy()
        attempt = 0

        while failed_sites and attempt <= max_retries:
            attempt += 1
            self.logger.info(f"🔁 Attempt {attempt} for {len(failed_sites)} sites...")
            current_failed = []

            batch_size = max_workers
            for i in range(0, len(failed_sites), batch_size):
                batch = failed_sites[i:i+batch_size]
                self.logger.info(f"📦 Processing batch {i//batch_size + 1}: {len(batch)} websites")

                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_url = {executor.submit(self.generate_enhanced_siteconfig, url): url for url in batch}
                    
                    for future in concurrent.futures.as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            config = future.result(timeout=360)
                            if config:
                                successful_configs.append(config)

                                # ✅ Save jobs to DB
                                job_items = config.get("jobs", [])
                                # saved_count = save_scraped_jobs(job_items, board_name=url)
                                # self.logger.info(f"✅ Saved {saved_count} jobs from {url}")

                                # Optional: save config if needed
                                self.save_siteconfig(config)
                            else:
                                current_failed.append(url)
                                self.logger.warning(f"❌ Failed: {url}")
                        except Exception as e:
                            current_failed.append(url)
                            self.logger.error(f"❌ Exception for {url}: {str(e)}")

            failed_sites = current_failed
            if failed_sites and attempt <= max_retries:
                self.logger.info(f"⏳ Waiting 30 seconds before retrying {len(failed_sites)} failed sites...")
                time.sleep(30)

        self._generate_proxy_summary_report(successful_configs, failed_sites)
        return successful_configs, failed_sites

    
    def save_siteconfig(self, siteconfig, filename=None):
        """Save siteconfig to JSON file"""
        if not filename:
            domain = siteconfig['domain'].replace('.', '_')
            filename = f"proxy_siteconfigs/{domain}_proxy_siteconfig.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(siteconfig, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Saved siteconfig: {filename}")
    
    def _generate_proxy_summary_report(self, successful_configs, failed_sites):
        """Generate comprehensive summary report for proxy-enhanced scraping"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "scrapeops_proxy_enabled": self.use_proxy,
            "total_websites_processed": len(successful_configs) + len(failed_sites),
            "successful_configs": len(successful_configs),
            "failed_configs": len(failed_sites),
            "success_rate": len(successful_configs) / (len(successful_configs) + len(failed_sites)) * 100 if (len(successful_configs) + len(failed_sites)) > 0 else 0,
            "regional_coverage": {},
            "specialization_coverage": {},
            "confidence_scores": [],
            "blocking_risk_analysis": {},
            "proxy_effectiveness": {},
            "failed_sites": failed_sites,
            "recommendations": []
        }
        
        # Analyze successful configs
        for config in successful_configs:
            region = config["metadata"]["regional_focus"]
            specialization = config["metadata"]["specialization"]
            risk_level = config["metadata"]["blocking_risk"]
            
            report["regional_coverage"][region] = report["regional_coverage"].get(region, 0) + 1
            report["specialization_coverage"][specialization] = report["specialization_coverage"].get(specialization, 0) + 1
            report["confidence_scores"].append(config["scraping_config"]["confidence_score"])
            report["blocking_risk_analysis"][risk_level] = report["blocking_risk_analysis"].get(risk_level, 0) + 1
            
            if config["metadata"]["proxy_used"]:
                report["proxy_effectiveness"][config["domain"]] = {
                    "confidence": config["scraping_config"]["confidence_score"],
                    "jobs_detected": config["metadata"]["total_jobs_detected"]
                }
        
        # Generate recommendations
        if self.use_proxy and len(report["proxy_effectiveness"]) > 0:
            avg_proxy_confidence = sum([data["confidence"] for data in report["proxy_effectiveness"].values()]) / len(report["proxy_effectiveness"])
            report["recommendations"].append(f"Proxy effectiveness: {avg_proxy_confidence:.2f} average confidence")
        
        if failed_sites:
            report["recommendations"].append("Consider upgrading ScrapeOps plan for higher request limits")
            report["recommendations"].append("Implement CAPTCHA solving for persistently blocked sites")
            report["recommendations"].append("Add request rate limiting and randomization")
        
        if successful_configs:
            avg_confidence = sum(report["confidence_scores"]) / len(report["confidence_scores"])
            report["average_confidence_score"] = avg_confidence
            
            if avg_confidence < 0.6:
                report["recommendations"].append("Manual review recommended for low-confidence selectors")
                report["recommendations"].append("Consider site-specific custom selectors")
        
        # Save report
        os.makedirs("reports", exist_ok=True)
        with open("reports/proxy_siteconfig_generation_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Also save as CSV
        self._save_proxy_csv_report(successful_configs)
        
        self.logger.info(f"📊 Proxy-enhanced summary report generated:")
        self.logger.info(f"   ✅ Successful: {len(successful_configs)}")
        self.logger.info(f"   ❌ Failed: {len(failed_sites)}")
        self.logger.info(f"   📈 Success Rate: {report['success_rate']:.1f}%")
        self.logger.info(f"   🔒 Proxy Used: {self.use_proxy}")
    
    def _save_proxy_csv_report(self, configs):
        """Save detailed proxy report as CSV"""
        os.makedirs("reports", exist_ok=True)
        
        with open("reports/proxy_siteconfig_details.csv", 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['domain', 'base_url', 'regional_focus', 'specialization', 
                         'blocking_risk', 'proxy_recommended', 'total_jobs_detected', 
                         'confidence_score', 'js_required', 'container_selector', 
                         'title_selector', 'company_selector', 'proxy_used']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for config in configs:
                row = {
                    'domain': config['domain'],
                    'base_url': config['base_url'],
                    'regional_focus': config['metadata']['regional_focus'],
                    'specialization': config['metadata']['specialization'],
                    'blocking_risk': config['metadata']['blocking_risk'],
                    'proxy_recommended': config['scraping_config']['proxy_recommended'],
                    'total_jobs_detected': config['metadata']['total_jobs_detected'],
                    'confidence_score': f"{config['scraping_config']['confidence_score']:.2f}",
                    'js_required': config['scraping_config']['js_required'],
                    'container_selector': config['scraping_config']['container_selector'],
                    'title_selector': config['scraping_config']['selectors'].get('title', {}).get('selector', ''),
                    'company_selector': config['scraping_config']['selectors'].get('company', {}).get('selector', ''),
                    'proxy_used': config['metadata']['proxy_used']
                }
                writer.writerow(row)
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        if self.session:
            self.session.close()

def main():
    """Main function to run the proxy-enhanced job scraper"""
    
    # ScrapeOps API Key (get from environment variable or replace with your key)
    SCRAPEOPS_API_KEY = settings.SCRAPEOPS_API_KEY
    
    print("🌍 Proxy-Enhanced Global Job Scraper")
    print("=" * 50)
    print()
    
    # Initialize scraper with proxy support
    scraper = ProxyEnhancedJobScraper(
        scrapeops_api_key=SCRAPEOPS_API_KEY,
        use_proxy=True,
        max_workers=3  # Lower to be respectful with proxy
    )
    
    # Get comprehensive job websites
    websites = scraper.get_comprehensive_job_websites()
    print(f"📋 Total websites to process: {len(websites)}")
    
    # Process websites with proxy enhancement
    successful_configs, failed_sites = scraper.process_sites_with_proxy(
        websites=websites[:60],  # Start with first 20 for testing
        max_workers=3
    )
    
    # Create master configuration file
    if successful_configs:
        master_config = {
            "version": "3.0",
            "generated_at": datetime.now().isoformat(),
            "scrapeops_proxy_enabled": True,
            "total_sites": len(websites),
            "successful_configs": len(successful_configs),
            "failed_configs": len(failed_sites),
            "success_rate": len(successful_configs) / (len(successful_configs) + len(failed_sites)) * 100,
            "configurations": successful_configs
        }
        
        os.makedirs("proxy_siteconfigs", exist_ok=True)
        with open("proxy_siteconfigs/master_proxy_siteconfig_v3.json", 'w', encoding='utf-8') as f:
            json.dump(master_config, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Files generated:")
        print("   - proxy_siteconfigs/individual site configs")
        print("   - proxy_siteconfigs/master_proxy_siteconfig_v3.json")
        print("   - reports/proxy_siteconfig_generation_report.json")
        print("   - reports/proxy_siteconfig_details.csv")
    
    # Final summary
    print("\n" + "="*50)
    print("🎯 FINAL SUMMARY")
    print(f"Total websites processed: {len(successful_configs) + len(failed_sites)}")
    print(f"Successful configurations: {len(successful_configs)}")
    print(f"Failed configurations: {len(failed_sites)}")
    print(f"Success rate: {len(successful_configs)/(len(successful_configs) + len(failed_sites))*100:.1f}%")
    print(f"Proxy protection: {'✅ Enabled' if scraper.use_proxy else '❌ Disabled'}")
    
    # Clean up
    scraper.close()
    
    print("\n✅ Proxy-enhanced job scraper siteconfig generation completed!")
    print("\n💡 Next steps:")
    print("   1. Review failed sites and consider manual configuration")
    print("   2. Test scraping with generated configs")
    print("   3. Consider upgrading ScrapeOps plan for higher limits")
    print("   4. Implement request rate limiting for production use")

if __name__ == "__main__":
    main()