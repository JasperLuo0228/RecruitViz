import asyncio
import csv
import json
import random
import os
from playwright.async_api import async_playwright

FIELDS = ["关键词", "职位", "职位描述", "公司信息"]

class BossSpiderScroll:
    def __init__(self):
        self.cookie_file = "boss_cookies.json"
        self.output_file = "BOSS直聘_后半数据.csv"
        self.max_retries = 3
        self.keyword_delay = (6, 12)
        self.batch_pause = 80
        self.max_scroll = 10  # 最多滑动几次（每次可加载一屏）

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

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100,113)}.0.0.0 Safari/537.36"
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

            keywords = ["托育", "家政", "养老"]  # 示例

            file_exists = os.path.exists(self.output_file)
            f = open(self.output_file, "a", newline="", encoding="utf-8-sig")
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(FIELDS)

            all_count = 0
            for keyword in keywords:
                print(f"\n🔍 采集关键词: {keyword}")
                page = await context.new_page()
                await page.goto(f"https://www.zhipin.com/web/geek/jobs?query={keyword}")
                await page.wait_for_timeout(2500)

                last_count = 0
                for i in range(self.max_scroll):
                    await page.mouse.wheel(0, 12000)  # 向下滚动到底
                    await page.wait_for_timeout(1600)
                    cards = await page.query_selector_all("li.job-card-box, li.job-card-wrapper")
                    print(f"滑动{i+1}次后，共{len(cards)}个岗位")
                    if len(cards) == last_count:
                        print(f"🟢 已经滑到底，共{len(cards)}个岗位，提前结束下拉")
                        break
                    last_count = len(cards)

                # 统一采集所有卡片
                cards = await page.query_selector_all("li.job-card-box, li.job-card-wrapper")
                print(f"共需采集{len(cards)}个岗位")

                for idx, card in enumerate(cards):
                    try:
                        await card.click()
                        await page.wait_for_selector("div.job-detail-box, div.job-detail-body", timeout=6000)
                        await page.wait_for_timeout(500)
                    except Exception as e:
                        print(f"⚠️ 第{idx+1}个岗位点击失败：{e}")
                        continue

                    # 职位名
                    try:
                        job_name = await page.locator("span.job-name").first.inner_text()
                    except:
                        job_name = ""
                    # 职位描述
                    try:
                        job_desc = await page.locator("div.job-sec-text, div.desc, p.desc").first.inner_text()
                    except:
                        job_desc = ""
                    # 公司信息
                    try:
                        boss_info = await page.locator("div.boss-info-attr").first.inner_text()
                    except:
                        boss_info = ""

                    writer.writerow([
                        keyword, job_name, job_desc, boss_info
                    ])
                    f.flush()
                    all_count += 1
                    print(f"✅ {keyword} | 卡片{idx+1}/{len(cards)} | 总{all_count}")

                    if all_count % self.batch_pause == 0:
                        print(f"⏳ 达到{self.batch_pause}条，自动休息8秒")
                        await asyncio.sleep(8)
                await page.close()
                await asyncio.sleep(random.uniform(*self.keyword_delay))
            f.close()
            await browser.close()
            print("\n🎉 采集完成！数据已实时保存")

if __name__ == "__main__":
    spider = BossSpiderScroll()
    asyncio.run(spider.run())
