import sys
import asyncio

from main_select_courses import main_select_courses
from inquire_course_info import inquire_course_info
from verify_cookie_validity import verify_cookie_validity
from check_course import check_course


def display_help():
    """
    Show Commands
    """
    print("Usage: python main.py <command>")
    print("Commands:")
    print("  --start    : Select courses for all users")
    print("               [--endless] Retry indefinitely until successful")
    print("  --inquire  : Inquire course info")
    print("  --validate : Batch validate cookie validity")
    print("  --check    : Verify course availability")
    print("  --help     : Show this help message and exit")


async def main():
    args = sys.argv

    if len(args) < 2:
        display_help()
        return

    match args[1].lower():
        case "--start":
            if len(args) > 2 and args[2].lower() == "--endless":
                print("Entering ENDLESS mode.")
                await main_select_courses(endless=True)
            else:
                await main_select_courses()
        case "--inquire":
            await inquire_course_info()
        case "--validate":
            await verify_cookie_validity()
        case "--check":
            await check_course()
        case "--help" | "-h":
            display_help()
        case _:
            print("Error: Unknown command.")
            display_help()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        print("Exiting application.")
