import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from custom import INQUIRY_USER_DATA, USE_PROXY, proxies
from config import headers

# URLs & Configuration
BASE = "https://jw.shiep.edu.cn/eams/stdElectCourse"
PID = INQUIRY_USER_DATA.get("profileId")[0] if isinstance(INQUIRY_USER_DATA.get("profileId"), list) else INQUIRY_USER_DATA.get("profileId")
URLS = {
    "ENTRY": f"{BASE}.action",
    "DEFAULT": f"{BASE}!defaultPage.action?electionProfile.id={PID}",
    "DATA": f"{BASE}!data.action?profileId={PID}",
}


async def hit(session, url):
    """单次点击，返回是否受限"""
    try:
        async with session.get(url, headers=headers, cookies=INQUIRY_USER_DATA["cookies"], ssl=False, timeout=5) as resp:
            return "过快" in await resp.text() or resp.status == 503
    except Exception:
        return True


async def main():
    connector = ProxyConnector.from_url(proxies.get("all")) if USE_PROXY and proxies.get("all") else None
    async with aiohttp.ClientSession(connector=connector) as session:
        print(f"Testing ProfileID: {PID}\n")

        # --- Phase 1: Baselines ---
        baselines = {}
        for key, url in URLS.items():
            print(f"[Phase 1] Establishing baseline for {key}...")
            count = 0
            while count < 30:
                if await hit(session, url):
                    break
                count += 1
                await asyncio.sleep(0.1)
            baselines[key] = count
            print(f"  > {key} can take {count} hits alone.\n")
            await asyncio.sleep(5)  # Cooldown

        # --- Phase 2: Group Iteration ---
        print("[Phase 2] Testing FULL GROUP cycles (ENTRY -> DEFAULT -> DATA) repeatedly...")
        cycles = 0
        cycle_failed_at = None

        while cycles < 30:
            current_cycle = cycles + 1
            print(f"  Cycle {current_cycle:02d}: ", end="", flush=True)

            # 按顺序请求这一组中的每一个
            for key, url in URLS.items():
                if await hit(session, url):
                    cycle_failed_at = key
                    break
                print(f"{key} ", end="", flush=True)

            if cycle_failed_at:
                print(f"-> 🚫 {cycle_failed_at} LIMITED")
                break

            print("-> ✅ OK")
            cycles += 1
            # await asyncio.sleep(0.2)  # 模拟真实操作间隙

        # --- Analysis ---
        print("\n" + "=" * 55)
        print("ANALYSIS COMPLETE")
        print(f"  Min individual baseline: {min(baselines.values())} hits")
        print(f"  Total successful cycles: {cycles}")

        # 核心逻辑判断
        # 如果总循环次数 * 3 接近或等于单点最大阈值，说明是全局共享
        if cycle_failed_at:
            print(f"  Failed at: {cycle_failed_at}")

        print("-" * 55)
        if cycles < min(baselines.values()):
            print("  Conclusion: SHARED POOL DETECTED")
            print("  The entire sequence consumes a global session quota.")
            print("  STRATEGY: Minimize requests in utils.py (KEEP COMMENTED).")
        else:
            print("  Conclusion: NO GLOBAL POOL INTERFERENCE")
            print("  APIs are likely independent or the pool is large enough.")
            print("  STRATEGY: Safe to use, but keep data.action commented to save quota.")
        print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
