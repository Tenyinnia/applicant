
# import requests
# from app.config import settings
# from urllib.parse import urlencode

# DOWNLOADER_MIDDLEWARES = {
#     'scrapeops_scrapy_proxy_sdk.scrapeops_scrapy_proxy_sdk.ScrapeOpsScrapyProxySdk': 725,
# } 
# proxy_params = {
#       'api_key': settings.SCRAPEOPS_API_KEY,
#       'url': 'https://www.linkedin.com/jobs/search/', 
#       'render_js': True,
#   }

# response = requests.get(
#   url='https://proxy.scrapeops.io/v1/',
#   params=urlencode(proxy_params),
#   timeout=120,
# )

# print('Body: ', response.content)
import scrapy

class LinkedinSpider(scrapy.Spider):
    name ="linked_jobs"
    api_url = "https://www.linkedin.com/jobs/search/?currentJobId="

    def start_requests(self):
        first_job_on_page = 0
        first_url = self.api_url + str(first_job_on_page)
        yield scrapy.Request(url=first_url, callback=self.parse_job, meta={"first_job_on_page": first_job_on_page})
    
    def parse_job(self, response):
        first_job_on_page = response.meta["first_job_on_page"]
        jobs = response.css(".bCCrUjwKPQkFwRvrUVWdrQmfudPffGOibE li")
        number_of_jobs_returned = len(jobs)
        for job in jobs:
            job_item = {}
            job_item["title"] = job.css(".full-width .artdeco-entity-lockup__title .ember-view::text").get(default="not-found").strip()
            job_item["company"] = job.css(".artdeco-entity-lockup__subtitle .ember-view::text").get(default="not-found").strip()
            job_item["location"] = job.css(".full-width .artdeco-entity-lockup__title .ember-view::text").get(default="not-found").strip()
            job_item["description"] = job.css("artdeco-entity-lockup__caption ember-view::text").get(default="not-found").strip()
            job_item["url"] = job.css("a .disabled ember-view job-card-container__link::attr(href)").get(default="not-found").strip()
            job_item["external_url"] = job.css("a::attr(href)").get(default="not-found").strip()
            job_item["posted_at"] = job.css(".job-card-list__footer-wrapper .job-card-container__footer-wrapper li time::text").get(default="not-found").strip()   
            yield job_item
        if number_of_jobs_returned >0:
            first_job_on_page = int(first_job_on_page)+25
            next_url = self.api_url + str(first_job_on_page)
            yield scrapy.Request(url=next_url, callback=self.parse_job, meta={"first_job_on_page": first_job_on_page})