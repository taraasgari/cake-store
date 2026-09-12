from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def prepare_uploaded_image(
    uploaded_file,
    *,
    min_width=500,
    min_height=500,
    max_dimension=1800,
    max_file_size=10 * 1024 * 1024,
    name_prefix="product",
):
    if not uploaded_file:
        raise ValidationError("فایل تصویر ارسال نشده است.")

    content_type = (
        getattr(uploaded_file, "content_type", "") or ""
    ).lower()

    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            "فرمت تصویر باید JPG، PNG یا WEBP باشد."
        )

    if uploaded_file.size > max_file_size:
        raise ValidationError(
            "حجم هر تصویر نباید بیشتر از ۱۰ مگابایت باشد."
        )

    try:
        uploaded_file.seek(0)

        image = Image.open(uploaded_file)
        image.load()

    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError(
            "فایل انتخاب‌شده تصویر معتبر نیست."
        ) from exc

    image = ImageOps.exif_transpose(image)

    width, height = image.size

    if width < min_width or height < min_height:
        raise ValidationError(
            f"ابعاد تصویر باید حداقل "
            f"{min_width}×{min_height} پیکسل باشد."
        )

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert(
            "RGBA" if "A" in image.getbands() else "RGB"
        )

    image.thumbnail(
        (max_dimension, max_dimension),
        Image.Resampling.LANCZOS,
    )

    output = BytesIO()

    image.save(
        output,
        format="WEBP",
        quality=88,
        method=6,
    )

    output.seek(0)

    original_stem = (
        Path(uploaded_file.name).stem[:70] or name_prefix
    )

    safe_stem = "".join(
        character
        if character.isalnum() or character in ("-", "_")
        else "-"
        for character in original_stem
    ).strip("-") or name_prefix

    return ContentFile(
        output.read(),
        name=f"{safe_stem}.webp",
    )