import asyncio
import csv
import os
import aiohttp
import json
import re
import warnings
from urllib3.exceptions import InsecureRequestWarning

from config import headers
from config_loader import INQUIRY_USER_DATA, ENROLLMENT_DATA_API_PARAMS

from utils import ensure_session_active, build_connector

warnings.simplefilter("ignore", InsecureRequestWarning)


def fix_nonstandard_json(data_str: str) -> str:
    """
    Normalize JSON-like JS object literals into valid JSON.
    Scan character by character, distinguishing "inside strings" from "structure":
      - String contents are preserved verbatim (single quotes unified to double quotes,
        inner double quotes escaped), so apostrophes, commas, colons in values are not broken;
      - Only bare identifiers in "key position" get quotes added;
      - Bare values like true/false/null/numbers are preserved as-is.
    """
    out = []
    i = 0
    n = len(data_str)
    stack = []          # Track containing container: '{' or '['
    expect_key = False  # Whether current position expects an object key

    while i < n:
        c = data_str[i]

        # String literal: copy verbatim, unify quote style
        if c == '"' or c == "'":
            quote = c
            out.append('"')
            i += 1
            while i < n:
                ch = data_str[i]
                if ch == "\\" and i + 1 < n:        # Preserve escape sequence
                    out.append(ch)
                    out.append(data_str[i + 1])
                    i += 2
                    continue
                if ch == quote:                     # Hit matching closing quote
                    i += 1
                    break
                if ch == '"':                       # Bare double quote inside single-quoted string -> escape
                    out.append('\\"')
                    i += 1
                    continue
                out.append(ch)
                i += 1
            out.append('"')
            expect_key = False
            continue

        if c == "{":
            stack.append("{")
            out.append(c)
            expect_key = True
            i += 1
            continue
        if c == "[":
            stack.append("[")
            out.append(c)
            expect_key = False
            i += 1
            continue
        if c == "}" or c == "]":
            if stack:
                stack.pop()
            out.append(c)
            expect_key = False
            i += 1
            continue
        if c == ",":
            out.append(c)
            expect_key = bool(stack) and stack[-1] == "{"
            i += 1
            continue
        if c == ":":
            out.append(c)
            expect_key = False
            i += 1
            continue
        if c.isspace():
            out.append(c)
            i += 1
            continue

        # Bare identifier in key position -> add quotes
        if expect_key and (c.isalpha() or c == "_"):
            j = i
            while j < n and (data_str[j].isalnum() or data_str[j] == "_"):
                j += 1
            out.append('"' + data_str[i:j] + '"')
            i = j
            expect_key = False
            continue

        # Other bare values (numbers / true / false / null) preserved as-is
        out.append(c)
        i += 1

    return "".join(out)


def parse_course_json(data_str: str):
    try:
        parsed_data = json.loads(data_str)
        return parsed_data
    except json.JSONDecodeError:
        print("Course data is non-standard JSON data! Attempting to fix.")
        fixed_data = fix_nonstandard_json(data_str)
        try:
            parsed_data = json.loads(fixed_data)
            print("Course data parsed successfully after fixing!")
            return parsed_data
        except json.JSONDecodeError as e:
            print(f"Parsing still failed after attempting to fix: {e}")
            return None


async def get_course_data(session: aiohttp.ClientSession, profile_id: str, inquiry_cookies: dict) -> list | None:
    url = f"https://jw.shiep.edu.cn/eams/stdElectCourse!data.action?profileId={profile_id}"
    try:
        async with session.get(
            url=url,
            headers=headers,
            cookies=inquiry_cookies,
            timeout=10,
            ssl=False,
            allow_redirects=False,
        ) as response:
            response.raise_for_status()
            raw_data = await response.text(encoding="utf-8")
            raw_data = raw_data.strip()
            json_data_match = re.search(r"\[.*\]", raw_data, re.DOTALL)
            if json_data_match:
                return parse_course_json(json_data_match.group())
            else:
                print("Failed to retrieve valid JSON course data from response.")
                return None
    except aiohttp.ClientError as e:
        print(f"Failed to retrieve course data due to client error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in get_course_data: {e}")
        return None


async def get_enrollment_data(session: aiohttp.ClientSession, inquiry_cookies: dict):
    base_url = "https://jw.shiep.edu.cn/eams/stdElectCourse!queryStdCount.action"
    try:
        async with session.get(
            url=base_url,
            headers=headers,
            cookies=inquiry_cookies,
            params=ENROLLMENT_DATA_API_PARAMS,
            timeout=10,
            ssl=False,
            allow_redirects=False,
        ) as response:
            response.raise_for_status()
            raw_data = await response.text(encoding="utf-8")
            json_data_match = re.search(r"\{.*\}", raw_data, re.DOTALL)
            if json_data_match:
                return parse_course_json(json_data_match.group())
            else:
                print("Failed to retrieve valid JSON enrollment data from response.")
                return None
    except aiohttp.ClientError as e:
        print(f"Failed to retrieve enrollment data due to client error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in get_enrollment_data: {e}")
        return None


def filter_courses(courses: list, keyword: str, enrollments: dict):
    filtered_courses_list = []
    # Check if keyword is in "key=value" format
    if "=" in keyword:
        key, value = keyword.split("=", 1)
        key = key.strip().lower()
        value = value.strip().lower()
    else:
        key = "name"  # Default to searching name
        value = keyword.lower()
    for course in courses:
        search_field = str(course.get(key, "")).lower()
        if value in search_field:
            lesson_id = str(course["id"])
            sc = enrollments.get(lesson_id, {}).get("sc", "N/A")
            lc = enrollments.get(lesson_id, {}).get("lc", "N/A")
            filtered_courses_list.append(
                {
                    "id": course["id"],
                    "no": course["no"],
                    "name": course["name"],
                    "credits": course["credits"],
                    "type": course["type"],
                    "teacher": course["teacher"],
                    "enrolled": sc,
                    "limit": lc,
                }
            )
    return filtered_courses_list


async def inquire_course_info():
    connector = build_connector("Inquiry")

    async with aiohttp.ClientSession(connector=connector) as session:
        # !important
        is_active = await ensure_session_active(session, INQUIRY_USER_DATA)
        if not is_active:
            print("\n[!] Error: Failed to activate Inquiry Session.")
            print("    Please check if INQUIRY_USER_DATA cookies are valid and network is connected.\n")
            return

        inquiry_cookies = INQUIRY_USER_DATA.get("cookies")

        if not inquiry_cookies:
            print("Error: Inquiry cookies not found in config.toml (INQUIRY_USER_DATA). Please configure them.")
            return

        profile_ids: list = INQUIRY_USER_DATA.get("profileId")

        if not profile_ids:
            print("Error: profileId list cannot be empty.")
            return

        all_courses = []
        print(f"Fetching course data for profileIds: {profile_ids}...")

        for profile_id in profile_ids:
            print(f"Fetching course data for profileId: {profile_id}...")
            courses = await get_course_data(session, profile_id, inquiry_cookies)
            if not courses:
                print(f"Could not fetch course data for profileId: {profile_id}. Skipping.")
                continue
            all_courses.extend(courses)

            if len(profile_ids) > 1:
                await asyncio.sleep(0.2)

        if not all_courses:
            print("Could not fetch any course data. Exiting inquiry.")
            return

        # Rename keys in course data
        key_mapping = {
            "id": "id",
            "no": "no",
            "name": "name",
            "credits": "credits",
            "courseTypeName": "type",
            "teachers": "teacher",
        }
        all_courses = [{new_key: course.get(old_key, "") for old_key, new_key in key_mapping.items()} for course in all_courses]

        print("Fetching enrollment data...")
        enrollments = await get_enrollment_data(session, inquiry_cookies)
        if not enrollments:
            print("Could not fetch enrollment data. Exiting inquiry.")
            return

        print("\n--- Course Inquiry Ready ---")
        while True:
            keyword = input("\nInput course name keyword or 'key=value' to search by field ('q' to quit): ").strip().lower()
            if keyword == "q":
                print("Exiting course inquiry.")
                break

            filtered = filter_courses(all_courses, keyword, enrollments)
            if filtered:
                filtered.sort(key=lambda x: (x["type"], -x["credits"], x["id"]))
                print("\nThe matching course information is as follows:")
                for course_item in filtered:
                    print(
                        f"ID: {course_item['id']}, No: {course_item['no']}, Type: {course_item['type']}, "
                        f"Credits: {course_item['credits']}, Enrolled: {course_item['enrolled']}/{course_item['limit']}, "
                        f"Name: {course_item['name']}, Teacher: {course_item['teacher']}"
                    )
                print(f"{len(filtered)} matching courses in total.\n")

                export_choice = input("Do you want to export the filtered courses to a CSV file? (y/n): ").strip().lower()
                if export_choice == "y":
                    file_path = input("Enter the file path to save the CSV (relative or absolute, e.g., 'courses.csv' or '/path/to/courses.csv'): ").strip()
                    if not file_path.endswith(".csv"):
                        file_path += ".csv"
                    file_path = os.path.abspath(file_path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    fieldnames = sorted(filtered[0].keys())
                    try:
                        with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(filtered)
                        print(f"Successfully exported {len(filtered)} filtered courses to {file_path}\n")
                    except Exception as e:
                        print(f"Error writing to file {file_path}: {str(e)}\n")

                # Add course to config
                add_choice = input("Do you want to add any course to config.toml? (y/n): ").strip().lower()
                if add_choice == "y":
                    from config_loader import add_course_to_config, list_user_configs, create_user_config

                    # List available user configs
                    users = list_user_configs()

                    print("\nAvailable user configurations:")
                    print("  [0] Create new user")
                    user_map = {}
                    idx = 1
                    for user in users:
                        for table in user["tables"]:
                            print(f"  [{idx}] {user['label']} - profileId: {table['profileId']}")
                            user_map[idx] = (user['label'], table['profileId'])
                            idx += 1

                    # User selection
                    try:
                        choice_idx = int(input("Select user configuration [number]: ").strip())

                        if choice_idx == 0:
                            # Create new user
                            print("\n--- Create New User ---")
                            label = input("Enter user label (e.g., User_Alice): ").strip()
                            if not label:
                                print("Error: User label cannot be empty")
                                continue

                            profile_id = input("Enter profileId: ").strip()
                            if not profile_id:
                                print("Error: profileId cannot be empty")
                                continue

                            jsessionid = input("Enter JSESSIONID cookie: ").strip()
                            if not jsessionid:
                                print("Error: JSESSIONID cannot be empty")
                                continue

                            servername = input("Enter SERVERNAME cookie: ").strip()
                            if not servername:
                                print("Error: SERVERNAME cannot be empty")
                                continue

                            if not create_user_config(label, profile_id, jsessionid, servername):
                                print("Failed to create user config")
                                continue

                            selected_label = label
                            selected_profile_id = profile_id

                        elif choice_idx in user_map:
                            selected_label, selected_profile_id = user_map[choice_idx]

                        else:
                            print("Invalid selection")
                            continue

                        # Enter course ID(s) with retry loop
                        while True:
                            course_ids_input = input("\nEnter course ID(s) to add (space/comma separated, or 'q' to cancel): ").strip()

                            if course_ids_input.lower() == 'q':
                                print("Add operation cancelled")
                                break

                            # Parse multiple IDs (support space and comma separation)
                            course_ids = [cid.strip() for cid in course_ids_input.replace(',', ' ').split() if cid.strip()]

                            if not course_ids:
                                print("No course ID entered, please try again")
                                continue

                            # Verify all IDs are in current query results
                            invalid_ids = [cid for cid in course_ids if not any(str(c["id"]) == cid for c in filtered)]

                            if invalid_ids:
                                print(f"Error: Course ID(s) not found in current results: {', '.join(invalid_ids)}")
                                print("Please re-enter valid ID(s)")
                                continue  # Retry input

                            # All valid, add one by one
                            success_count = 0
                            for cid in course_ids:
                                if add_course_to_config(selected_label, selected_profile_id, cid):
                                    success_count += 1

                            print(f"✓ Successfully added {success_count}/{len(course_ids)} course(s)")
                            break  # Exit retry loop

                    except ValueError:
                        print("Invalid input, skipping add operation")
                    except KeyboardInterrupt:
                        print("\nAdd operation cancelled")

            else:
                print("No matching course found.")
        print("--- Course Inquiry Ended ---")


if __name__ == "__main__":
    print("--- Independently testing inquire_course_info.py ---")
    print("Ensure INQUIRY_USER_DATA in config.toml is correctly set (cookies).")
    print("Ensure ENROLLMENT_DATA_API_PARAMS in config.py is correctly set.")
    try:
        asyncio.run(inquire_course_info())
    except KeyboardInterrupt:
        print("\nInquiry test interrupted by user.")
    finally:
        print("--- Inquiry test finished ---")
