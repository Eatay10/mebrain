"""CSV dışa aktarım — formül enjeksiyonuna karşı hücre temizleme (T08)."""

import csv
import io

from fastapi.responses import Response

_DANGEROUS = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value: object) -> str:
    s = "" if value is None else str(value)
    return "'" + s if s.startswith(_DANGEROUS) else s


def csv_response(rows: list[list[object]], filename: str) -> Response:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    for row in rows:
        writer.writerow([safe_cell(v) for v in row])
    return Response(
        "﻿" + buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
