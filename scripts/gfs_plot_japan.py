import datetime
import requests
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# =====================
# 日本域
# =====================
LAT_MIN, LAT_MAX = 20, 50
LON_MIN, LON_MAX = 120, 150

# =====================
# 最新GFS時刻を決定
# =====================
now = datetime.datetime.utcnow()
cycle = (now.hour // 6) * 6
date = now.strftime("%Y%m%d")
cycle_str = f"{cycle:02d}"

url = (
    f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
    f"gfs.{date}/{cycle_str}/atmos/gfs.t{cycle_str}z.pgrb2.0p25.f024"
)

print("Downloading:", url)

r = requests.get(url)
with open("gfs.grib2", "wb") as f:
    f.write(r.content)

# =====================
# GRIB 読み込み
# =====================
ds = xr.open_dataset(
    "gfs.grib2",
    engine="cfgrib",
    backend_kwargs={
        "filter_by_keys": {
            "typeOfLevel": "isobaricInhPa",
            "level": 500
        },
        "indexpath": ""
    }
)

# 経度補正
ds = ds.assign_coords(
    longitude=((ds.longitude + 180) % 360) - 180
).sortby("longitude")

ds_jp = ds.sel(
    latitude=slice(LAT_MAX, LAT_MIN),
    longitude=slice(LON_MIN, LON_MAX)
)

z = ds_jp["gh"]

# =====================
# 描画
# =====================
fig = plt.figure(figsize=(6, 8))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX])

z.plot(
    ax=ax,
    transform=ccrs.PlateCarree(),
    cmap="viridis",
    cbar_kwargs={"label": "m"}
)

ax.coastlines(resolution="10m")
ax.add_feature(cfeature.BORDERS, linewidth=0.5)
ax.set_title(f"GFS 500hPa Z (+24h) {date} {cycle_str}UTC")

plt.savefig("images/gfs_latest.png", dpi=150, bbox_inches="tight")
plt.close()
