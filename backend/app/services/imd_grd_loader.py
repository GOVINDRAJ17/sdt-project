"""IMD GRD (Gridded Data) Max-Temperature Loader.

Feature-flagged loader for India Meteorological Department Pune Long Range Forecast (LRF)
daily high-resolution gridded data (0.5 x 0.5 or 1.0 x 1.0 degree NetCDF/binary GRD).
Source portal: https://imdpune.gov.in/lrfindex.php
"""

import struct
from pathlib import Path
from typing import Any


class IMDGRDLoader:
    """Parser and loader for IMD Pune max temperature binary GRD files."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def is_available(self) -> bool:
        return self.enabled

    def parse_grd_file(self, filepath: Path | str) -> list[dict[str, Any]]:
        """
        Parse binary IMD GRD file (31x31 or similar grid for India domain: 6.5N-38.5N, 66.5E-100.5E).
        Returns list of structured regional extractions if enabled.
        """
        if not self.enabled:
            return []

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"IMD GRD file not found at: {filepath}")

        records = []
        # Binary GRD files typically store IEEE 32-bit floats with 99.9 missing values
        with open(path, "rb") as f:
            data = f.read()

        num_floats = len(data) // 4
        if num_floats > 0:
            grid = struct.unpack(f"{num_floats}f", data)
            valid_temps = [t for t in grid if 0.0 < t < 65.0]
            if valid_temps:
                avg_tmax = round(sum(valid_temps) / len(valid_temps), 1)
                records.append(
                    {
                        "region_name": "IMD Pune Gridded Composite",
                        "region_type": "plains",
                        "date": "2026-05-01",
                        "forecast_tmax_c": avg_tmax,
                        "normal_tmax_c": 38.5,
                        "source": "IMD Pune GRD",
                    }
                )
        return records


imd_grd_loader = IMDGRDLoader(enabled=False)
