from asyncio import sleep
from aiohttp import ClientSession

from config import headers


async def ensure_session_active(session: ClientSession, user_config: dict):
    """
    自适应激活 Session 状态。
    兼容 Selection 用户 (含 tables) 和 Inquiry 用户 (含 profileId 列表)。
    """
    label = user_config.get("label", "Unknown")
    cookies = user_config.get("cookies")

    pids = set()
    if "tables" in user_config:  # Course Selection Mode: Extract from the tables list
        pids = {t.get("profileId") for t in user_config["tables"] if t.get("profileId")}
    elif "profileId" in user_config:  # Query Mode: Directly retrieve the top-level profileId (supports strings or lists)
        val = user_config["profileId"]
        pids = set(val) if isinstance(val, list) else {val}

    # 按顺序激活 EAMS 会话状态，确保后续请求合法。
    # 顺序：入口 -> 默认页 -> 数据页
    base = "https://jw.shiep.edu.cn/eams/stdElectCourse"

    try:
        async with session.get(f"{base}.action", headers=headers, cookies=cookies, ssl=False, timeout=5) as r:
            if r.status != 200:
                print(f"[Warning] {label}: Entry portal access failed.")
                return False
            if "过快" in await r.text():
                print(f"[Rate Limit] Rate limit triggered for user {label}")
                return False
    except Exception as e:
        print(f"[Error] {label}: Connection error at Entry: {e}")
        return False

    for pid in pids:
        url = f"{base}!defaultPage.action?electionProfile.id={pid}"

        try:
            async with session.get(url, headers=headers, cookies=cookies, ssl=False, timeout=5) as r:
                if r.status != 200:
                    print(f"[Warning] {label}: DefaultPage failed for PID {pid}")
                    return False
                if "过快" in await r.text():
                    print(f"[Rate Limit] Rate limit triggered for user {label} (PID: {pid})")
                    return False
                print(f"[Success] {label}: Session activated for profile {pid}")

            if len(pids) > 1:
                await sleep(0.2)

        except Exception as e:
            print(f"[Error] {label}: Connection error at PID {pid}: {e}")
            return False

    return True
