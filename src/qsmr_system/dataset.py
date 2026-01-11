from __future__ import annotations

import json
from datetime import UTC, datetime

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel

start_mjd_epoch = datetime(1858, 11, 17, 0, 0, 0, 0, tzinfo=UTC)


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
    L2: Level2 | list[Level2]
    L2I: Level2i
    L2C: str


def l2_dataframe(batch: Level2 | list[Level2]) -> DataFrame:
    # Assume all lists in Level2 have the same length
    if not batch:
        return pd.DataFrame()

    # Get the first Level2 object to determine the length
    records = []
    if isinstance(batch, Level2):
        batch = [batch]
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
    df["year"] = df.time.dt.year.astype(str).str.zfill(4)
    df["month"] = df.time.dt.month.astype(str).str.zfill(2)
    return df.set_index("time").sort_index()


def l2i_dataframe(batch: Level2i, mjd: float) -> DataFrame:
    records = []
    n = len(batch.STW)
    for i in range(n):
        rec = {
            "bline_offset": [b[i] for b in batch.BlineOffset],
            "channels_id": batch.ChannelsID[i],
            "fit_spectrum": batch.FitSpectrum[i],
            "freq_mode": batch.FreqMode,
            "freq_offset": (
                batch.FreqOffset[i]
                if isinstance(batch.FreqOffset, list)
                else batch.FreqOffset
            ),
            "inv_mode": batch.InvMode,
            "lo_freq": batch.LOFreq[i],
            "min_lm_factor": batch.MinLmFactor,
            "point_offset": batch.PointOffset,
            "residual": batch.Residual,
            "sb_path": batch.SBpath,
            "stw": batch.STW[i],
            "scan_id": batch.ScanID,
            "tsat": batch.Tsat,
        }
        records.append(rec)
    if len(records) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(start_mjd_epoch) + pd.to_timedelta(mjd, unit="d")
    df["year"] = df.time.dt.year.astype(str).str.zfill(4)
    df["month"] = df.time.dt.month.astype(str).str.zfill(2)
    return df.set_index("time").sort_index()


def save_parquet(input_data: str, project: str = "dummy") -> None:
    processed = pd.Timestamp.now(tz=UTC)
    print("Saving parquet for project:", project)
    # with open("debug.json", "w") as f:
    #     f.write(input_data)
    data = json.loads(input_data)

    parsed_data = Result.model_validate(data)
    df = l2_dataframe(parsed_data.L2)
    if not df.empty:
        df["project"] = project
        df["processed"] = processed
        df.to_parquet(
            "s3://odin-level2-batch/l2/",
            partition_cols=["project", "freq_mode", "product", "year", "month"],
            index=True,
        )
        mjd = df["MJD"].iloc[0]
        dfi = l2i_dataframe(parsed_data.L2I, mjd)
        if not dfi.empty:
            dfi["project"] = project
            dfi["errors"] = parsed_data.L2C
            dfi["processed"] = processed
            dfi.to_parquet(
                "s3://odin-level2-batch/l2i/",
                partition_cols=["project", "freq_mode", "year", "month"],
                index=True,
            )
