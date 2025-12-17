import datetime
import requests
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os

# =====================
# 日本域
# =====================
LAT_MIN, LAT_MAX = 20, 50
LON_MIN, LON_MAX = 120, 150
os.makedirs("images", exist_ok=True)

# =====================
# GFS GRIB取得関数
# =====================
def download_gfs(fhr):
    now = datetime.datetime.utcnow()
    cycle = (now.hour // 6) * 6
    date = now.strftime("%Y%m%d")
    cycle_str = f"{cycle:02d}"
    
    url = (
        f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/"
        f"gfs.{date}/{cycle_str}/atmos/gfs.t{cycle_str}z.pgrb2.0p25.f{fhr:03d}"
    )
    fname = f"images/gfs_{fhr:03d}.grib2"
    
    # 既存ファイルがあればスキップ
    if os.path.exists(fname):
        print(f"{fname} already exists, skipping download.")
        return fname

    print("Downloading:", url)
    r = requests.get(url)
    if r.status_code != 200:
        raise RuntimeError(f"Failed to download: {url} (status {r.status_code})")
    if len(r.content) < 1000:
        raise RuntimeError(f"Downloaded file too small: {fname}")

    with open(fname, "wb") as f:
        f.write(r.content)
    return fname
# =====================
# 描画関数
# =====================
def plot_gfs(fhr):
    """指定予報時間の500hPa高度と降水量を描画しPNG保存"""
    fname = download_gfs(fhr)
    ds = xr.open_dataset(
        fname,
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"typeOfLevel": "isobaricInhPa", "level": 500}, "indexpath": ""}
    )
    
    # 経度補正
    ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360) - 180).sortby("longitude")
    ds_jp = ds.sel(latitude=slice(LAT_MAX, LAT_MIN), longitude=slice(LON_MIN, LON_MAX))
    z = ds_jp["gh"]
    
    # 描画
    fig, ax = plt.subplots(figsize=(6,8), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX])
    z.plot(ax=ax, transform=ccrs.PlateCarree(), cmap="viridis", cbar_kwargs={"label": "m"})
    ax.coastlines(resolution="10m")
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.set_title(f"GFS 500hPa Z Forecast +{fhr}h")
    
    png_fname = f"images/gfs_{fhr:03d}.png"
    plt.savefig(png_fname, dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved:", png_fname)
# =====================
# 0h～240hまで3hごとに描画
# =====================
for fhr in range(0, 241, 3):
    plot_gfs(fhr)

# =====================
# HTML生成（スライダー切替用）
# =====================
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>GFS Japan Forecast</title>
</head>
<body>
    <h2>GFS Forecast Japan 500hPa Z</h2>
    <input type="range" min="0" max="240" step="3" id="slider" value="0">
    <span id="fhr_label">0h</span>
    <br>
    <img id="gfs_img" src="images/gfs_000.png" width="600">
    
    <script>
    const slider = document.getElementById("slider");
    const img = document.getElementById("gfs_img");
    const label = document.getElementById("fhr_label");
    
    slider.addEventListener("input", function() {
        let val = String(slider.value).padStart(3,'0');
        img.src = `images/gfs_${val}.png`;
        label.textContent = slider.value + "h";
    });
    </script>
</body>
</html>
"""

with open("gfs_japan.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("HTML saved as gfs_japan.html")
