# Telegram Group Stats

This project provides a streamlined approach to extracting and analyzing information about Telegram groups using TDLib.

It allows you to retrieve and analyze user membership data, find common groups between users, and run analytics through
a convenient Streamlit interface.

## Overview

- [x] **Connection to Telegram:** Connects to Telegram and authorizes a user session.
- [x] **Basic group chat listing:** Fetches and displays all basic groups you are a member of.
- [x] **Chat member retrieval:** Retrieves all users in a selected group.
- [x] **Common group analysis:** Calculates how many groups each user shares with you.
- [x] **Streamlit UI:** Provides an interactive interface to search groups and run analysis.
- [x] **Write basic tests:** Write basic tests to ensure the application works as expected.
- [ ] **Support for Supergroups/Channels:** Extend the logic to handle supergroups and channel members.
- [ ] **Extended analytics:** Add more metrics (e.g., message counts, user activity levels, common interests).
- [ ] **Build graph visualization:** Display group relationships in a graph.
- [ ] **Authentication improvements:** Authorize using OAuth method.
- [ ] **Improved UI:** Add more features and improve the interface.

## Tech overview
**Core Functionality:**

- Connect to Telegram through TDLib and authorize a user session.
- Retrieve and display a list of Telegram groups (basic groups).
- Fetch detailed member lists from these groups.
- Analyze the common groups shared with each member in a selected group.
- Display results interactively using a Streamlit application.

**Key Components:**

- **TDLibClient:** Handles low-level interaction with TDLib, including authorization, sending requests, and receiving
  events.
- **ChatMemberService:** Provides higher-level operations for retrieving chat info, members, and common groups with
  other users.
- **Streamlit App (main.py):** Offers an interface to select groups, run analysis, and view results.


## Inference

### Set up Environment Variables

Copy the example environment file and fill in your `APP_ID` and `APP_HASH`:

```bash
cp example.env .env
```

Your .env file should look like:

```
API_ID=your_api_id_here
API_HASH=your_api_hash_here
DATABASE_DIR=tdlib
TDLIB_LOGGING_LEVEL=2
TELEGRAM_BOT_TOKEN=your_bot_token_here
```


Then use `docker-compose`:

```bash
docker-compose up
```

Visit http://localhost:8501 to see the Streamlit app.

## Development

**Prerequisites:**

- Linux-based system
- `cmake`, `g++`, `zlib1g-dev`, `libssl-dev`, `gperf`, `make`, `git`
- Python 3.11+
- Poetry (for dependency management)

### Build and Install TDLib

Prepare your system and clone the TDLib repository:

```bash
sudo apt-get update && sudo apt-get upgrade && \
sudo apt-get install make git zlib1g-dev libssl-dev gperf cmake g++ && \
git clone https://github.com/tdlib/td.git
```

Build tdlib:

```bash
cd td && mkdir build && cd build && \
cmake -DCMAKE_BUILD_TYPE=Release .. && cmake --build . && \
cd ../../ && cp ./td/build/libtdjson.so.1.8.40 ./libtdjson.so
```

## Tests

Detailed description will be added in the future.

You can view the tests here:
```
tests/
├── test_client.py
└── test_processor.py
```

Run:
```bash
pytest
```

## License

This project is licensed under the MIT License.
