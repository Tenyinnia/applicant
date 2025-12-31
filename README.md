# AI-Powered Job Application Assistant

An end-to-end **AI-driven job application platform** that parses user CVs, scrapes job listings from multiple sources, intelligently matches candidates to roles, and assists with generating tailored applications.

This system is designed with a **modular agent-based architecture** to simulate real-world hiring workflows and automate repetitive job search tasks.



## 🚀 Key Features

 -  Upload CVs and job preferences via web or mobile frontend
 -  Automated CV parsing and skill extraction
 -  Continuous job scraping from public job boards and company career pages
 -  AI-powered CV ↔ Job matching and ranking
 -  Assisted job application workflow with user confirmation
 -  Scalable FastAPI backend with clean service separation


## 🧠 System Architecture
```
Frontend (Web / Mobile)
│
│──Upload CV, Cover letter, preferences(supporting documents)
│──Job Lists and other automated actions
▼
FastAPI Backend
│
├── CV Parser Agent
│   ├── Skill extraction
│   ├── Experience analysis
│   └── Keyword normalization
│
├── Job Scraper Agent
│   ├── Public job boards scraping
│   ├── API-based job sources
│   └── Company career pages
│
├── Matching Agent (AI)
│   ├── CV ↔ Job similarity scoring
│   ├── Tech stack relevance scoring
│   └── Job ranking & prioritization
│
├── Apply Assistant
│   ├── Redirect application links
│   ├── Autofill suggestions
│   └── User confirmation / browser extension support
│
└── Database
    ├── Users
    ├── CVs
    ├── Jobs
    └── Applications

```

## 🛠 **Tech Stack**
# Backend

  -  Python 3.11.0+

  -  FastAPI

  -  SQLAlchemy

  -  PostgreSQL

  -  Background task scheduling

  -  AI / NLP

  -  spaCy / NLP pipelines

  -  Embedding-based similarity matching

  -  Keyword normalization & scoring

  -  LLM-powered document generation

  -  Scraping & Automation

  -  Requests / Playwright / Selenium

  -  Heuristic-based selector detection

  -  Rate limiting & retry mechanisms

# Frontend (Pluggable)

  -  Web (HTML, CSS, JavaScript) (Focus)

  -  Mobile-ready API design

  -  Browser extension support (planned)

### 🧩 **Core Agents**
# 🔍 CV Parser Agent

  -  Extracts skills, tools, experience, and keywords from uploaded CVs

  -  Normalizes data into structured profiles

  -  Supports PDF and DOCX formats

# 🌐 Job Scraper Agent

  -  Scrapes job listings from multiple public sources

  -  Supports both API-based and HTML-based job boards

  -  Handles pagination, deduplication, and freshness tracking

# 🧠 Matching Agent (AI)

  -  Computes similarity between candidate profiles and job descriptions

  -  Scores technical stack alignment

  -  Ranks jobs based on relevance and preference weighting

# 🧭 Apply Assistant

  -  Assists users during the application process

  -  Suggests autofill data

  -  Supports redirect-based and semi-automated workflows

  -  Keeps user in control (confirmation required)

# 🗄 Database Schema (High-Level)

  -  Users – authentication & preferences

  -  CVs – parsed and versioned CV data

  -  Jobs – scraped and indexed job listings

  -  Applications – tracking submitted and pending applications

## 🔐 Security & Best Practices

  -  JWT-based authentication

  -  Secure file handling for uploads

  -  Rate-limited scraping

  -  Modular service architecture

  -  Clean separation of concerns


# 📦 Installation (Backend)
  1. git clone https://github.com/Tenyinnia/applicant.git

  2.  cd applicant

  3.  python -m venv .venv

  4.  source .venv/bin/activate (MAC)

      .venv/Scripts/Activate (WINDOWS)

  5.  pip install -r requirements.txt

  6.  uvicorn app.main:app --reload

# 🧪 Future Enhancements

  -  Browser extension for intelligent autofill

  -  Application status tracking dashboard

  -  Feedback loop for improving match accuracy

  -  Multi-language CV support

  -  Cloud deployment (Docker + CI/CD)

# 👨‍💻 Author
    ```
    Enyinnia Clifford  Tochi
    FUllstack & AI System Developer
    Specialized in Python, FastAPI, Django, Frontend, Automation & AI-driven platforms
    ```