from __future__ import annotations

BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def encode_geohash(latitude: float, longitude: float, precision: int = 7) -> str:
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be between -90 and 90")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("longitude must be between -180 and 180")
    if precision < 1:
        raise ValueError("precision must be >= 1")

    lat_min, lat_max = -90.0, 90.0
    lng_min, lng_max = -180.0, 180.0
    bits = [16, 8, 4, 2, 1]

    geohash = []
    bit = 0
    char = 0
    even = True

    for _ in range(precision):
        while bit < 5:
            if even:
                mid = (lng_min + lng_max) / 2
                if longitude >= mid:
                    char |= bits[bit]
                    lng_min = mid
                else:
                    lng_max = mid
            else:
                mid = (lat_min + lat_max) / 2
                if latitude >= mid:
                    char |= bits[bit]
                    lat_min = mid
                else:
                    lat_max = mid
            even = not even
            bit += 1

        geohash.append(BASE32[char])
        char = 0
        bit = 0

    return "".join(geohash)
