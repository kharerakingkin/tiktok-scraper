import asyncio
import random
import os
import urllib.parse
from patchright.async_api import async_playwright
import yt_dlp

# =========================
# CONFIG
# =========================
KEYWORDS = ["cewe cantik"]
MAX_VIDEO_PER_KEYWORD = 10
MAX_RETRY = 3
BASE_SAVE_DIR = "videos"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120 Safari/537.36"
)


# =========================
# HELPERS
# =========================
async def random_delay(a=2, b=5):
    await asyncio.sleep(random.uniform(a, b))


def download_with_ytdlp(video_url: str, save_dir: str):
    ydl_opts = {
        "outtmpl": os.path.join(save_dir, "%(id)s.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])


# =========================
# VIDEO PROCESSOR
# =========================
async def process_video(video_url, save_dir):
    for attempt in range(1, MAX_RETRY + 1):
        try:
            print(f"[YT-DLP] Try {attempt} → {video_url}")
            download_with_ytdlp(video_url, save_dir)
            print("[SAVED]")
            return True
        except Exception as e:
            print(f"[RETRY] yt-dlp error: {e}")
            await asyncio.sleep(3)

    print("[SKIP] Gagal / slideshow")
    return False


# =========================
# MAIN
# =========================
async def main():
    os.makedirs(BASE_SAVE_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, args=["--disable-blink-features=AutomationControlled"]
        )

        for keyword in KEYWORDS:
            print(f"\n===== KEYWORD: {keyword} =====")

            keyword_slug = keyword.replace(" ", "_").lower()
            save_dir = os.path.join(BASE_SAVE_DIR, keyword_slug)
            os.makedirs(save_dir, exist_ok=True)

            context = await browser.new_context(
                viewport={"width": 1280, "height": 800}, user_agent=USER_AGENT
            )

            page = await context.new_page()

            search_url = "https://www.tiktok.com/search?q=" + urllib.parse.quote(
                keyword
            )

            await page.goto(search_url, wait_until="domcontentloaded")
            await random_delay(4, 6)

            # Scroll
            for _ in range(4):
                await page.mouse.wheel(0, 3000)
                await random_delay(2, 3)

            video_links = page.locator('a[href*="/video/"]')
            total = await video_links.count()

            urls = []
            for i in range(min(total, MAX_VIDEO_PER_KEYWORD)):
                href = await video_links.nth(i).get_attribute("href")
                if href and href not in urls:
                    urls.append(href)

            print(f"[INFO] Video ditemukan: {len(urls)}")

            for video_url in urls:
                await process_video(video_url, save_dir)
                await random_delay(4, 7)

            await context.close()
            await random_delay(8, 12)

        await browser.close()
        print("\n[DONE] Semua keyword selesai")


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    asyncio.run(main())
