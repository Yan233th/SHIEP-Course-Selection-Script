from asyncio import sleep
from aiohttp import ClientSession

from config import headers
from custom import USE_PROXY, proxies

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    ProxyConnector = None


def build_connector(label: str = ""):
    """
    Build aiohttp connector based on proxy config.
    Returns None (no proxy) if USE_PROXY is False, dependencies missing, or config incomplete.
    """
    if not USE_PROXY:
        return None

    tag = f" ({label})" if label else ""
    if not ProxyConnector:
        print(f"Warning{tag}: USE_PROXY is True, but aiohttp-socks not installed. No proxy.")
        return None

    proxy_url = proxies.get("all")
    if not proxy_url:
        print(f"Warning{tag}: USE_PROXY is True, but proxy URL is empty/missing. No proxy.")
        return None

    return ProxyConnector.from_url(proxy_url)


async def ensure_session_active(session: ClientSession, user_config: dict):
    """
    Adaptively activate session state.
    Compatible with Selection users (with tables) and Inquiry users (with profileId list).
    """
    label = user_config.get("label", "Unknown")
    cookies = user_config.get("cookies")

    pids = set()
    if "tables" in user_config:  # Course Selection Mode: Extract from the tables list
        pids = {t.get("profileId") for t in user_config["tables"] if t.get("profileId")}
    elif "profileId" in user_config:  # Query Mode: Directly retrieve the top-level profileId (supports strings or lists)
        val = user_config["profileId"]
        pids = set(val) if isinstance(val, list) else {val}

    # Activate EAMS session state in order to ensure subsequent requests are valid.
    # Order: Entry -> Default Page -> Data Page
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
