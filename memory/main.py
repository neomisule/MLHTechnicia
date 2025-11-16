import asyncio
import sys

from MLHTechnicia.memory.mem.response_generator import run_chat
from MLHTechnicia.memory.mem.vectordb import init_qdrant


async def main(user_id):

    try:
        await init_qdrant()
        await run_chat(user_id)
    except KeyboardInterrupt:
        print("Exitting...")
        sys.exit(0)
    except asyncio.exceptions.CancelledError:
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    else:
        user_id = 1
    response = asyncio.run(main(user_id))