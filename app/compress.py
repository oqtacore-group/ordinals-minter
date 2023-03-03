import pathlib
from PIL import Image

IMAGE_EXTENSIONS = ['.jpeg', '.jpg', '.png']


def compress_file(filepath: pathlib.Path) -> pathlib.Path:
    """Return filepath of compressed image file."""
    if not any(filepath.with_suffix(ext) for ext in IMAGE_EXTENSIONS):
        return filepath

    img = Image.open(filepath)

    filepath, _, ext = str(filepath).rpartition('.')
    compressed_filename = f'{filepath}_compressed.{ext}'

    img.save(compressed_filename, optimize=True)

    return pathlib.Path(compressed_filename)


if __name__ == '__main__':
    #new_filename = compress_file('./storage/0x2f40162f4b966f68300fd54b10ca207e5b542410a80b9c57e98524d9babdbe37_A2-gCLAdlRU.jpg')
    new_filename = compress_file('./storage/0x7e8841d1f38c418de9a20fbdc0103527b185e85efc61bf027f7eb34c7d434a20_avatar.jpg')
    print(new_filename)
