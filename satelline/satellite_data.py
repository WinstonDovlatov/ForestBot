import shutil
from pathlib import Path
import math

from satelline.firehr_data import RegionST, download_data
from PIL import Image
import rasterio
import numpy as np
from rasterio.warp import calculate_default_transform, reproject, Resampling

products = ["COPERNICUS/S2"]
bands = ['B4', 'B3', 'B2']  # Red, Green, Blue
dst_crs = 'EPSG:3857'
time_start = '2020-05-01'
time_end = '2020-09-25'

brightness = 4


def epsg3857_to_epsg4326(x, y):
    x = (x * 180) / 20037508.34
    y = (y * 180) / 20037508.34
    y = (math.atan(math.pow(math.e, y * (math.pi / 180))) * 360) / math.pi - 90
    return y, x


def download_rect(image_name, center: (float, float), radius: float, download_dir: Path):
    """
    Must run ee.Initialize() at least once before
    :param image_name: name of the region
    :param center: center of the region in terms of geographical coordinates, (latitude, longitute) (широат, долгота)
    :param radius: radius (degrees)
    :param download_dir: directory to place the downloaded file into
    :return: a function that accepts x and y coordinates of a point in the image and returns the corresponding latitude and longitude

    The downloaded image will be at download_dir/{image_name}
    Note: Format(.jpg, .png) must be specified in image_name
    """
    left, bottom, right, top = center[1] - radius, center[0] - radius, center[1] + radius, center[0] + radius
    region = RegionST(name=image_name,
                      bbox=[left, bottom, right, top],
                      scale_meters=10,
                      time_start=time_start,
                      time_end=time_end)

    time_window = region.times[0], region.times[-1]
    temp_folder = download_dir / f"temp_{image_name}"
    download_data(region, time_window, products, bands, temp_folder, use_least_cloudy=5, download_crop_size=1000)
    with rasterio.open(temp_folder / f'{image_name}.download.B2.tif') as b2_raster:
        b2_data = b2_raster.read()
        orig_transform = b2_raster.transform
        crs = b2_raster.crs
    with rasterio.open(temp_folder / f'{image_name}.download.B3.tif') as b3_raster:
        b3_data = b3_raster.read()
    with rasterio.open(temp_folder / f'{image_name}.download.B4.tif') as b4_raster:
        b4_data = b4_raster.read()

    channels = np.empty([3, b3_data.shape[1], b3_data.shape[2]], dtype=np.float32)
    for index, image in enumerate([b4_data, b3_data, b2_data]):
        channels[index, :, :] = image

    combined_file = Path(temp_folder / f'{image_name}.combined.tiff')
    reprojected_file = Path(temp_folder / f'{image_name}.reprojected.tiff')
    num_chans, height, width = channels.shape

    with rasterio.open(combined_file, 'w', driver='GTiff',
                       height=height, width=width,
                       count=num_chans, dtype=channels.dtype,
                       crs=crs, transform=orig_transform, nodata=0.0) as dst:
        dst.write(channels)
        keys = ['4', '3', '2']
        for index, chan_name in enumerate(keys):
            dst.update_tags(index + 1, name=chan_name)

    with rasterio.open(combined_file) as src:
        new_transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': new_transform,
            'width': width,
            'height': height
        })

        with rasterio.open(reprojected_file, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=new_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)

    with rasterio.open(reprojected_file) as src:
        img = src.read()
        transform = src.transform
    img = img.transpose(1, 2, 0).astype(np.float32) / 10000 * brightness * 255
    img = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    img.save(download_dir / image_name)
    shutil.rmtree(temp_folder)
    return lambda y, x: epsg3857_to_epsg4326(*rasterio.transform.xy(transform, x, y))
