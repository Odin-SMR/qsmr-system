from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel

start_mjd_epoch = datetime(1858, 11, 17, 0, 0, 0, 0, tzinfo=timezone.utc)


class Level2(BaseModel):
    AVK: list[list[float]]
    Altitude: list[float]
    Apriori: list[float]
    ErrorNoise: list[float]
    ErrorTotal: list[float]
    FreqMode: int
    InvMode: str
    Lat1D: float
    Lon1D: float
    Longitude: list[float]
    Latitude: list[float]
    MJD: float
    MeasResponse: list[float]
    Pressure: list[float]
    Product: str
    Quality: int | None
    ScanID: int
    Temperature: list[float]
    VMR: list[float] | None


class Level2i(BaseModel):
    BlineOffset: list[list[float]]
    ChannelsID: list[int]
    FitSpectrum: list[list[float]]
    FreqMode: int
    FreqOffset: float | list[float]
    InvMode: str
    LOFreq: list[float]
    MinLmFactor: float
    PointOffset: float
    Residual: float
    SBpath: float
    STW: list[int]
    ScanID: int
    Tsat: float


class Result(BaseModel):
    L2: list[Level2]
    L2I: Level2i
    L2C: str


def l2_dataframe(batch: list[Level2]) -> DataFrame:
    # Assume all lists in Level2 have the same length
    if not batch:
        return pd.DataFrame()

    # Get the first Level2 object to determine the length
    records = []
    for p in batch:
        n = len(p.AVK)
        for i in range(n):
            rec = {
                "altitude": p.Altitude[i],
                "apriori": p.Apriori[i],
                "error_noise": p.ErrorNoise[i],
                "error_total": p.ErrorTotal[i],
                "freq_mode": p.FreqMode,
                "inv_mode": p.InvMode,
                "lat_1d": p.Lat1D,
                "lon_1d": p.Lon1D,
                "longitude": p.Longitude[i],
                "latitude": p.Latitude[i],
                "mjd": p.MJD,
                "meas_response": p.MeasResponse[i],
                "pressure": p.Pressure[i],
                "product": p.Product.replace(" ", "").replace("/", "-"),
                "quality": p.Quality,
                "scan_id": p.ScanID,
                "temperature": p.Temperature[i],
                "vmr": p.VMR[i] if p.VMR is not None else None,
                # AVK is a list of floats for each row (i-th row of AVK matrix)
                "avk": p.AVK[i] if p.AVK is not None else None,
            }
            records.append(rec)

    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(start_mjd_epoch) + pd.to_timedelta(df["mjd"], unit="d")
    df["quality"] = df["quality"].astype("Int64")
    df["year"] = df.time.dt.year.astype(str).str.zfill(4)  # type: ignore
    df["month"] = df.time.dt.month.astype(str).str.zfill(2)  # type: ignore
    return df.set_index("time").sort_index()


def l2i_dataframe(batch: list[Level2i]) -> DataFrame:
    # Assume all lists in Level2 have the same length
    if not batch:
        return pd.DataFrame()

    # Get the first Level2 object to determine the length
    records = []
    for p in batch:
        n = len(p.BlineOffset)
        for i in range(n):
            rec = {
                "bline_offset": p.BlineOffset[i],
                "channels_id": p.ChannelsID[i],
                "fit_spectrum": p.FitSpectrum[i],
                "freq_mode": p.FreqMode,
                "freq_offset": (
                    p.FreqOffset[i] if isinstance(p.FreqOffset, list) else p.FreqOffset
                ),
                "inv_mode": p.InvMode,
                "lo_freq": p.LOFreq[i],
                "min_lm_factor": p.MinLmFactor,
                "point_offset": p.PointOffset,
                "residual": p.Residual,
                "sb_path": p.SBpath,
                "stw": p.STW[i],
                "scan_id": p.ScanID,
                "tsat": p.Tsat,
            }
            records.append(rec)

    df = pd.DataFrame(records)
    df["scan_id_prefix"] = np.vectorize(lambda x: f"{x >> (6*4):03x}")(
        df.scan_id.to_numpy()
    )
    return df.set_index("scan_id").sort_index()


def save_parquet(input: str, project: str = "dummy") -> None:
    data = json.loads(input)
    parsed_data = Result.model_validate(data)
    df = l2_dataframe(parsed_data.L2)
    df["project"] = project
    df.to_parquet(
        "s3://odin-level2-batch/l2/",
        partition_cols=["project", "freq_mode", "product", "year", "month"],
        index=True,
    )
    dfi = l2i_dataframe([parsed_data.L2I])
    dfi["project"] = project
    dfi.to_parquet(
        "s3://odin-level2-batch/l2i/",
        partition_cols=["project", "freq_mode", "scan_id_prefix"],
        index=True,
    )
