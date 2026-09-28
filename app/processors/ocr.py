from pathlib import Path

import pytesseract
from PIL import Image


class OCRProcessor:

    def process_image(self, file_path: str) -> str:

        path = Path(file_path)

        image = Image.open(path)

        text = pytesseract.image_to_string(image)

        return text.strip()

    def process_pdf_page(self, image) -> str:

        text = pytesseract.image_to_string(image)

        return text.strip()