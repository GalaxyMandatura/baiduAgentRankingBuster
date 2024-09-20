import asyncio
import json
import os
import re
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from baidu_buster import AUTH_VALID
from baidu_buster.main import BaiduAgentChatBusterForMDB, baidu_account_auth_detect, baidu_account_auth
from conf import BASE_DIR

load_dotenv()

COOKIES_DIR = str(Path(BASE_DIR / "cookies" / "baidu"))
authorized_status_file = str(Path(BASE_DIR / "cookies" / "baidu" / "authorized_status.json"))


def save_authorized_status(authorized_status):
    with open(authorized_status_file, "w") as f:
        json.dump(authorized_status, f)


def load_authorized_status():
    if not os.path.exists(authorized_status_file):
        return {}
    with open(authorized_status_file, "r") as f:
        return json.load(f)


def load_authorized_files():
    """Load a list of authorized accounts from files in the cookies directory."""
    return [
        filename.split("_")[1].split(".")[0]
        for filename in os.listdir(COOKIES_DIR)
        if filename.startswith("account_") and filename.endswith(".json")
    ]


def load_authorized_accounts_with_authorized_status(authorized_status: dict[str, str] = None) -> dict[str, str]:
    accounts = load_authorized_files()
    if not authorized_status:
        authorized_status = load_authorized_status()
    return {
        account: (
            "有效" if authorized_status and account in authorized_status and authorized_status[account] == AUTH_VALID
            else "无效" if authorized_status and account in authorized_status
            else "未知"
        )
        for account in accounts
    }


def get_authorized_accounts_options(authorized_status: dict[str, str] = None) -> list[str]:
    authorized_accounts = load_authorized_accounts_with_authorized_status(authorized_status)
    return [f"{account}（{status}）" for account, status in authorized_accounts.items()]


def do_brush_rank(agent_url: str, accounts: list[str], silent: bool):
    try:
        app = BaiduAgentChatBusterForMDB(accounts)
        asyncio.run(app.main(agent_url, silent), debug=True)
    except Exception as e:
        return f"出错啦:\n{e}"
    return "任务执行完毕!"


def do_account_auth_rank(account: str):
    try:
        asyncio.run(baidu_account_auth(account))
    except Exception as e:
        return f"出错啦:\n{e}"
    return "任务执行完毕!"


def on_authorization_click(account: str):
    yield gr.update(interactive=False), "任务正在执行..."
    result = do_account_auth_rank(account)
    yield gr.update(interactive=True), result


def on_brush_rank_click(agent_url, accounts, silent=False):
    if not accounts:
        yield gr.update(interactive=True), "请选择已经授权的账号"
        return
    if not agent_url:
        yield gr.update(interactive=True), "智能体地址不能为空"
        return
    accounts = [re.search(r'\d{11}', account).group() for account in accounts]
    yield gr.update(interactive=False), "任务正在执行..."
    result = do_brush_rank(agent_url, accounts, silent)
    yield gr.update(interactive=True), result


def check_account_authorization():
    accounts = load_authorized_files()
    authorized_status = {}
    for account in accounts:
        try:
            r = asyncio.run(baidu_account_auth_detect(account))
            authorized_status[account] = r
        except:
            pass
    return authorized_status


def on_check_authorization_click():
    yield gr.update(interactive=False), "检查中，请稍候..."
    authorized_status = check_account_authorization()
    save_authorized_status(authorized_status)
    yield gr.update(interactive=True), "检查完毕，请刷新页面"
    # return "检查完毕，请刷新页面"
    # return gr.Dropdown(choices=new_options, interactive=True)


def select_all_accounts():
    authorized_accounts = load_authorized_accounts_with_authorized_status()
    all_accounts = [f"{account}（{status}）" for account, status in authorized_accounts.items()]
    return gr.update(value=all_accounts)


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 百度账号授权")
            account_textbox = gr.Textbox(label="百度账号(手机号)",
                                         placeholder="请输入正难题百度账号，如：186****7044")
            with gr.Row():
                authorization_button = gr.Button("增加百度账号授权", scale=10)
                check_authorization_button = gr.Button("检测授权状态", scale=5)  # Add a smaller button
                loading_label = gr.Label("检测中...", visible=False)

            output_text = gr.Textbox(label="授权输出")
            authorization_button.click(fn=on_authorization_click, inputs=account_textbox,
                                       outputs=[authorization_button, output_text])
            check_authorization_button.click(fn=on_check_authorization_click, outputs=[output_text])

        with gr.Column():
            gr.Markdown("### 智能体开刷功能")
            account_list = gr.Dropdown(choices=get_authorized_accounts_options(),
                                       label="已授权百度账号列表（授权状态）",
                                       multiselect=True)

            agent_url_textbox = gr.Textbox(label="智能体地址",
                                           placeholder="请输入正难题的地址，如：https://mbd.baidu.com/ma/s/cAXZgRZK")
            silent_model = gr.Checkbox(label="静默模式", value=False)
            brush_rank_click_button = gr.Button("开刷！！！开刷(*^▽^*)")
            brush_rank_output_text = gr.Textbox(label="开刷输出")
            brush_rank_click_button.click(fn=on_brush_rank_click,
                                          inputs=[agent_url_textbox, account_list, silent_model],
                                          outputs=[brush_rank_click_button, brush_rank_output_text])

demo.launch(share=False)
