from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .metrics import compute_metrics


def metric_table(metrics_a: dict, metrics_b: dict):

    rows = []

    for key in sorted(metrics_a):

        value_a = metrics_a[key]
        value_b = metrics_b[key]

        if isinstance(value_a, float):
            delta = value_b - value_a
        else:
            delta = ""

        rows.append({
            "name": key,
            "before": value_a,
            "after": value_b,
            "delta": delta,
        })

    return rows


def build_context(image_a, image_b):

    metrics_a = compute_metrics(image_a)
    metrics_b = compute_metrics(image_b)

    return {

        "metrics": metric_table(
            metrics_a,
            metrics_b,
        ),

        "figures": {

            "images": "images.png",

            "histogram": "brightness_histogram.png",

            "lab": "lab_scatter.png",

            "sobel_before": "sobel_before.png",
            "sobel_after": "sobel_after.png",

            "laplacian_before": "laplacian_before.png",
            "laplacian_after": "laplacian_after.png",

            "brightness_difference": "brightness_difference.png",

            "texture_difference": "texture_difference.png",
        },
        
        "metric_explanations" : {
           "area_pixels":
                "Number of pixels classified as belonging to the coral area. Useful for tracking changes in visible coral size, but affected by cropping, camera distance and perspective.",

            "dynamic_range_L":
                "Difference between the brightest and darkest coral pixels in the LAB L channel. Indicates the range of perceived brightness within the coral tissue.",

            "laplacian_variance":
                "Measures variation in the Laplacian response, which captures fine intensity changes. Higher values usually indicate more small-scale structural detail or texture.",

            "mean_L":
                "Average LAB L value of the coral area. The L channel represents perceived brightness, making this useful for detecting overall lightness changes.",

            "mean_a":
                "Average LAB a-channel value. Represents the green-to-red colour axis. Changes may indicate shifts in coral pigmentation or imaging conditions.",

            "mean_b":
                "Average LAB b-channel value. Represents the blue-to-yellow colour axis. Changes may indicate shifts in coral pigmentation or environmental appearance.",

            "median_L":
                "Middle LAB L brightness value of all coral pixels. Less affected by extreme bright or dark pixels than the mean and often provides a more robust brightness estimate.",

            "p5_L":
                "5th percentile of LAB L values. Represents the darker end of the coral brightness distribution, excluding the darkest few pixels.",

            "p10_L":
                "10th percentile of LAB L values. Describes the lower brightness range of the coral and helps detect shifts towards darker tissue areas.",

            "p15_L":
                "15th percentile of LAB L values. Captures the lower brightness region of the coral while reducing sensitivity to extreme pixels.",

            "p25_L":
                "25th percentile of LAB L values. Represents the lower quarter of the coral brightness distribution.",

            "p75_L":
                "75th percentile of LAB L values. Represents the upper quarter of the coral brightness distribution.",

            "p85_L":
                "85th percentile of LAB L values. Captures brighter coral regions while reducing sensitivity to isolated highlights.",

            "p90_L":
                "90th percentile of LAB L values. Represents the brighter end of the coral brightness distribution.",

            "p95_L":
                "95th percentile of LAB L values. Captures the brightest coral regions while avoiding influence from only the most extreme pixels.",

            "sobel_mean":
                "Average Sobel gradient magnitude. Measures overall edge strength and structural complexity within the coral image.",

            "sobel_median":
                "Median Sobel gradient magnitude. Represents the typical edge strength while being less affected by isolated sharp boundaries.",

            "sobel_p95":
                "95th percentile of Sobel gradient magnitude. Highlights the strongest edges and fine structural details present in the coral.",

            "sobel_std":
                "Standard deviation of Sobel gradient magnitude. Measures how variable the structural complexity is across the coral surface.",

            "std_L":
                "Standard deviation of LAB L brightness values. Higher values indicate greater variation between darker and brighter coral regions.",

            "std_a":
                "Standard deviation of LAB a-channel values. Measures variation along the green-red colour axis.",

            "std_b":
                "Standard deviation of LAB b-channel values. Measures variation along the blue-yellow colour axis.",
        }
    }


def create_report(
    image_a,
    image_b,
    output_directory: Path,
):

    env = Environment(
        loader=FileSystemLoader(
            Path(__file__).parent / "templates"
        )
    )

    template = env.get_template("report.html")

    context = build_context(
        image_a,
        image_b,
    )

    html = template.render(context)

    report = output_directory / "report.html"

    report.write_text(
        html,
        encoding="utf-8",
    )

    return report