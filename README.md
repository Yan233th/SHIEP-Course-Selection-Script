# Course Selection Engine

An asynchronous automation tool for course registration, inquiry, and session management. This engine is designed to handle state-heavy legacy systems by simulating required navigation paths and maintaining persistent session states.

## Technical Context
The system requires specific session activation sequences to prevent server-side errors. For a detailed technical analysis of the underlying access logic, refer to: [about_access_permissions.md](about_access_permissions.md).

## Installation

This project requires Python 3.10+ and uses `uv` for dependency management.

1. Install the environment and dependencies:
   ```bash
   uv sync
   ```

## Configuration Guide

Configuration is managed via `custom.py`. Copy the template to begin:
```bash
cp custom.py.example custom.py
```

### 1. Account Cookies
Required for all operations.
- **How to obtain**: Open the course system in a browser, press `F12`, and navigate to **Application** -> **Storage** -> **Cookies**.
- **Values**: Copy the values for `JSESSIONID` and `SERVERNAME`.
- **Expiry**: If the script returns `302` redirects, your cookies have expired and must be updated in `custom.py`.

### 2. Identifying the Profile ID
The `profileId` is a prerequisite for both inquiry and selection.
- **How to obtain**: Log in to the course system manually and enter the course selection module. Check the browser address bar for the URL; the `profileId` is the numeric value following the `profileId=` parameter.
- **Usage**: Enter this ID in `INQUIRY_USER_DATA` to enable searching, and in `USER_CONFIGS` for registration.

### 3. Fetching Course Information
With valid cookies and a `profileId`, use the inquiry tool to retrieve specific course details.
- **Command**: `uv run main.py --inquire`
- **Function**: This command retrieves course names, teacher information, current enrollment status, and the unique **Course ID**.
- **Usage**: Copy the **Course ID** from the inquiry results into the `course_ids` list under `USER_CONFIGS` for the registration process.

### 4. Proxy and Network Environments
Configuration of the `USE_PROXY` setting depends on your connection method:
- **Official VPN (EasyConnect) or Campus Network**: These environments usually provide a direct route to the server, requiring `USE_PROXY` to be set to `False`.
- **Third-party VPNs (e.g., EasierConnect)**: These environments often require a SOCKS5 proxy to route traffic. Set `USE_PROXY` to `True` and specify the proxy server address and port within the `proxies` dictionary in `custom.py`.

### 5. API Parameters
Configure `ENROLLMENT_DATA_API_PARAMS` with the correct `projectId` and `semesterId`.
- **How to obtain**: Open the browser developer tools (`F12`), switch to the **Network** tab, and refresh the course system page. Search for `projectId` or `semesterId` within the captured requests to find the values for the current academic term.

## Usage

Commands are executed via `uv run main.py <command>`.

### Available Commands
- `--start` : Executes the registration process for all users defined in `USER_CONFIGS`.
  - `--endless`: Optional flag to retry indefinitely until successful. Used for sniping courses as they become available.
- `--inquire`: Interactive mode to search for courses and check enrollment status. Requires a valid `profileId`.
- `--validate`: Batch verification of cookie validity for all accounts.
- `--check`: Real-time verification of course capacity and current enrollment status for courses in your config.
- `--help`: Displays the command help menu.

## Characteristics

- **Asynchronous Concurrency**: Built with `asyncio` and `aiohttp` for efficient multi-account management.
- **Session Activation**: Automated pre-access routine to satisfy server-side state requirements.
- **Rate Limit Protection**: Implements sequential activation and task interleaving to avoid triggering IP or session-based frequency limits.
- **Data Sanitization**: Built-in recovery for non-standard JSON responses from legacy endpoints.

## Maintenance and Safety
- **SSL**: Verification is disabled by default to accommodate internal network certificate issues.
- **Termination**: Use `Ctrl+C` to stop the process safely.
