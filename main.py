# Idaho Mean Annual Extreme Low Temperature Map for determining where to plant native species
# Ryan Nielsen, 2025
# Mean Annual Extreme Low Temperature Raster from https://agdatacommons.nal.usda.gov/articles/dataset/2023_USDA_Plant_Hardiness_Zone_Map_Mean_Annual_Extreme_Low_Temperature_Rasters/25343293
# Idaho Counties Shape File from https://hub.arcgis.com/api/v3/datasets/c294041ddf7840c8b1521937105739eb_0/downloads/data?format=shp&spatialRefId=8826&where=1%3D1
# Legend shows estimated temperatures based on existing plant hardiness maps

import rasterio
import folium
import numpy as np
import matplotlib.pyplot as plt
from rasterio.mask import mask
from folium.raster_layers import ImageOverlay
from folium.plugins import Geocoder
import geopandas as gpd
from shapely.geometry import mapping
from PIL import Image

def main():
    tif_path = "Contiguous US/2023ConusNAD83_Clip.tif"
    idaho_shp_path = "Idaho_Counties/Idaho_Counties.shp"
    idaho_gdf = gpd.read_file(idaho_shp_path)
    with rasterio.open(tif_path) as src:
        raster_crs = src.crs
        print("Raster CRS:", raster_crs)
        if idaho_gdf.crs != raster_crs:
            print("Reprojecting Idaho shapefile...")
            idaho_gdf = idaho_gdf.to_crs(raster_crs)
        idaho_shapes = [mapping(geom) for geom in idaho_gdf.geometry]
        idaho_clipped, idaho_transform = mask(src, idaho_shapes, crop=True)
        data = idaho_clipped[0]
        left, bottom, right, top = rasterio.transform.array_bounds(
            idaho_clipped.shape[1],
            idaho_clipped.shape[2],
            idaho_transform
        )
        bounds = [[bottom, left], [top, right]]
        print("Bounds for Idaho:", bounds)
    nodata_value = src.nodata if src.nodata is not None else -32000
    nodata_mask = (data == nodata_value) | np.isnan(data)
    vmin, vmax = np.percentile(data[~nodata_mask], [2, 98])
    data = np.clip(data, vmin, vmax)
    data = (data - vmin) / (vmax - vmin)
    cmap = plt.get_cmap("jet")
    rgba_img = cmap(data)
    rgba_img[nodata_mask, :] = [0, 0, 0, 0]
    rgba_img = (rgba_img * 255).astype(np.uint8)
    image_path = "idaho_colormap_transparent.png"
    Image.fromarray(rgba_img).save(image_path, format="PNG")
    m = folium.Map(
        location=[44.0682, -114.742],
        zoom_start=6,
        tiles=None
    )
    esri_street_map = folium.TileLayer("Esri.WorldStreetMap", name="Esri World Street Map")
    openstreetmap = folium.TileLayer('OpenStreetMap', name='OpenStreetMap')
    openstreetmap.add_to(m)
    esri_street_map.add_to(m)
    Geocoder(
        position="topleft",
        zoom=8
    ).add_to(m)
    ImageOverlay(
        image=image_path,
        bounds=bounds,
        opacity=0.5,
        name="Idaho Climate Overlay"
    ).add_to(m)
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: auto; 
                border:2px solid grey; background:white; z-index:9999; 
                font-size:14px; padding:10px;">
        <b>Mean Annual Extreme Low Temperature (F)</b><br>
        <i style="background:rgba(0, 0, 255, 0.5); width: 20px; height: 20px; display: inline-block;"></i> &nbsp; -20 and below<br>
        <i style="background:rgba(0, 255, 200, 0.5); width: 20px; height: 20px; display: inline-block;"></i> &nbsp; -20 to -10<br>
        <i style="background:rgba(255, 230, 0, 0.5); width: 20px; height: 20px; display: inline-block;"></i> &nbsp; -10 to -5<br>
        <i style="background:rgba(255, 100, 0, 0.5); width: 20px; height: 20px; display: inline-block;"></i> &nbsp; -5 to 5<br>
        <i style="background:rgba(220, 50, 50, 0.7); width: 20px; height: 20px; display: inline-block;"></i> &nbsp; 5 to 10<br>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl().add_to(m)
    m.save("index.html")
    print("Saved Idaho overlay map.")

if __name__ == "__main__":
    main()
