import asyncio

from baidu_buster.main import BaiduAgentChatBusterForChat, BaiduAgentChatBusterForMDB

if __name__ == '__main__':
    # account_file = Path(BASE_DIR / "cookies" / "baidu" / "account_18610807044.json")
    accounts = ['18610807044', '13271557189', '13523079221', '13526609822', '16638075731']
    # agent_url="https://chat.baidu.com/bot?appId=bWDjeHduXlKlYi6WTXvBSevLNObFURht"
    # agent_url = "https://chat.baidu.com/bot?appId=k8wXTLAmi9CXc21RL34L8VEGoKYO904A"
    agent_url = "https://mbd.baidu.com/ma/s/cAXZgRZK"
    try:
        app = BaiduAgentChatBusterForMDB(accounts)
        asyncio.run(app.main(agent_url, True), debug=True)
    except Exception as e:
        print(e)
