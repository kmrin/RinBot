import asyncio

async def main() -> None:
    tasks = []
    
    async def generate_obj(name) -> str:
        return name
    
    async def generate_string():
        tasks.append(asyncio.create_task(generate_obj("penis")))
    
    await generate_string()
    await asyncio.gather(*tasks)
    
    for i in tasks:
        print(i.result())

asyncio.run(main())