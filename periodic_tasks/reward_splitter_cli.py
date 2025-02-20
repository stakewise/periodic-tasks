import asyncio

from periodic_tasks.reward_splitter.tasks import process_reward_splitter


async def main() -> None:
    await process_reward_splitter()


if __name__ == '__main__':
    asyncio.run(main())
