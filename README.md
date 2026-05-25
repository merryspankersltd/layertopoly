# layertopoly

Exports a polygon layer to the Osmium/osmconvert .poly boundary format.

Each feature becomes a named block. Multipolygons are supported:
outer rings → positive numbers, inner rings (holes) → !number.

The layer must be EPSG:4326, or will be reprojected automatically.

Feed the output directly to:
* osmium extract --polygon boundary.poly input.pbf -o out.pbf
* osmconvert input.pbf -B=boundary.poly -o=out.pbf
