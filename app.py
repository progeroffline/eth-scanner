import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from eth_scanner import scan_last_blocks


async def main():
    while True:
        await scan_last_blocks()


if __name__ == "__main__":
    asyncio.run(main())
