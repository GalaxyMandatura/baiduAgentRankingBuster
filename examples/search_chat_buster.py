import asyncio
from pathlib import Path

from baidu_buster.main import BaiduAgentChatBusterForChat, BaiduAgentSearchBuster
from conf import BASE_DIR

if __name__ == '__main__':
    app = BaiduAgentSearchBuster()
    asyncio.run(app.main(), debug=True)
