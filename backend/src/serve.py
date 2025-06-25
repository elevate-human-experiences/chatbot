# MIT License
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
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Copyright (c) 2025 A.I. Hero, Inc.
# All Rights Reserved.
#
# This software and associated documentation files (the "Software") are provided "as is", without warranty
# of any kind, express or implied, including but not limited to the warranties of merchantability, fitness
# for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be
# liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise,
# arising from, out of, or in connection with the Software or the use or other dealings in the Software.
#
# Unauthorized copying of this file, via any medium, is strictly prohibited.

"""Start the API server."""

import logging
import multiprocessing
import os
import signal
import subprocess
import sys

from common.logger import setup_logging

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
    sys.exit(0)


def start_server() -> None:
    """Start the API server."""
    logger.info(f"Starting API with {server_workers} workers.")

    # link the log streams to stdout/err so they will be logged to the container logs
    subprocess.check_call(["ln", "-sf", "/dev/stdout", "/var/log/nginx/access.log"])
    subprocess.check_call(["ln", "-sf", "/dev/stderr", "/var/log/nginx/error.log"])

    nginx = subprocess.Popen(["nginx", "-c", "/home/user/app/nginx.conf"])
    uvicorn = subprocess.Popen(
        [
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
        ]
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
