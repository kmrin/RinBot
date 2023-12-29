# Imports
from PIL import Image
from program.petpet.petpet_gif import save_transparent_gif
from pkg_resources import resource_stream

# Vars
frames = 10
resolution = (128, 128)
delay = 20

# Gen gif
def make_petpet(source, dest):
    images = []
    base = Image.open(source).convert('RGBA').resize(resolution)
    for i in range(frames):
        squeeze = i if i < frames/2 else frames - 1
        width = 0.8 + squeeze * 0.02
        height = 0.8 - squeeze * 0.05
        offsetX = (1 - width) * 0.5 + 0.1
        offsetY = (1 - height) - 0.08
        canvas = Image.new('RGBA', size=resolution, color=(0, 0, 0, 0))
        canvas.paste(base.resize((round(width * resolution[0]), 
                                  round(height * resolution[1]))), 
                                 (round(offsetX * resolution[0]), 
                                  round(offsetY * resolution[1])))
        pet = Image.open(resource_stream(
            __name__, f"/../assets/images/pet/pet{i}.gif")).convert('RGBA').resize(resolution)
        canvas.paste(pet, mask=pet)
        images.append(canvas)

    save_transparent_gif(images, durations=20, save_file=dest)