import datetime
import requests
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import panel as pn

pn.extension('matplotlib')

LAT_MIN, LAT_MAX = 20, 50
LON_MIN, LON_MAX = 120, 150

def download_gfs(fhr):
    now = datetime.datetime.utcnow()
    cycle = (now.hour // 6) * 6
    date = now.strftime("%Y%m%d")
    cycle_str = f"{cycle:02d}"
    url = (
        f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
        f"gfs.{date}/{cycle_str}/atmos/gfs.t{cycle_str}z.pgrb2.0p25.f{fhr:03d}"
    )
    fname = f"gfs_{fhr:03d}.grib2"
    r = requests.get(url)
    with open(fname, "wb") as f:
        f.write(r.content)
    return fname

def plot_gfs(fhr):
    fname = download_gfs(fhr)
    ds = xr.open_dataset(
        fname,
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"typeOfLevel": "isobaricInhPa", "level": 500}, "indexpath": ""}
    )
    ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360) - 180).sortby("longitude")
    ds_jp = ds.sel(latitude=slice(LAT_MAX, LAT_MIN), longitude=slice(LON_MIN, LON_MAX))
    z = ds_jp["gh"]

    fig, ax = plt.subplots(figsize=(6, 8), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX])
    z.plot(ax=ax, transform=ccrs.PlateCarree(), cmap="viridis", cbar_kwargs={"label": "m"})
    ax.coastlines(resolution="10m")
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.set_title(f"GFS 500hPa Z (+{fhr}h) Forecast")
    return fig

# Panelのスライダー
slider = pn.widgets.IntSlider(name='Forecast Hour', start=0, end=240, step=3)
pn.panel(plot_gfs, slider).servable()

# HTMLとして保存
pn.panel(plot_gfs, slider).save("gfs_japan.html", embed=True)
