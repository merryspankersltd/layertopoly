# layertopoly

## presentation

__layertopoly__ is a qgis processing script.

It exports a polygon layer to the Osmium/osmconvert .poly boundary format.

Each feature becomes a named block. Multipolygons are supported:
outer rings → positive numbers, inner rings (holes) → !number.

The layer must be EPSG:4326, or will be reprojected automatically.

Feed the output directly to:
* osmium extract --polygon boundary.poly input.pbf -o out.pbf
* osmconvert input.pbf -B=boundary.poly -o=out.pbf

## Installation

  1. Open QGIS
  2. Go to Processing > Toolbox
  3. Click the Python icon (⚙) > "Add Script to Toolbox..."
  4. Select this file
  5. The tool appears under "Scripts > Export to Osmium Poly"
