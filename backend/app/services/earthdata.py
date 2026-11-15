"""NASA Earthdata archives: SMAP, GPM IMERG and GRACE-FO read for a field (phase 8).

The files live in NASA's cloud archives (NSIDC for SMAP, GES DISC for GPM, PO.DAAC for GRACE)
and need a NASA Earthdata login. The server holds a user token (``EARTHDATA_TOKEN``) and never
shows it. A
granule is found through NASA's catalogue (CMR); the archive answers the token with a short-lived
signed address, and the values for the field's pixel are read from the HDF5 file by HTTP range
requests, so a few kilobytes are fetched from a file of many megabytes.

What these are, and are not: SMAP is a 9 km surface (top 5 cm) soil moisture, GPM IMERG a 10 km
rainfall estimate, GRACE a 300 km total water storage anomaly. None is a measurement of the field.
They are regional cross-checks of the model, never inputs to it.
"""

from __future__ import annotations

import io
import logging
import math
import time
import urllib.parse
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
NASA_HOST_SUFFIX = (
    "nasa.gov"  # the token goes to NASA hosts only, never to the signed storage address
)
TIMEOUT_S = 60.0
BLOCK_BYTES = 4 * 1024 * 1024
MAX_REDIRECTS = 8
ATTEMPTS = 3

SMAP_SHORT_NAME = "SPL3SMP_E"
# IMERG Final run (the better one, through September 2025) and the Late run (near real time, after).
GPM_SHORT_NAME = "GPM_3IMERGDF"
GPM_LATE_SHORT_NAME = "GPM_3IMERGDL"
GRACE_SHORT_NAME = "TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4"

# SMAP 9 km EASE-Grid 2.0 global grid (EPSG:6933): 1624 rows by 3856 columns.
EASE_ORIGIN_X = -17_367_530.445
EASE_ORIGIN_Y = 7_314_540.833
EASE_CELL_M = 9_008.055
SMAP_ROWS, SMAP_COLS = 1624, 3856
SMAP_FILL = -9999.0
GPM_CELL_DEG = 0.1
GPM_FILL = -9999.9


class EarthdataError(RuntimeError):
    """A read failed; the text is stored on the job and shown in the Data Center."""


@dataclass(frozen=True)
class Granule:
    title: str
    day: date
    url: str


# --- Finding the files -------------------------------------------------------------------------


def _data_links(entry: dict[str, Any], suffixes: tuple[str, ...]) -> list[str]:
    return [
        link["href"]
        for link in entry.get("links", [])
        if link.get("rel", "").endswith("/data#")
        and link["href"].startswith("https")
        and link["href"].endswith(suffixes)
    ]


def search_granules(
    client: httpx.Client,
    token: str,
    short_name: str,
    start: date,
    end: date,
    *,
    suffixes: tuple[str, ...],
    day_from_title: Any,
) -> list[Granule]:
    """The granules of a product in a period, one per day, with the address of their data file."""
    granules: list[Granule] = []
    page = 1
    while True:
        response = client.get(
            CMR_URL,
            params={
                "short_name": short_name,
                "temporal": f"{start.isoformat()}T00:00:00Z,{end.isoformat()}T23:59:59Z",
                "page_size": 200,
                "page_num": page,
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT_S,
        )
        if response.status_code != 200:
            raise EarthdataError(f"NASA's catalogue answered {response.status_code}")
        entries = response.json().get("feed", {}).get("entry", [])
        for entry in entries:
            links = _data_links(entry, suffixes)
            day = day_from_title(entry["title"])
            if links and day:
                granules.append(Granule(entry["title"], day, links[0]))
        if len(entries) < 200:
            return sorted(granules, key=lambda g: g.day)
        page += 1


def smap_day(title: str) -> date | None:
    """SMAP_L3_SM_P_E_20250501_R19240_002.h5 -> 2025-05-01."""
    for part in title.replace(".", "_").split("_"):
        if len(part) == 8 and part.isdigit():
            return datetime.strptime(part, "%Y%m%d").date()
    return None


def gpm_day(title: str) -> date | None:
    """GPM_3IMERGDF.07:3B-DAY.MS.MRG.3IMERG.20250501-S000000-E235959.V07B.nc4 -> 2025-05-01."""
    for part in title.replace(".", "-").split("-"):
        if len(part) == 8 and part.isdigit():
            return datetime.strptime(part, "%Y%m%d").date()
    return None


# --- Reading a file without downloading it -----------------------------------------------------


def resolve(client: httpx.Client, url: str, token: str) -> tuple[str, int]:
    """Follow the archive's redirects by hand, sending the token to NASA hosts only, until the
    signed storage address. Returns it and the size of the file."""
    for _ in range(MAX_REDIRECTS):
        host = urllib.parse.urlparse(url).netloc
        headers = {"Range": "bytes=0-0"}
        if host.endswith(NASA_HOST_SUFFIX):
            headers["Authorization"] = f"Bearer {token}"
        response = client.get(url, headers=headers, timeout=TIMEOUT_S)
        if response.status_code in (301, 302, 303, 307, 308):
            url = urllib.parse.urljoin(url, response.headers["location"])
            continue
        if response.status_code in (200, 206):
            size = response.headers.get("content-range", "").rpartition("/")[2]
            return url, int(size) if size.isdigit() else int(
                response.headers.get("content-length", 0)
            )
        if response.status_code in (401, 403):
            raise EarthdataError(
                f"The archive refused the token ({response.status_code}); the application for "
                "this archive may need to be authorized in the Earthdata account"
            )
        raise EarthdataError(f"The archive answered {response.status_code}")
    raise EarthdataError("The archive redirected too many times")


class RangeFile(io.RawIOBase):
    """A read-only file backed by HTTP range requests with a small block cache, so that h5py can
    read one pixel of a large HDF5 file without downloading it."""

    def __init__(self, client: httpx.Client, url: str, size: int) -> None:
        self._client, self._url, self._size = client, url, size
        self._pos = 0
        self._blocks: dict[int, bytes] = {}

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self._pos, io.SEEK_END: self._size}[whence]
        self._pos = max(0, base + offset)
        return self._pos

    def _block(self, index: int) -> bytes:
        if index not in self._blocks:
            start = index * BLOCK_BYTES
            end = min(start + BLOCK_BYTES, self._size) - 1
            for attempt in range(ATTEMPTS):
                try:
                    response = self._client.get(
                        self._url, headers={"Range": f"bytes={start}-{end}"}, timeout=TIMEOUT_S
                    )
                    if response.status_code in (200, 206):
                        data = response.content
                        self._blocks[index] = (
                            data if response.status_code == 206 else data[start : end + 1]
                        )
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(2**attempt)
            else:
                raise EarthdataError("A range read of the archive file failed")
            if len(self._blocks) > 8:  # keep memory small: drop the oldest block
                self._blocks.pop(next(iter(self._blocks)))
        return self._blocks[index]

    def readinto(self, buffer: Any) -> int:
        want = min(len(buffer), max(0, self._size - self._pos))
        out = bytearray()
        while len(out) < want:
            index, offset = divmod(self._pos + len(out), BLOCK_BYTES)
            block = self._block(index)
            out += block[offset : offset + (want - len(out))]
        buffer[: len(out)] = out
        self._pos += len(out)
        return len(out)


@contextmanager
def open_hdf5(client: httpx.Client, url: str, token: str) -> Iterator[Any]:
    """The HDF5 file at an archive address, opened by range requests."""
    import h5py

    signed, size = resolve(client, url, token)
    with h5py.File(RangeFile(client, signed, size), "r") as handle:
        yield handle


# --- SMAP -------------------------------------------------------------------------------------


def smap_cell(longitude: float, latitude: float) -> tuple[int, int]:
    """The (row, column) of the SMAP 9 km EASE-Grid 2.0 cell that holds a point."""
    from rasterio.warp import transform

    xs, ys = transform("EPSG:4326", "EPSG:6933", [longitude], [latitude])
    column = int(math.floor((xs[0] - EASE_ORIGIN_X) / EASE_CELL_M))
    row = int(math.floor((EASE_ORIGIN_Y - ys[0]) / EASE_CELL_M))
    if not (0 <= row < SMAP_ROWS and 0 <= column < SMAP_COLS):
        raise EarthdataError("The point is outside the SMAP grid")
    return row, column


def read_smap(handle: Any, row: int, column: int) -> dict[str, float | None]:
    """Morning and evening surface soil moisture (cm3/cm3) of one cell; None where SMAP has no
    retrieval (a gap between orbit swaths, frozen or heavily vegetated ground).

    The evening group names its variables with a ``_pm`` suffix, the morning group does not.
    """
    out: dict[str, float | None] = {}
    for key, group, names in (
        ("soil_moisture_am", "Soil_Moisture_Retrieval_Data_AM", ("soil_moisture",)),
        (
            "soil_moisture_pm",
            "Soil_Moisture_Retrieval_Data_PM",
            ("soil_moisture_pm", "soil_moisture"),
        ),
    ):
        name = next((n for n in names if n in handle[group]), None)
        if name is None:
            out[key] = None
            continue
        value = float(handle[group][name][row, column])
        out[key] = None if value == SMAP_FILL or not 0.0 <= value <= 1.0 else value
    return out


# --- GPM IMERG --------------------------------------------------------------------------------


def gpm_cell(longitude: float, latitude: float) -> tuple[int, int]:
    """The (longitude index, latitude index) of the 0.1 degree IMERG cell that holds a point."""
    return (
        min(3599, int(math.floor((longitude + 180.0) / GPM_CELL_DEG))),
        min(1799, int(math.floor((latitude + 90.0) / GPM_CELL_DEG))),
    )


def read_gpm(handle: Any, lon_index: int, lat_index: int) -> float | None:
    """The day's rainfall in mm of one cell, or None."""
    value = float(handle["precipitation"][0, lon_index, lat_index])
    return None if value <= GPM_FILL + 1 or value < 0 else value


# --- GRACE ------------------------------------------------------------------------------------


def read_grace(handle: Any, longitude: float, latitude: float) -> list[tuple[date, float]]:
    """The monthly liquid water equivalent thickness anomaly (cm) of the 0.5 degree cell holding a
    point, for every month of the file."""
    lats = handle["lat"][:]
    lons = handle["lon"][:]
    lon = longitude % 360.0 if float(lons.max()) > 180.0 else longitude
    i = int(abs(lats - latitude).argmin())
    j = int(abs(lons - lon).argmin())
    series = handle["lwe_thickness"][:, i, j]
    days = handle["time"][:]
    base = date(2002, 1, 1)
    out = []
    for offset, value in zip(days, series, strict=True):
        value = float(value)
        if math.isfinite(value) and abs(value) < 1e4:
            out.append((base + timedelta(days=float(offset)), value))
    return out
