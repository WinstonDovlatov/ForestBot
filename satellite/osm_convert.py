from typing import Callable

import numpy as np
import cv2

import xml.etree.ElementTree as ET


def get_lines(mask, coord_transform: Callable):
    skel = np.zeros(mask.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    img = mask.copy()
    for i in range(10):
        open_morph = cv2.morphologyEx(img, cv2.MORPH_OPEN, element)
        temp = cv2.subtract(img, open_morph)
        eroded = cv2.erode(img, element)
        if i > 0:
            skel = cv2.bitwise_or(skel, temp)
        img = eroded.copy()
        if cv2.countNonZero(img) == 0:
            break

    cont, _ = cv2.findContours(skel, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_NONE)
    cont = sorted(cont, key=lambda x: len(x), reverse=True)

    osm = ET.Element("osm", attrib={"version": "0.6"})

    nodes = {}
    count = 0
    for way in cont:
        way_el = ET.SubElement(osm, "way", {"id": str(count)})
        count += 1
        for x, y in way.squeeze(1):
            lat, lon = coord_transform(x, y)
            if (lat, lon) not in nodes:
                nodes[(lat, lon)] = count
                ET.SubElement(osm, "node", {"id": str(count), "lat": str(lat), "lon": str(lon)})
                count += 1
            ET.SubElement(way_el, "nd", {"ref": str(nodes[(lat, lon)])})

    return osm
