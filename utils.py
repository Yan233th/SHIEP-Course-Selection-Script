from config import headers


async def ensure_session_active(session, user_config):
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

    base = "https://jw.shiep.edu.cn/eams/stdElectCourse"
    for pid in pids:
        # 按顺序激活 EAMS 会话状态，确保后续请求合法。
        # 顺序：入口 -> 默认页 -> 数据页
        steps = [
            f"{base}.action",
            f"{base}!defaultPage.action?electionProfile.id={pid}",
            f"{base}!data.action?profileId={pid}",
        ]

        for i, url in enumerate(steps, 1):
            try:
                async with session.get(url, headers=headers, cookies=cookies, ssl=False, timeout=5) as r:
                    if r.status != 200:
                        print(f"[Warning] User {label}: Step {i} failed (Status: {r.status}, PID: {pid})")
                        return False
            except Exception as e:
                print(f"[Error] User {label}: Connection error at step {i}: {e}")
                return False
        print(f"[Success] User {label}: Session activated for profile {pid}")

    return True
