import asyncio

from baidu_buster.main import baidu_setup

if __name__ == '__main__':
    mobile_numbers = ['18610807044', '13271557189', '13523079221', '13526609822']
    mobile_number = '16638075731'
    cookie_setup = asyncio.run(baidu_setup(mobile_number, handle=True))
