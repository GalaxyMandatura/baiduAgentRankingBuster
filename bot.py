import qianfan
from qianfan import QfResponse, QfRole
from qianfan.resources.typing import JsonBody, QfMessages
from dotenv import load_dotenv

load_dotenv()


class AgentBusterBot:
    def __init__(self, system_msg=None):
        self.system_message = system_msg
        self.chat_comp = qianfan.ChatCompletion()
        self.messages = QfMessages()
        if self.system_message:
            self.messages.append(self.system_message)

    def chat(self, content: str):
        self.messages.append(content, QfRole.User)
        try:
            resp: QfResponse = self.chat_comp.do(model="ERNIE-Speed-128K", messages=self.messages)
            if resp.body and "result" in resp.body:
                self.messages.append(resp)
                return resp.body["result"]
            else:
                return "Error: Invalid response received."
        except Exception as e:
            return f"An error occurred: {str(e)}"


#  for test
if __name__ == '__main__':
    bot = AgentBusterBot()
    print(bot.chat("你好呀"))
