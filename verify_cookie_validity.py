import asyncio
import aiohttp
from tqdm.asyncio import tqdm

from config import headers
from config_loader import USER_CONFIGS, INQUIRY_USER_DATA
from utils import build_connector

check_url = "https://jw.shiep.edu.cn/eams/stdElectCourse.action"


class CheckResult:
    def __init__(self, label: str, success: bool):
        self.label = label
        self.success = success


async def check(label: str, cookies: dict) -> CheckResult:
    connector = build_connector(label)

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url=check_url,
                headers=headers,
                cookies=cookies,
                timeout=5,
                ssl=False,
                allow_redirects=False,
            ) as response:
                if response.status != 200:
                    return CheckResult(label=label, success=False)

    except Exception:
        return CheckResult(label=label, success=False)

    return CheckResult(label=label, success=True)


async def verify_cookie_validity():
    all_cookies_tasks = []
    print("Collecting cookies...")

    all_cookies_tasks.append(
        check(
            label=INQUIRY_USER_DATA.get("label", "Unknown_User"),
            cookies=INQUIRY_USER_DATA.get("cookies"),
        )
    )

    for user_config in USER_CONFIGS:
        all_cookies_tasks.append(
            check(
                label=user_config.get("label", "Unknown_User"),
                cookies=user_config.get("cookies"),
            )
        )

    if not all_cookies_tasks:
        print("Cannot find any cookies.")
        return

    print(f"Starting verification of all {len(all_cookies_tasks)} cookies...\n")
    results: list[CheckResult] = await tqdm.gather(*all_cookies_tasks, desc="Overall Cookies Verification Progress")

    print("\nAll cookies verification tasks have been processed.")
    await asyncio.sleep(0.1)

    invalid_results: list[CheckResult] = []

    for result in results:
        if not result.success:
            invalid_results.append(result)

    print("\n--- Cookie Verification Summary ---")
    print(f"Total verified: {len(results)}")
    print(f"Valid cookies: {len(results) - len(invalid_results)}")
    print(f"Invalid cookies: {len(invalid_results)}")

    if invalid_results:
        print("\n--- Invalid Cookies Details ---")
        for peer in invalid_results:
            print(f"[INVALID] User: {peer.label}")

    print()
