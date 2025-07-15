# Boss Zhipin Job Data Crawler

## Project Overview

This project aims to use Python and Playwright to automatically collect job and company data from [Boss Zhipin](https://www.zhipin.com/), one of China’s largest online job platforms, and support further data analysis and visualization for HR research, job market trends, and industry insights.

The scripts use two different approaches — **API-based collection** and **page-scrolling simulation** — to maximize data coverage, reduce risk of being blocked, and meet various data needs.

---

## Scripts Overview

### 1. boss_spider_api_company.py

- **Collection Method:**  
  Directly calls Boss Zhipin’s official APIs to fetch job listings and key company fields such as company size and number of open positions (scraped from the company page).

#### **Logic Summary**
1. For each keyword, fetch all pages of job listings through the API.
2. For each job, open a new tab and scrape company profile data (e.g., size, hiring count).
3. Write all fields to CSV row by row (supports resumable collection).
4. Includes robust timing and retry logic to minimize risk of account bans.

---

### 2. boss_spider_scroll_detail.py

- **Collection Method:**  
  Automates browser to simulate scrolling down, triggering lazy-loading of more jobs, then clicks on each card to fetch details (e.g., job description, company info) from the right panel.

#### **Logic Summary**
1. For each keyword, open the search result page and scroll down repeatedly to trigger loading of more job cards, up to a maximum scroll count.
2. For each loaded card, click to open job details and wait for the detail panel.
3. Scrape **Job Title**, **Job Description**, and **Company Info** from the right-hand panel and write them into CSV.
4. Like the API script, supports robust error handling, interval throttling, and resumable runs.

---

## Progress So Far

- Initial automated crawler scripts (Playwright + asyncio) are completed, supporting automatic cookie saving, breakpoint resume (continue from where stopped), and anti-anti-crawling measures.

- Supports batch keyword scraping, company information completion, and deduplication before writing to CSV.

- Integrated with ServerChan (Server酱) push service to notify for scan code login (enabling remote scan and login). (Working in Progress...)

## Project Goals

- Fully automated scraping of key job postings from BOSS Zhipin (covering multiple keywords, industries, and cities).

- Data cleaning and structured storage for easy subsequent analysis.

- Visualization and trend analysis (such as job distribution, salary trends, company size, etc.).

## Repository Structure

```
.
├── README.md                  # Project overview (this file)
├── Graph                      # Project Images Storing
├── BOSS直聘_合并结果.csv       # Data (Beijing)
├── Result.html                # Project Dashboard
├── boss_spider_api_company.py
├── boss_spider_scroll_detail.py
└── boss_cookies.json