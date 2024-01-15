import asyncio, discord, os
from rinbot.base.logger import logger

img_dir = f"{os.path.realpath(os.path.dirname(__file__))}/rinbot/assets/images/fortnite/images"
img_files = [f for f in os.listdir(img_dir) if f.endswith(".png")]

async def generate_file(img_name) -> discord.File:
    path = os.path.join(img_dir, img_name)
    return discord.File(path, filename=img_name)

# Generates a list of image batches
async def generate_batches(guild_name) -> list:
    batches = []
    for i in range(0, len(img_files), 6):
        batch = []
        img_names = img_files[i:i+6]
        tasks = [generate_file(img) for img in img_names]
        results = await asyncio.gather(*tasks)
        batch.extend(results)
        batches.append(batch)
    logger.info(f"Generated image batch for {guild_name}")
    return batches

async def main():
    batches = await generate_batches("guild1")
    print(batches)

asyncio.run(main())