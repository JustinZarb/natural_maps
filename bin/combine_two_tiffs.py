import numpy as np
import rasterio
from rasterio.transform import from_origin

# Read the original raster files
with rasterio.open('raster1.tif') as src1:
    raster1 = src1.read(1)

with rasterio.open('raster2.tif') as src2:
    raster2 = src2.read(1)

# Perform computations to create masks (this will depend on your specific needs)
# For this example, let's create a mask where both rasters have values > 0
mask = np.logical_and(raster1 > 0, raster2 > 0)

# Convert the boolean mask to integer format (optional)
mask = mask.astype(rasterio.int32)

# Get the metadata of the original raster
meta = src1.meta

# Update metadata for the mask (number of bands, data type)
meta.update(count=1, dtype=rasterio.int32)

# Save the mask as a new GeoTIFF
with rasterio.open('mask.tif', 'w', **meta) as dst:
    dst.write(mask, 1)