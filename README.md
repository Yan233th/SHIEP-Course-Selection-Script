# Course Selection Engine

This tool provides a command-line interface for batch course registration, inquiry, and session management. It utilizes asynchronous I/O to handle multiple accounts and requests simultaneously.

## Technical Context
The system requires specific session activation sequences to prevent server-side errors. For a detailed technical analysis of the underlying access logic, refer to: [about_access_permissions.md](about_access_permissions.md).

## Installation

This project requires Python 3.10+ and uses `uv` for dependency management.

1. Install the environment and dependencies:
   ```bash
   uv sync
   ```

## Configuration

### 1. Initialize custom.py
Copy the template file to create your local configuration:
```bash
cp custom.py.example custom.py
```

### 2. User Credentials and Tables
Edit `custom.py` to fill the `USER_CONFIGS` and `INQUIRY_USER_DATA` sections.
- **JSESSIONID & SERVERNAME**: Obtain these from the browser developer tools (F12). Navigate to Application -> Storage -> Cookies.
- **profileId**: The internal identifier for the course selection round, found in the network requests of the course system or via the `--inquire` command.
- **course_ids**: The unique identifiers for specific courses.

### 3. Proxy and Network Environments
Configuration of the `USE_PROXY` setting depends on your connection method:
- **Official VPN (EasyConnect) or Campus Network**: These environments usually provide a direct route to the server, requiring `USE_PROXY` to be set to `False`.
- **Third-party VPNs (e.g., EasierConnect)**: These environments often require a SOCKS5 proxy to route traffic. Set `USE_PROXY` to `True` and specify the proxy server address and port within the `proxies` dictionary in `custom.py`.

### 4. API Parameters
Ensure `ENROLLMENT_DATA_API_PARAMS` (containing `projectId` and `semesterId`) matches the current academic term. These values can be extracted from the network traffic when manually loading course counts.

## Usage

Commands are executed via `uv run main.py <command>`.

### Available Commands
- `--start` : Execute registration for all users defined in `USER_CONFIGS`.
  - `--endless`: Optional flag to retry indefinitely until successful. Used for sniping courses as they become available.
- `--inquire`: Interactive mode to search for courses. Supports keywords or field-specific queries (e.g., `teacher=Smith`).
- `--validate`: Batch verification of cookie validity for all accounts.
- `--check`: Real-time verification of course capacity and current enrollment status.
- `--help`: Display the command help menu.

## Characteristics

- **Asynchronous Concurrency**: Built with `asyncio` and `aiohttp` to manage concurrent tasks efficiently.
- **Session Activation**: Automated pre-access routine to satisfy server-side state requirements.
- **Interleaved Scheduling**: Task queuing logic that interleaves course requests to distribute traffic across different profile contexts.
- **Data Sanitization**: Built-in recovery for non-standard JSON responses from legacy endpoints.

## Maintenance and Safety
- **SSL**: Verification is disabled by default to accommodate internal network certificate issues.
- **Termination**: Use `Ctrl+C` to stop the process safely.
- **Cookie Expiry**: If the system returns 302 redirects to a login page, update the `cookies` in `custom.py` with fresh values.
 
