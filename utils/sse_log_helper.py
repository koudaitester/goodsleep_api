# utils/sse_log_helper.py
import asyncio
from collections import deque

log_buffer = deque(maxlen=200)


def push_log(line: str):
    log_buffer.append(line)


async def log_stream_generator():
    while True:
        if log_buffer:
            line = log_buffer.popleft()
            yield f"data: {line}\n\n"
        await asyncio.sleep(0.15)
