# Modified version of the FireHR data handling script by Miguel Pinto (https://github.com/mnpinto/FireHR/tree/master/)
import asyncio
import time

import ee
import os
import requests
import rasterio
import pandas as pd
import zipfile
import json
from pathlib import Path
import warnings
from banet.geo import open_tif, merge, Region
from multiprocessing import Process

from tqdm.auto import tqdm


proj_name = "forest-bot-browser-proj"

class RegionST(Region):
    "Defines a region in space and time with a name, a bounding box and the pixel size."

    def __init__(self, name: str, bbox: list, pixel_size: float = None, scale_meters: int = None,
                 time_start: str = None, time_end: str = None, time_freq: str = 'D', time_margin: int = 0,
                 shape: tuple = None, epsg=4326):
        super().__init__(name, bbox, pixel_size, epsg, shape)
        if scale_meters is not None and pixel_size is not None:
            raise Exception('Either pixel_size or scale_meters must be set to None.')
        self.name = name
        self.bbox = rasterio.coords.BoundingBox(*bbox)  # left, bottom, right, top
        if pixel_size is not None:
            self.pixel_size = pixel_size
        else:
            self.pixel_size = scale_meters / 111000
        self.epsg = epsg
        self.scale_meters = scale_meters
        self._shape = shape
        self.time_start = pd.Timestamp(str(time_start))
        self.time_end = pd.Timestamp(str(time_end))
        self.time_margin = time_margin
        self.time_freq = time_freq

    @property
    def shape(self):
        "Shape of the region (height, width)"
        if self._shape is None:
            return self.height, self.width
        else:
            return self._shape

    @property
    def times(self):
        "Property that computes the date_range for the region."
        tstart = self.time_start - pd.Timedelta(days=self.time_margin)
        tend = self.time_end + pd.Timedelta(days=self.time_margin)
        return pd.date_range(tstart, tend, freq=self.time_freq)

    @classmethod
    def load(cls, file, time_start=None, time_end=None):
        "Loads region information from json file"
        with open(file, 'r') as f:
            args = json.load(f)
        if time_start is None:
            time_start = args['time_start']
        if time_end is None:
            time_end = args['time_end']
        return cls(args['name'], args['bbox'], args['pixel_size'],
                   time_start=time_start, time_end=time_end)


def extract_region(df_row, cls=Region):
    """Create Region object from a row of the metadata dataframe."""
    if issubclass(cls, RegionST):
        return cls(df_row.event_id, df_row.bbox, df_row.pixel_size,
                   df_row.time_start, df_row.time_end)
    elif issubclass(cls, Region):
        return cls(df_row.event_id, df_row.bbox, df_row.pixel_size)
    else:
        raise NotImplemented('cls must be one of the following [Region, RegionST]')


def coords2bbox(lon, lat, pixel_size):
    return [lon.min(), lat.min(), lon.max() + pixel_size, lat.max() + pixel_size]


def split_region(region: RegionST, size: int, cls=Region):
    lon, lat = region.coords()
    Nlon = (len(lon) // size) * size
    Nlat = (len(lat) // size) * size
    lons = [*lon[:Nlon].reshape(-1, size), lon[Nlon:][None]]
    lats = [*lat[:Nlat].reshape(-1, size), lat[Nlat:][None]]
    if len(lats[-1].reshape(-1)) == 0 and len(lons[-1].reshape(-1)) == 0:
        lons = lons[:-1]
        lats = lats[:-1]
    if issubclass(cls, RegionST):
        return [cls(f'{region.name}.{i}.{j}', coords2bbox(ilon, ilat, region.pixel_size),
                    pixel_size=region.pixel_size, time_start=region.time_start,
                    time_end=region.time_end, time_freq=region.time_freq,
                    time_margin=region.time_margin) for i, ilon in enumerate(lons) for j, ilat in enumerate(lats)]
    else:
        raise NotImplemented('cls must be one of the following [Region, RegionST]')


def merge_tifs(files: list, fname: str, delete=False):
    data, tfm = merge([open_tif(str(f)) for f in files])
    data = data.squeeze()
    fname = Path(files[0]).parent / fname
    profile = open_tif(str(files[0])).profile
    with rasterio.Env():
        height, width = data.shape
        profile.update(width=width, height=height, transform=tfm, compress='lzw')
        with rasterio.open(str(fname), 'w', **profile) as dst:
            dst.write(data, 1)
    if delete:
        for f in files: os.remove(f)


# Cell
def filter_region(image_collection: ee.ImageCollection, region: RegionST, times: tuple, bands=None):
    image_collection = image_collection.filterDate(times[0], times[1])
    geometry = ee.Geometry.Rectangle(region.bbox)
    image_collection = image_collection.filterBounds(geometry)
    if bands is not None:
        image_collection = image_collection.select(bands)
    return image_collection


def filter_cloudy(image_collection: ee.ImageCollection, max_cloud_fraction=0.2):
    return image_collection.filterMetadata(
        'CLOUDY_PIXEL_PERCENTAGE', 'not_greater_than', max_cloud_fraction)


def n_least_cloudy(image_collection: ee.ImageCollection, n=5):
    image_collection = image_collection.sort(prop='CLOUDY_PIXEL_PERCENTAGE')
    image_collection = image_collection.toList(image_collection.size())
    colsize = image_collection.size().getInfo()
    if colsize < n:
        warnings.warn(f'Total number of images in the collection {colsize} less than n={n}. Setting n={colsize}')
        n = colsize
    image_collection = ee.ImageCollection([ee.Image(image_collection.get(i)) for i in range(n)])
    return image_collection


def download_data(R: RegionST, times, products, bands, path_save, scale=None, max_cloud_fraction=None,
                  use_least_cloudy=None, download_crop_size=1000, show_progress=False):
    if scale is None: scale = R.scale_meters
    orig_name = R.name
    path_save.mkdir(exist_ok=True, parents=True)
    if not ((path_save / f'download.{R.name}.{bands[0]}.tif').is_file() and
            (path_save / f'download.{R.name}.{bands[1]}.tif').is_file() and
            (path_save / f'download.{R.name}.{bands[2]}.tif').is_file()):
        sR = [R] if min(R.shape) <= download_crop_size else split_region(R, size=download_crop_size, cls=RegionST)
        fsaves = []
        loop = enumerate(sR) if not show_progress else tqdm(enumerate(sR), total=len(sR))
        processes = []
        for j, R in loop:
            p = Process(target=download_image, args=(
                R, bands, fsaves, j, max_cloud_fraction, path_save, products, scale, times, use_least_cloudy))
            p.Daemon = True
            processes.append(p)
            p.start()
        # download_image(R, bands, fsaves, j, max_cloud_fraction, path_save, products, scale, times, use_least_cloudy)
        # Merge files
        for p in processes:
            p.join()
        suffix = '.tif'
        files = path_save.ls(include=[suffix])
        file_groups = []
        for band in bands:
            file_groups.append([f for f in files if band in str(f)])
        for fs, band in zip(file_groups, bands):
            fsave = f"{orig_name}.download.{band}.tif"
            merge_tifs(fs, fsave, delete=True)


def download_image(R, bands, fsaves, j, max_cloud_fraction, path_save, products, scale, times, use_least_cloudy):
    ee.Initialize(project=proj_name)
    region = (f"[[{R.bbox.left}, {R.bbox.bottom}], [{R.bbox.right}, {R.bbox.bottom}], " +
              f"[{R.bbox.right}, {R.bbox.top}], [{R.bbox.left}, {R.bbox.top}]]")
    if not ((path_save / f'download.{R.name}.{bands[0]}_{j}.tif').is_file() and
            (path_save / f'download.{R.name}.{bands[1]}_{j}.tif').is_file() and
            (path_save / f'download.{R.name}.{bands[2]}_{j}.tif').is_file()):
        # Merge products to single image collection
        imCol = ee.ImageCollection(products[0])
        for i in range(1, len(products)):
            imCol = imCol.merge(ee.ImageCollection(products[i]))
        imCol = filter_region(imCol, R, times=times, bands=bands)
        if max_cloud_fraction is not None:
            imCol = filter_cloudy(imCol, max_cloud_fraction=max_cloud_fraction)
        if use_least_cloudy is not None:
            imCol = n_least_cloudy(imCol, n=use_least_cloudy)
        im = imCol.median()
        imCol = ee.ImageCollection([im])
        colList = imCol.toList(imCol.size())
        # info = colList.getInfo()
        # data_times = [pd.to_datetime(o['properties']['system:time_start'], unit='ms') for o in info]
        # data_cloudy = [o['properties']['CLOUDY_PIXEL_PERCENTAGE'] for o in info]
        # Download each image
        for i in range(colList.size().getInfo()):
            image = ee.Image(colList.get(i))
            fname = f'download.{R.name}'
            # fname = image.get('system:id').getInfo().split('/')[-1]
            fnames_full = [f'{fname}.{b}.tif' for b in bands]
            fnames_partial0 = [f'{fname}.{b}_{j}.tif' for b in bands]
            fnames_full = all([(path_save / f).is_file() for f in fnames_full])
            fnames_partial = all([(path_save / f).is_file() for f in fnames_partial0])
            if not fnames_full:
                fsaves.append([path_save / f for f in fnames_partial0])
                if not fnames_partial:
                    url = image.getDownloadURL(
                        # {'scale': scale, 'crs': 'EPSG:3857',
                        {'scale': scale, 'crs': 'EPSG:4326',
                         'region': f'{region}'})
                    r1 = requests.get(url)
                    # print(r1.status_code, r1.text)
                    with open(str(path_save / f'data.{R.name}.zip'), 'wb') as f:
                        f.write(r1.content)
                    with zipfile.ZipFile(str(path_save / f'data.{R.name}.zip'), 'r') as f:
                        for info in f.infolist():
                            info.filename = f"{R.name}.{info.filename[:-4]}_{j}.tif"
                            f.extract(info, path=str(path_save))
                        # files1 = f.namelist()
                        # f.extractall(str(path_save))
                    os.remove(str(path_save / f'data.{R.name}.zip'))

        # print(f"Done with segment {j}")
