import asyncio
import os
import time
import typing
from pathlib import Path

import requests
from playwright.async_api import Page, FrameLocator

from conf import BASE_DIR

proxy_key = os.environ["PROXY_KEY"]


def get_proxy_server() -> str:
    response = requests.get(f"https://share.proxy.qg.net/get?key={proxy_key}")
    response.raise_for_status()
    # 解析 JSON 响应
    data = response.json()
    # 检查返回的内容是否包含数据
    if data['code'] == 'SUCCESS' and 'data' in data and len(data['data']) > 0:
        # 获取第一个数据项中的 server 字段
        return data['data'][0]['server']
    else:
        raise ValueError("Invalid response or no data available")


async def set_init_script(context):
    stealth_js_path = Path(BASE_DIR / "utils/stealth.min.js")
    await context.add_init_script(path=stealth_js_path)
    return context


async def wait_talking(locator: Page | FrameLocator, locator_str: str) -> None:
    s = 0
    max_waiting_times = 60
    while await locator.locator(locator_str).is_visible():
        s += 1
        if s > max_waiting_times:
            await locator.locator(locator_str).click()
            break
        await asyncio.sleep(1)


async def do_wait_talking(page: Page, locator: Page | FrameLocator,
                          url: typing.Union[str, typing.Pattern[str], typing.Callable[[str], bool]], locator_str: str,
                          count) -> tuple[int, float]:
    start_time = time.perf_counter()  # 记录开始时间
    try:
        await wait_talking(locator, locator_str)
        return count + 1, time.perf_counter() - start_time
    except asyncio.TimeoutError:
        await page.reload()
        await page.wait_for_url(url)
        return count, time.perf_counter() - start_time
