import asyncio
import aiohttp
import warnings
from collections import deque
from tqdm.asyncio import tqdm
from urllib3.exceptions import InsecureRequestWarning

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    ProxyConnector = None

from config import url, headers, data as base_data_payload, failed_words, error_words
from custom import USE_PROXY, proxies, USER_CONFIGS

from utils import ensure_session_active

warnings.simplefilter("ignore", InsecureRequestWarning)

ENDLESS = False
failed_courses: list[dict] = []


async def attempt_single_course_selection(
    session: aiohttp.ClientSession,
    course_id: str,
    user_cookies: dict,
    user_params: dict,
    user_label: str,
) -> str:
    """
    Makes a single attempt to select a course for a specific user.
    Sets the provided succeed_event if successful.
    """

    current_data_payload = base_data_payload.copy()
    current_data_payload["operator0"] = f"{course_id}:true:0"

    request_kwargs = {
        "headers": headers,
        "cookies": user_cookies,
        "params": user_params,
        "data": current_data_payload,
        "timeout": 1.5,
        "ssl": False,  # disables SSL cert verification
        "allow_redirects": False,
    }

    profileId = user_params.get("profileId", "N/A")

    try:
        async with session.post(url, **request_kwargs) as response:
            response_text = await response.text()
            print(f"User {user_label} ({profileId}) - Course ID {course_id}: Status {response.status}")

            if response.status == 200:
                if "已经选过" in response_text or not (any(word in response_text for word in failed_words) or any(word in response_text for word in error_words)):
                    if "已经选过" in response_text:
                        print(f"User {user_label} ({profileId}) - Course ID {course_id}: Already selected.\n")
                    else:
                        print(f"User {user_label} ({profileId}) - Course ID {course_id}: Selection Succeeded!\n")
                    return "success"
                elif any(word in response_text for word in failed_words):
                    print(f"User {user_label} ({profileId}) - Course ID {course_id}: Failed (reason: {response_text.strip()}).\n")
                    return "failed"
                elif "当前选课不开放" in response_text:
                    print(f"User {user_label} ({profileId}) - Course ID {course_id}: Failed (error: 操作失败:当前选课不开放).\n")
                elif "请不要过快点击" in response_text:
                    print(f"User {user_label} ({profileId}) - Course ID {course_id}: Failed (error: 请不要过快点击).\n")
                elif any(word in response_text for word in error_words):
                    print(f"User {user_label} ({profileId}) - Course ID {course_id}: Failed (error: {response_text.strip()}).\n")
                else:
                    print(f"User {user_label} ({profileId}) - Course ID {course_id}: 200 OK, outcome unclear (response: {response_text.strip()}).\n")
            elif response.status == 302:
                print(f"User {user_label} ({profileId}) - Course ID {course_id}: Non-200 Status 302. Please check your cookies!!!")
                print(f"Status 302 redirecting to {response.headers.get('Location')}\n")
                return "redirect"
            else:
                print(f"User {user_label} ({profileId}) - Course ID {course_id}: Non-200 Status {response.status} (response: {response_text.strip()}).\n")

    except asyncio.TimeoutError:
        print(f"User {user_label} ({profileId}) - Course ID {course_id}: Request timed out.\n")
    except aiohttp.ClientError as e:
        print(f"User {user_label} ({profileId}) - Course ID {course_id}: Network ClientError: {e}\n")
    except Exception as e:
        print(f"User {user_label} ({profileId}) - Course ID {course_id}: Exception: {e}\n")

    return "error"


async def run_loop_for_single_user(user_config: dict):
    user_label = user_config.get("label", "Unknown_User")
    user_cookies = user_config.get("cookies")
    user_tables = user_config.get("tables")

    connector = None
    if USE_PROXY:
        if ProxyConnector and "all" in proxies:
            proxy_url_val = proxies["all"]
            if proxy_url_val:
                connector = ProxyConnector.from_url(proxy_url_val)
            else:
                print(f"Warning (User {user_label}): USE_PROXY is True, but proxy URL is empty. No proxy.")
        elif not ProxyConnector:
            print(f"Warning (User {user_label}): USE_PROXY is True, but aiohttp-socks not installed. No proxy.")
        else:
            print(f"Warning (User {user_label}): USE_PROXY is True, but 'all' proxy key missing. No proxy.")

    async with aiohttp.ClientSession(connector=connector) as session:
        # !important
        is_active = await ensure_session_active(session, user_config)
        if not is_active:
            print(f"\n[!] User {user_label}: Session activation failed (Entry/DefaultPage/Data Error).")
            print("    Skipping all tasks for this user to avoid illegal parameter errors.\n")
            return

        task_queue = deque()
        task_data_map = {}

        # Interleaved append tasks
        max_length = max(len(table.get("course_ids", [])) for table in user_tables if table.get("profileId")) or 0
        for i in range(max_length):
            for table in user_tables:
                profileId = table.get("profileId")
                course_ids = table.get("course_ids", [])
                if not profileId or not course_ids:
                    print(f"Missing parameter in {user_label}'s table: profileId={profileId}, course_ids={course_ids}")
                    continue
                if i < len(course_ids):
                    course_id = course_ids[i]
                    task_key = (profileId, course_id)
                    task_data = {
                        "session": session,
                        "course_id": course_id,
                        "user_cookies": user_cookies,
                        "user_params": {"profileId": profileId},
                        "user_label": user_label,
                    }
                    task_queue.append(task_key)
                    task_data_map[task_key] = task_data

        if not task_queue:
            print(f"No valid tasks found for user: {user_label}. Exiting selection process.")
            return

        print(f"\nStarting selection for {len(task_queue)} course(s) for user {user_label}...\n")

        while True:
            task_key = task_queue.popleft()
            task_data: dict = task_data_map[task_key]
            status = await attempt_single_course_selection(**task_data)
            # print(status + "\n")

            match status:
                case "success":
                    del task_data_map[task_key]
                case "failed" | "redirect":
                    if ENDLESS:
                        task_queue.append(task_key)
                    else:
                        print(f"Failed completely - ({task_key[0]}, {task_key[1]}) of {user_label}")
                        failed_courses.append(
                            {
                                "user_label": user_label,
                                "profileId": task_key[0],
                                "course_id": task_key[1],
                            }
                        )
                        del task_data_map[task_key]
                case "error" | _:
                    if task_queue:
                        top_task = task_queue.popleft()
                        task_queue.appendleft(task_key)
                        task_queue.appendleft(top_task)
                    else:
                        task_queue.append(task_key)

            if task_queue:
                await asyncio.sleep(0.2)
            else:
                break

    print(f"User {user_label} - Course selection processes has concluded.")


async def main_select_courses(endless=False):
    if not USER_CONFIGS:
        print("No user configurations found in custom.py. Exiting course selection.")
        return

    global ENDLESS
    ENDLESS = endless

    peer_selection_tasks = []
    print("Preparing course selection tasks for all users...")

    for peer_config in USER_CONFIGS:
        if not peer_config.get("cookies") or not peer_config.get("tables"):
            label = peer_config.get("label", "Unknown")
            print(f"Skipping {label}: Missing cookies or tables")
            continue

        peer_selection_tasks.append(
            run_loop_for_single_user(peer_config),
        )

    print(f"\nStarting selection for {len(peer_selection_tasks)} user(s)...\n")
    await tqdm.gather(*peer_selection_tasks, desc="Total Course Selection Progress")

    print("\nAll course selection tasks have been processed.")
    if failed_courses:
        print("\nSummary of failed course selections:")
        for failure in failed_courses:
            print(f"User {failure['user_label']} ({failure['profileId']}) - Course ID {failure['course_id']}: Failed.")
    else:
        print("\nNo failed course selections.")
    await asyncio.sleep(0.1)  # Add a small delay to ensure all print statements from tasks are flushed
