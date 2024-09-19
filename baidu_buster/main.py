import asyncio
import os
import random
import re
from pathlib import Path
from typing import List

from playwright.async_api import Playwright, async_playwright, Page, Locator, FrameLocator, BrowserContext

from baidu_buster import AUTH_VALID, AUTH_INVALID
from bot import AgentBusterBot
from conf import BASE_DIR
from utils import get_proxy_server, set_init_script, do_wait_talking

system_message = """
你是一个对话助理，请在对话时简明扼要。
"""


def generate_question(message: str) -> str:
    if not message:
        return "你好呀"
    try:
        bot = AgentBusterBot(system_message)
        return bot.chat(message)
    except Exception as e:
        print(f"生成对话出现异常:{e}")
        return "你好呀"


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        await page.goto("https://agents.baidu.com/agent/list/codeless")  # 我的智能体页
        try:
            await page.wait_for_url("https://agents.baidu.com/agent/list/codeless", timeout=5000)
        except:
            await context.close()
            await browser.close()
            return False
        if await page.get_by_text('扫码登录').count():
            return False
        return True


async def baidu_cookie_gen(mobile_number):
    account_file = str(Path(BASE_DIR / "cookies" / "baidu" / f"account_{mobile_number}.json"))
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=False)
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://agents.baidu.com/center")
        await page.get_by_role("button", name="登录", exact=True).click()
        await page.get_by_text("短信登录").click()
        await page.get_by_placeholder("手机号", exact=True).type(mobile_number)
        await page.get_by_role("button", name="发送验证码").click()
        await page.wait_for_url("https://agents.baidu.com/center")
        await page.pause()
        await context.storage_state(path=account_file)
        await context.close()
        await browser.close()


async def baidu_account_auth_detect(account) -> str:
    account_file = str(Path(BASE_DIR / "cookies" / "baidu" / f"account_{account}.json"))
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        return AUTH_INVALID
    return AUTH_VALID


async def baidu_account_auth(account):
    await baidu_cookie_gen(account)


async def baidu_setup(mobile_number, handle=False) -> bool:
    account_file = str(Path(BASE_DIR / "cookies" / "baidu" / f"account_{mobile_number}.json"))
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        print(f"账号为:{mobile_number}的登录凭证无效，正在尝试重新授权...")
        if not handle:
            return False
        await baidu_cookie_gen(mobile_number)
    print(f"账号为:{mobile_number}的登录凭证有效.")
    return True


async def random_suggestion_item(locator: Page | FrameLocator, locator_str: str) -> Locator | None:
    elements = await locator.locator(locator_str).all()
    if elements:
        return random.choice(elements[1:] if len(elements) > 3 else elements)
    return None


# recommend-item

class BaiduAgentChatBusterForChat(object):
    def __init__(self, mobile_number):
        self.account_file = str(Path(BASE_DIR / "cookies" / "baidu" / f"account_{mobile_number}.json"))

    async def do_chat_buster(self, playwright: Playwright, agent_url: str) -> None:
        browser = await playwright.firefox.launch(headless=False)
        _context = await browser.new_context(storage_state=self.account_file)
        _context = await set_init_script(_context)
        page = await _context.new_page()

        await page.goto(agent_url)
        await page.wait_for_url(agent_url)

        max_chat_num = random.randint(2, 5)
        dialog_count = 1
        default_text = "你好呀!"
        first_chat = True
        print(f"本次预计沟通 {max_chat_num} 轮")
        while dialog_count <= max_chat_num:
            await asyncio.sleep(2)
            suggestion_item = await random_suggestion_item(page, "div[class='suggestion-item-container']")
            if first_chat:
                random_element = await random_suggestion_item(page, "div[class='demo']")
                if random_element:
                    await random_element.click()
                else:
                    await page.get_by_placeholder("请在此输入").type(default_text)
                    await page.keyboard.press("Enter")
                first_chat = False
            elif suggestion_item:
                await suggestion_item.click()
            else:
                await page.get_by_placeholder("请在此输入").type(default_text)
                await page.keyboard.press("Enter")

            await asyncio.sleep(1)
            print(f"沟通进度:{round((dialog_count / max_chat_num) * 100, 2)}%")
            dialog_count, _ = await do_wait_talking(page, page, agent_url, "div[class='control-stop']", dialog_count)

        print(f"沟通结束({dialog_count}/{max_chat_num})，释放资源.")
        await _context.close()
        await browser.close()

    async def main(self, agent_url: str):
        async with async_playwright() as playwright:
            await self.do_chat_buster(playwright, agent_url)


async def do_chat_buster(context: BrowserContext, account: str, agent_url: str) -> None:
    page = await context.new_page()
    await page.goto(agent_url)
    await page.wait_for_url(re.compile(r"smartapps\.baidu\.com.*"), timeout=30000)

    max_chat_num = random.randint(2, 5)
    dialog_count = 1
    first_chat = True
    frame: FrameLocator = page.frame_locator('iframe[name="webswan-slave"]')
    agent_name = await frame.locator('span.pc-bar-title-text').inner_text()
    print(f"账号:{account} 智能体:{agent_name} 本次预计沟通 {max_chat_num} 轮")
    while dialog_count <= max_chat_num:
        await asyncio.sleep(2)
        suggestion_item = await random_suggestion_item(frame, "div.suggestion-item-container")
        if first_chat:
            random_element = await random_suggestion_item(frame, ".recommend-item")
            if random_element:
                await random_element.click()
                log = f'Step {max_chat_num}/{dialog_count}: 点击引导语执行提问执行成功'
            else:
                welcome_text = await frame.locator('div.description p').inner_text()
                content = generate_question(welcome_text)
                await frame.get_by_placeholder("可以问我任何问题…").type(content)
                await page.keyboard.press("Enter")
                log = f'Step {max_chat_num}/{dialog_count}: 自由输入提问执行成功'
            first_chat = False
        elif suggestion_item:
            await suggestion_item.click()
            log = f'Step {max_chat_num}/{dialog_count}: 点击引导提示语执行提问执行成功'
        else:
            await frame.get_by_placeholder("可以问我任何问题…").type("请详细展开讲一下")
            await page.keyboard.press("Enter")
            log = f'Step {max_chat_num}/{dialog_count}: 自由输入提问执行成功'
        await asyncio.sleep(1)
        dialog_count, elapsed_time = await do_wait_talking(page, frame, re.compile(r"smartapps\.baidu\.com.*"),
                                                           "div[class='control-stop']", dialog_count)
        print(
            f"{account}|{agent_name} "
            f"{log}, "
            f"单步耗时:{round(elapsed_time, 2)}，")

    print(f"账号{account} 沟通结束({dialog_count - 1}/{max_chat_num})，释放资源.")
    await page.close()


async def do_chat_buster_with_try(browser, account, agent_url):
    auth_file = str(Path(BASE_DIR / "cookies" / "baidu" / f"account_{account}.json"))
    context = await browser.new_context(storage_state=auth_file)
    context = await set_init_script(context)
    try:
        await do_chat_buster(context, account, agent_url)
    finally:
        await context.close()


class BaiduAgentChatBusterForMDB(object):
    def __init__(self, accounts: List[str]):
        self.accounts = accounts

    async def chat_buster(self, playwright: Playwright, agent_url: str, silent: bool) -> None:
        browser = await playwright.firefox.launch(headless=silent, args=['--no-sandbox', '--disable-dev-shm-usage'])
        tasks = [do_chat_buster_with_try(browser, account, agent_url) for account in self.accounts]
        await asyncio.gather(*tasks)
        await browser.close()

    async def main(self, agent_url: str, silent: bool):
        async with async_playwright() as playwright:
            await self.chat_buster(playwright, agent_url, silent)


async def type_text_slowly(page, selector, text, delay=100):
    textarea = page.locator(selector)
    await textarea.click()  # 点击以激活输入框
    await page.keyboard.type(text, delay=delay)  # 使用 type 方法逐字输入


async def click_random_element(parent_container: Locator, selector: str) -> None:
    elements = await parent_container.locator(selector).all()
    if elements:
        await random.choice(elements).click()
    else:
        print("No elements found with the specified conditions.")


class BaiduAgentSearchBuster(object):
    def __init__(self):
        self.url = "https://www.baidu.com/"
        pass

    async def main(self):
        async with async_playwright() as playwright:
            count = 0
            while count < 80:
                try:
                    server = get_proxy_server()
                    proxy = {
                        "server": server,
                        "username": "681C3003",
                        "password": "C4613783C915"
                    }
                    await self.do_search_buster(playwright, proxy)
                except Exception as e:
                    print(e)
                    pass
                count += 1

    async def do_search_buster(self, playwright, proxy):
        browser = await playwright.chromium.launch(headless=True)
        _context = await browser.new_context(proxy=proxy)  # 使用代理
        page = await _context.new_page()
        await page.goto(self.url)
        await page.wait_for_url(self.url)

        # 等待搜索框出现并输入文字
        await page.wait_for_selector("input[id='kw']")
        await type_text_slowly(page, "input[id='kw']", "大模型定制")

        # 点击搜索按钮
        await page.locator("input[id='su']").click()
        await asyncio.sleep(10)
        agent_container = page.locator("div[tpl='ins_application_card']")
        await click_random_element(agent_container, 'div[data-module="cardentry"]')
        print('Done!')
        await asyncio.sleep(20)
        await browser.close()
