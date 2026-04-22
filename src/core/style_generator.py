from src.core.structures import LineConfig


class LineType:
    RAW_DATA = "raw"
    FIT_CURVE = "fit"
    RESIDUALS = "res"

def get_default_config(line_id, line_type):
    if line_type == LineType.RAW_DATA:
        return LineConfig(
            label=line_id,
            color="#1f77b4", # Professional Blue
            marker="o",
            line_style="None", # Dots only
            line_width=0
        )
    elif line_type == LineType.FIT_CURVE:
        return LineConfig(
            label=line_id,
            color="#d62728", # Professional Red
            marker="None",
            line_style="-",  # Solid line
            line_width=2.0
        )

    return LineConfig(label=line_id)