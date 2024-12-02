# Telegram Group Stats

## Installation

Prepare your system and clone tdlib:
```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install make git zlib1g-dev libssl-dev gperf php-cli cmake clang-18 libc++-18-dev libc++abi-18-dev
git clone https://github.com/tdlib/td.git
```

Build tdlib:
```bash
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
```

Copy .so file and remove tdlib folder:
```bash
sudo cp ./td/build/libtdjson.so.1.8.40 ./libtdjson.so
sudo rm -rf ./td
```