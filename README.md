# Telegram Group Stats

## Installation

Prepare your system and clone tdlib:

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

Copy .env.example file and fill it:

```bash
cp example.env .env
```
