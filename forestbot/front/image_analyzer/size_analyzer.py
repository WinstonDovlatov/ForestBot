from urllib import request
from PIL import ImageFile


def get_sizes(url):
    # source: https://stackoverflow.com/questions/7460218/get-image-size-without-downloading-it-in-python
    # get file size *and* image size (None if not known)
    file = request.urlopen(url)
    size = file.headers.get("content-length")
    if size:
        size = int(size)
    p = ImageFile.Parser()
    while True:
        data = file.read(1024)
        if not data:
            break
        p.feed(data)
        if p.image:
            return size, p.image.size
    file.close()
    return size, None


def is_correct_size(url, max_size, min_size) -> bool:
    max_size_bytes = 15 * 1024 ** 3
    mem_size, size = get_sizes(url)
    if size is not None:
        return (min_size <= size[0] <= max_size) and (min_size <= size[1] <= max_size)

    else:
        return mem_size < max_size_bytes
