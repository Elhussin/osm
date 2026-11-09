from io import BytesIO
import hashlib
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.core.files.uploadhandler import FileUploadHandler
from django.core.exceptions import RequestDataTooBig

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 16_000_000


class BoundedUploadHandler(FileUploadHandler):
    def __init__(self, request=None):
        super().__init__(request)
        self.total = 0

    def receive_data_chunk(self, raw_data, start):
        self.total += len(raw_data)
        if self.total > MAX_BYTES:
            raise RequestDataTooBig("Uploaded file exceeds the configured size limit")
        return raw_data

    def file_complete(self, file_size):
        return None


def normalize_image(upload):
    if upload is None:
        return None
    if upload.size > MAX_BYTES:
        raise ValidationError({"image": "حجم الصورة يتجاوز 5 ميجابايت."})
    raw = upload.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValidationError({"image": "حجم الصورة يتجاوز 5 ميجابايت."})
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw), formats=["JPEG", "PNG"]) as check:
                if check.width * check.height > MAX_PIXELS or max(check.size) > 6000 or getattr(check, "n_frames", 1) != 1:
                    raise ValueError
                check.verify()
            with Image.open(BytesIO(raw), formats=["JPEG", "PNG"]) as source:
                source.load()
                oriented = ImageOps.exif_transpose(source).convert("RGBA")
                clean = Image.new("RGB", oriented.size, "white")
                clean.paste(oriented, mask=oriented.getchannel("A"))
                output = BytesIO()
                clean.save(output, format="PNG")
                data = output.getvalue()
                if len(data) > MAX_BYTES:
                    raise ValueError
                return {"data": data, "sha256": hashlib.sha256(data).hexdigest(), "width": clean.width, "height": clean.height}
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError({"image": "أرفق صورة JPEG أو PNG سليمة، حتى 5 ميجابايت و16 مليون بكسل وبُعد أقصى 6000 بكسل."}) from None
