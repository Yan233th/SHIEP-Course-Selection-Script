import asyncio
import aiohttp
from tqdm.asyncio import tqdm

from inquire_course_info import get_enrollment_data
from config_loader import USER_CONFIGS, INQUIRY_USER_DATA
from utils import build_connector


class CourseStatus:
    def __init__(self, label: str, id: str, success: bool):
        self.label = label
        self.id = id
        self.success = success


async def check(label: str, id: str, enrollments: dict):
    sc = enrollments.get(id, {}).get("sc")
    lc = enrollments.get(id, {}).get("lc")
    if sc is None or lc is None:
        return CourseStatus(label, id, False)
    try:
        # API may return numbers as strings, explicitly convert to int before comparison
        has_slot = int(sc) < int(lc)
    except (TypeError, ValueError):
        return CourseStatus(label, id, False)
    return CourseStatus(label, id, has_slot)


async def check_course():
    connector = build_connector("Check")

    async with aiohttp.ClientSession(connector=connector) as session:
        print("Fetching enrollment data...")
        enrollments = await get_enrollment_data(session, INQUIRY_USER_DATA.get("cookies"))
        if not enrollments:
            print("Could not fetch enrollment data. Exiting inquiry.")
            return

        all_check_tasks = []
        print("Collecting courses' id...")

        for user_config in USER_CONFIGS:
            user_label = user_config.get("label", "Unknown_User")
            user_tables = user_config.get("tables", [])
            for user_table in user_tables:
                user_course_ids = user_table.get("course_ids", [])
                for course_id in user_course_ids:
                    all_check_tasks.append(
                        check(
                            label=user_label,
                            id=course_id,
                            enrollments=enrollments,
                        )
                    )

        if not all_check_tasks:
            print("Cannot find any course to check.")
            return

        print(f"Starting checking of all {len(all_check_tasks)} courses...\n")
        results: list[CourseStatus] = await tqdm.gather(*all_check_tasks, desc="Overall Courses Checking Progress")

        print("\nAll courses checking tasks have been processed.")
        await asyncio.sleep(0.1)

        invalid_results: list[CourseStatus] = []

        for result in results:
            if not result.success:
                invalid_results.append(result)

        print("\n--- Courses Checking Summary ---")
        print(f"Total checked: {len(results)}")
        print(f"available courses: {len(results) - len(invalid_results)}")
        print(f"Unavailable courses: {len(invalid_results)}")

        if invalid_results:
            print("\n--- Unavailable Courses Details ---")
            for peer in invalid_results:
                print(f"[Unavailable] User: {peer.label} Course: {peer.id}")

        print()
