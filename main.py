import subprocess
import sys
import os
import signal
import time
from threading import Thread

def run_server():
    server_process = subprocess.Popen(
        ["uvicorn", "server.start_server:app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return server_process

def run_bot():
    bot_process = subprocess.Popen(
        [sys.executable, "tgbot/bot.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return bot_process

def stream_output(process, prefix):
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(f"{prefix}: {line.decode().strip()}")

def main():
    print("Starting server...")
    server_process = run_server()
    server_output_thread = Thread(target=stream_output, args=(server_process, "Server"))
    server_output_thread.daemon = True
    server_output_thread.start()

    time.sleep(2)

    print("Starting bot...")
    bot_process = run_bot()
    bot_output_thread = Thread(target=stream_output, args=(bot_process, "Bot"))
    bot_output_thread.daemon = True
    bot_output_thread.start()

    def signal_handler(signum, frame):
        print("\nShutting down...")
        server_process.terminate()
        bot_process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            if server_process.poll() is not None:
                print("Server process ended unexpectedly")
                break
            if bot_process.poll() is not None:
                print("Bot process ended unexpectedly")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server_process.terminate()
        bot_process.terminate()

if __name__ == "__main__":
    main()