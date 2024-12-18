url = 'https://jw.shiep.edu.cn/eams/stdElectCourse!batchOperator.action'

headers = {
    'Accept': 'text/html, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://jw.shiep.edu.cn',
    'Referer': 'https://jw.shiep.edu.cn/eams/stdElectCourse!defaultPage.action?electionProfile.id=1614',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

params = {
    'profileId': '1614',
}

data = {
    'optype': 'true',
    'operator0': '???:true:0',
}

# 修改成你的代理端口, 若使用VPN则请删去requests.post中的proxies传参
proxies = {
    "http": "socks5://127.0.0.1:10114",
    "https": "socks5://127.0.0.1:10114"
}

failed_words = ['上限', '已满', '已达', '已经达到', '冲突']

error_words = ['失败', '错误', 'fail', 'error', '503', '过快点击', '上限', '已满', '已达', '已经达到', '冲突']
