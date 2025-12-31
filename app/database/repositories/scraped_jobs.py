# app/services/scraper/agent.py
from apscheduler.schedulers.background import BackgroundScheduler
from app.database.models import Job
from app.utils import dbSession
import logging
from sqlalchemy.exc import IntegrityError
# app/scraper/agent.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.agents.jobscraper import ProxyEnhancedJobScraper


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scraper = ProxyEnhancedJobScraper()

def scrape_job_cycle():
    logger.info("🔄 Starting scraping cycle...")
    db = dbSession()
    try:
        websites = scraper.get_comprehensive_job_websites()
        successful, failed = scraper.process_sites_with_proxy(websites=websites, max_workers=5)
        
        # Process scraped jobs and save to DB
        for config in successful:
            for job in config.get("jobs", []):
                try:
                    # Example: insert job into your Job table
                    if not db.query(Job).filter_by(url=job['url']).first():
                        db.add(Job(
                            title=job.get("title") or "N/A",
                            company=job.get("company") or "N/A",
                            location=job.get("location"),
                            description=job.get("description"),
                            url=job.get("url"),
                            external_id=job.get("external_id"),
                            board=job.get("board"),
                            posted_at=job.get("posted_at"),
                            raw_payload=job
                        ))
                        db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"❌ Failed to save job {job.get('url')}: {e}")
        
        logger.info(f"✅ Scraping cycle completed: {len(successful)} sites, {len(failed)} failed")
    except Exception as e:
        logger.exception(f"❌ Scraping cycle failed: {e}")
    finally:
        db.close()

def start_scraper_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_job_cycle, "interval", minutes=10, max_instances=1)
    scheduler.start()
    logger.info("🚀 Scraper scheduler started (every 10 mins)")