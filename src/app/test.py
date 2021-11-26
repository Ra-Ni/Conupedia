import asyncio
from asyncio import sleep

async def run():
    while True:
        print('2')
        await sleep(5)


if __name__ == '__main__':
    asyncio.run(run())

    while True:
        key = input('prompt')
        if key == 'k':
            exit(0)