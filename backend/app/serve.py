# MIT-0 License
#
# Copyright (c) 2025 Elevate Human Experiences, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Start the API server."""

import logging
import multiprocessing
import os
import signal
import subprocess
import sys

from helpers.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

cpu_count = multiprocessing.cpu_count()
# Set number of workers as the server count
server_timeout = os.environ.get("SERVER_TIMEOUT", 3600)
server_workers = int(os.environ.get("SERVER_WORKERS", cpu_count))


def sigterm_handler(*pids: int) -> None:
    """Kill all subprocesses and exit."""
    for pid in pids:
        try:
            os.kill(pid, signal.SIGQUIT)
        except OSError:
            pass

    # Clean up the Unix domain socket
    try:
        os.unlink("/tmp/gunicorn.sock")
    except OSError:
        pass

    sys.exit(0)


def start_server() -> None:
    """Start the API server."""
    logger.info(f"Starting API with {server_workers} workers.")

    # Clean up any existing socket file from previous runs
    try:
        os.unlink("/tmp/gunicorn.sock")
    except OSError:
        pass

    # link the log streams to stdout/err so they will be logged to the container logs
    subprocess.check_call(["ln", "-sf", "/dev/stdout", "/var/log/nginx/access.log"])
    subprocess.check_call(["ln", "-sf", "/dev/stderr", "/var/log/nginx/error.log"])

    nginx = subprocess.Popen(["nginx", "-c", "/home/user/app/nginx.conf"])
    uvicorn = subprocess.Popen(
        [
            "uv",
            "run",
            "uvicorn",
            "app:app",
            "--uds",
            "/tmp/gunicorn.sock",
            "--workers",
            str(server_workers),
            "--timeout-keep-alive",
            str(server_timeout),
            "--proxy-headers",
            "--loop",
            "uvloop",
            "--http",
            "h11",
        ],
        cwd="/home/user/app",
    )

    signal.signal(signal.SIGTERM, lambda a, b: sigterm_handler(nginx.pid, uvicorn.pid))

    # If either subprocess exits, so do we.
    pids = {nginx.pid, uvicorn.pid}
    while True:
        pid, _ = os.wait()
        if pid in pids:
            break

    logger.info("API server exiting")
    sigterm_handler(nginx.pid, uvicorn.pid)


if __name__ == "__main__":
    # The main routine just invokes the start function.
    start_server()
