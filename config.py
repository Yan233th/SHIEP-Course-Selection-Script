url = "https://jw.shiep.edu.cn/eams/stdElectCourse!batchOperator.action"

headers = {
    "Accept": "text/html, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cache-Control": "no-cache",
    "Origin": "https://jw.shiep.edu.cn",
    "Referer": "https://jw.shiep.edu.cn/eams/stdElectCourse!defaultPage.action",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "X-Requested-With": "XMLHttpRequest",
}

data = {
    "optype": "true",
    "operator0": "???:true:0",
}

failed_words = ["上限", "已满", "已达", "已经达到", "冲突"]

error_words = ["失败", "错误", "fail", "error", "503", "过快点击"]
