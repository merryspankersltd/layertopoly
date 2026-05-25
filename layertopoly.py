"""
Export to Osmium .poly format
QGIS Processing Geoprocessing Tool  —  @alg decorator style

Installation:
  1. Open QGIS
  2. Go to Processing > Toolbox
  3. Click the Python icon (⚙) > "Add Script to Toolbox..."
  4. Select this file
  5. The tool appears under "Scripts > Export to Osmium Poly"
"""

from qgis.processing import alg
from qgis.core import (
    QgsProcessingException,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)


@alg(
    name="exporttoosmiumply",
    label=alg.tr("Export to Osmium .poly"),
    group="export",
    group_label=alg.tr("Export"),
)
@alg.input(type=alg.SOURCE, name="INPUT", label="Input polygon layer")
@alg.input(type=alg.FIELD, name="NAME_FIELD", label="Field to use as polygon name (optional)",
           optional=True, parentLayerParameterName="INPUT")
@alg.input(type=alg.BOOL, name="USE_LAYER_NAME",
           label="Fall back to layer name when no field selected", default=True)
@alg.input(type=alg.FILE_DEST, name="OUTPUT", label="Output .poly file",
           fileFilter="Poly files (*.poly);;All files (*.*)")
def export_to_osmium_poly(instance, parameters, context, feedback, results):
    """
    Exports a polygon layer to the Osmium/osmconvert .poly boundary format.

    Each feature becomes a named block. Multipolygons are supported:
    outer rings → positive numbers, inner rings (holes) → !number.

    The layer must be EPSG:4326, or will be reprojected automatically.

    Feed the output directly to:
      osmium extract --polygon boundary.poly input.pbf -o out.pbf
      osmconvert input.pbf -B=boundary.poly -o=out.pbf
    """

    source         = instance.parameterAsSource(parameters, "INPUT", context)
    output_path    = instance.parameterAsFileOutput(parameters, "OUTPUT", context)
    name_field     = instance.parameterAsString(parameters, "NAME_FIELD", context)
    use_layer_name = instance.parameterAsBool(parameters, "USE_LAYER_NAME", context)

    if source is None:
        raise QgsProcessingException(instance.invalidSourceError(parameters, "INPUT"))

    total = source.featureCount()
    if total == 0:
        raise QgsProcessingException("The input layer contains no features.")

    # CRS / reprojection
    wgs84      = QgsCoordinateReferenceSystem("EPSG:4326")
    source_crs = source.sourceCrs()
    transform  = None

    if source_crs != wgs84:
        feedback.pushWarning(
            f"CRS is {source_crs.authid()} — reprojecting to EPSG:4326 on the fly."
        )
        transform = QgsCoordinateTransform(source_crs, wgs84, QgsProject.instance())

    if not output_path.lower().endswith(".poly"):
        output_path += ".poly"

    lines     = []
    processed = 0

    for feature in source.getFeatures():
        if feedback.isCanceled():
            break

        # Name resolution
        if name_field and feature[name_field] is not None:
            poly_name = str(feature[name_field])
        elif use_layer_name:
            poly_name = source.sourceName()
        else:
            poly_name = f"polygon_{feature.id()}"

        poly_name = poly_name.replace("\n", " ").strip()

        # Geometry
        geom = feature.geometry()
        if geom is None or geom.isEmpty():
            feedback.pushWarning(f"Feature {feature.id()} has no geometry — skipped.")
            continue

        if transform:
            geom.transform(transform)

        geom_type = geom.wkbType()
        if QgsWkbTypes.geometryType(geom_type) != QgsWkbTypes.PolygonGeometry:
            feedback.pushWarning(f"Feature {feature.id()} is not a polygon — skipped.")
            continue

        polygons = (
            geom.asMultiPolygon()
            if QgsWkbTypes.isMultiType(geom_type)
            else [geom.asPolygon()]
        )

        # Write feature block
        lines.append(poly_name)
        ring_counter = 1

        for polygon in polygons:
            for ring_idx, ring in enumerate(polygon):
                label = str(ring_counter) if ring_idx == 0 else f"!{ring_counter}"
                lines.append(label)
                ring_counter += 1

                for point in ring:
                    lines.append(f"\t{point.x():.7f}\t{point.y():.7f}")

                lines.append("END")

        lines.append("END")
        lines.append("")

        processed += 1
        feedback.setProgress(int(processed / total * 100))

    # Write file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as e:
        raise QgsProcessingException(f"Could not write output file: {e}")

    feedback.pushInfo(f"✓ Exported {processed} feature(s) to {output_path}")
    results["OUTPUT"] = output_path