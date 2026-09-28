import asyncio
import os
import glob
from playwright.async_api import async_playwright

async def record_demo():
    os.makedirs("scratch/raw_video", exist_ok=True)
    for f in glob.glob("scratch/raw_video/*.webm"):
        try: os.remove(f)
        except Exception: pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir="scratch/raw_video/",
            record_video_size={"width": 1280, "height": 720}
        )

        page = await context.new_page()

        print("Navigating to frontend...")
        await page.goto("http://localhost:8080")
        await page.wait_for_timeout(2500)

        input_box = page.locator("#input")

        # 1. Click prompt chip: 30-min workout
        print("Clicking prompt chip 1...")
        chip1 = page.locator(".prompt-chip").first
        await chip1.click()

        print("Waiting for response 1...")
        await page.wait_for_timeout(8000)

        # 2. Richer Prompt: Visual Generation Tool Call
        print("Submitting richer prompt 2...")
        rich_prompt = "Generate a visual demonstration card for a high protein post-workout breakfast smoothie bowl."

        await input_box.fill("")
        for char in rich_prompt:
            await input_box.type(char, delay=35)
            
        await page.wait_for_timeout(500)
        await page.click("#form button")

        print("Waiting for tool execution & visual card rendering...")
        await page.wait_for_timeout(15000)

        # Final pause to showcase the rebranded dialogue layout & visual card
        await page.wait_for_timeout(4000)

        print("Closing context and saving video...")
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(record_demo())
