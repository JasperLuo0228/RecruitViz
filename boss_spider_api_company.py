import asyncio
import csv
import json
import random
import os
from playwright.async_api import async_playwright

FIELDS = ["关键词", "职位", "薪资", "城市", "公司", "经验", "学历", "公司规模", "在招职位数"]

class BossSpiderFastCompany:
    def __init__(self):
        self.cookie_file = "boss_cookies.json"
        self.output_file = "BOSS直聘_前半数据.csv"
        self.max_retries = 3
        self.request_delay = (1, 3)       # 页间隔加快
        self.company_delay = (8, 18)         # 公司页采集后加快
        self.keyword_delay = (10, 20)        # 关键词间隔
        self.batch_pause = 45              # 每100条暂停
        self.batch_sleep = 30              # 休息时间

    async def save_cookies(self, context):
        cookies = await context.cookies()
        with open(self.cookie_file, "w") as f:
            json.dump(cookies, f)

    async def load_cookies(self, context):
        try:
            with open(self.cookie_file, "r") as f:
                await context.add_cookies(json.load(f))
            return True
        except:
            return False

    async def ensure_login(self, context):
        for attempt in range(self.max_retries):
            test_url = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json?query=测试&page=1"
            response = await context.request.get(test_url)
            if response.status == 200:
                try:
                    data = await response.json()
                    if data.get('zpData', {}).get('jobList') is not None:
                        return True
                except:
                    pass
            print(f"🔄 会话失效，扫码登录BOSS直聘（第{attempt+1}次）")
            page = await context.new_page()
            await page.goto("https://www.zhipin.com/web/geek/job?query=测试")
            await page.wait_for_timeout(60000)
            await self.save_cookies(context)
            await page.close()
        return False

    async def get_company_info(self, context, company):
        company_size, hiring_count = "", ""
        if not company:
            return company_size, hiring_count
        page = await context.new_page()
        try:
            await page.goto(f"https://www.zhipin.com/web/geek/job?query={company}", timeout=20000)
            await page.wait_for_timeout(1000)
            tags = await page.locator('span.company-info-tag').all_text_contents()
            company_size = next((tag for tag in tags if "人" in tag), "")
            try:
                hiring_count = await page.locator('span.count-text').first.text_content()
            except:
                hiring_count = ""
        except Exception as e:
            print(f"⚠️ 公司主页采集异常: {e}")
            await asyncio.sleep(30)
        await page.close()
        await asyncio.sleep(random.uniform(*self.company_delay))
        return company_size, hiring_count

    async def fetch_job_page(self, context, keyword, page_num):
        url = f"https://www.zhipin.com/wapi/zpgeek/search/joblist.json?query={keyword}&city=101010100&page={page_num}"
        for attempt in range(self.max_retries):
            try:
                response = await context.request.get(url)
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                data = await response.json()
                if not data.get('zpData', {}).get('jobList'):
                    raise Exception("无效的接口响应")
                return data['zpData']['jobList']
            except Exception as e:
                print(f"⚠️ {keyword} 第{page_num}页第{attempt+1}次失败: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                await asyncio.sleep(30)
                await self.ensure_login(context)

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=T,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90,110)}.0.0.0 Safari/537.36"
                ]
            )
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="zh-CN"
            )

            if not await self.load_cookies(context) or not await self.ensure_login(context):
                print("❌ 登录失败，请手动扫码")
                await browser.close()
                return

            existing = set()
            if os.path.exists(self.output_file):
                with open(self.output_file, newline="", encoding="utf-8-sig") as ff:
                    reader = csv.DictReader(ff)
                    for row in reader:
                        existing.add((row['关键词'], row['职位'], row['公司']))

            keywords = ["托育", "家政", "养老", "康复", "育婴", "母婴", "护理员", "护理专业", "养老护理", "殡葬", "临终关怀", "婚宴策划", "家宴管家", "宴会主持",
                        "智慧养老", "智能养老", "智能护理", "健康管理", "健康照护", "养老顾问", "社区养老", "居家养老", "养老运营", "养老院院长",
                        "老年人服务", "老年健康", "康养", "医疗护理", "护理学", "医养结合", "临床护理", "专科护士", "护士长", "医疗服务",
                        "管家", "家政经理", "保姆", "月嫂", "育儿嫂", "家政督导", "家政项目经理", "居家照护", "生活助理",
                        "托班老师", "托育老师", "早教老师", "亲子园", "幼教", "幼托", "早教中心", "儿童照护", "幼儿园保育员", "婴幼儿发展", "婴幼儿早教",
                        "照护", "照护师", "健康照护师", "护理助理", "老人陪护", "护工", "院长助理", "社区照护", "养老培训", "失能老人照护",
                        "康复治疗师", "康复师", "养生顾问", "中医护理", "老年产业"]
            file_exists = os.path.exists(self.output_file)
            f = open(self.output_file, "a", newline="", encoding="utf-8-sig")
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(FIELDS)

            all_count = 0
            for keyword in keywords:
                print(f"\n🔍 采集关键词: {keyword}")
                page_num = 1
                total = 0
                while page_num <= 30:
                    jobs = await self.fetch_job_page(context, keyword, page_num)
                    if not jobs:
                        print(f"⏹️ {keyword} 采集终止于第{page_num}页")
                        break
                    for job in jobs:
                        job_name = job.get("jobName", "")
                        salary = job.get("salaryDesc", "")
                        city = job.get("cityName", "")
                        company = job.get("brandName", "")
                        experience = job.get("jobExperience", "")
                        degree = job.get("jobDegree", "")

                        company_size, hiring_count = await self.get_company_info(context, company)

                        key = (keyword, job_name, company)
                        if key not in existing:
                            writer.writerow([
                                keyword, job_name, salary, city, company,
                                experience, degree, company_size, hiring_count
                            ])
                            f.flush()
                            existing.add(key)
                            total += 1
                            all_count += 1
                            print(f"✅ {keyword} 第{page_num}页 | 本页{len(jobs)} | 累计{total} | 总{all_count}")

                            if all_count % self.batch_pause == 0:
                                print(f"⏳ 达到{self.batch_pause}条，自动休息{self.batch_sleep}秒")
                                await asyncio.sleep(self.batch_sleep)

                        if all_count % self.batch_pause == 0:
                            print(f"⏳ 达到{self.batch_pause}条，自动休息{self.batch_sleep}秒")
                            await asyncio.sleep(self.batch_sleep)

                    page_num += 1
                    await asyncio.sleep(random.uniform(*self.request_delay))

                await asyncio.sleep(random.uniform(*self.keyword_delay))
            f.close()
            await browser.close()
            print("\n🎉 采集完成！数据已实时保存")

if __name__ == "__main__":
    spider = BossSpiderFastCompany()
    asyncio.run(spider.run())
