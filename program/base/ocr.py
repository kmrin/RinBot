# Imports
import pytesseract, cv2, platform, numpy as np
from PIL import Image

# Tesseract path
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Usa o tesseract-ocr pra extrair texto de imagens
def get_string_from_img(img_path):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    cv2.imwrite("cache/ocr/removed_noise.png", img)
    cv2.imwrite(img_path, img)
    result = pytesseract.image_to_string(Image.open(img_path))
    return result