export interface MetricDefinition {
    id: string;
    group: string;
    label: string;
    explanation: string;
    unit?: string;
}

export interface Metric {
    id: string;
    value: number;
    changePercentage: number;
}

export const metricDefinitions = [
    {
        "id": "MEAN_L",
        "label": "Mean LAB Lightness value [1-100]",
        "group": "Brightness",
        "explanation": "'Overall, is this coral becoming lighter or darker?': Average LAB L value of the coral area. The L channel represents perceived brightness, making this useful for detecting overall lightness changes. 0=Black, 255=white",
    }, {
        "id": "MEDIAN_L",
        "label": "Median LAB Lightness value [1-100]",
        "group": "Brightness",
        "explanation": "'Ignoring a few unusually bright or dark spots, what does most of the coral look like?': Middle LAB L brightness value of the coral area. Less affected by extreme bright or dark pixels than the mean and often provides a more robust brightness estimate. 0=Black, 255=white",
    }, {
        "id": "STD_L",
        "label": "Standard Deviation LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'Does the coral have a uniform appearance, or are there strong contrasts between dark and bright areas?': Standard deviation of LAB L brightness values. Higher values indicate greater variation between darker and brighter coral regions.",
    }, {
        "id": "P5_L",
        "label": "5th Percentile LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'Only 5%% of the pixels are darker': 5th percentile of LAB L values. Represents the darker end of the coral brightness distribution, excluding the darkest few pixels.",
    }, {
        "id": "P10_L",
        "label": "10th Percentile LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'Only 10%% of the pixels are darker': 10th percentile of LAB L values. Describes the lower brightness range of the coral and helps detect shifts towards darker tissue areas.",
    }, {
        "id": "P15_L",
        "label": "15th Percentile LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'15%% of the pixels are darker': 15th percentile of LAB L values. Captures the lower brightness region of the coral while reducing sensitivity to extreme pixels.",
    }, {
        "id": "P25_L",
        "label": "25th Percentile LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'25%% of the pixels are darker': 25th percentile of LAB L values. Represents the lower quarter of the coral brightness distribution.",
    }, {
        "id": "P75_L",
        "label": "75th Percentile LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'25%% of the pixels are brighter': 75th percentile of LAB L values. Represents the upper quarter of the coral brightness distribution.",
    }, {
        "id": "P85_L",
        "label": "85th Percentile LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'15%% of the pixels are brighter': 85th percentile of LAB L values. Captures brighter coral regions while reducing sensitivity to isolated highlights.",
    }, {
        "id": "P90_L",
        "label": "90th Percentile LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'Only 10%% of the pixels are brighter': 90th percentile of LAB L values. Represents the brighter end of the coral brightness distribution.",
    }, {
        "id": "P95_L",
        "label": "95th Percentile LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'5%% of the pixels are brighter': '95th percentile of LAB L values. Captures the brightest coral regions while avoiding influence from only the most extreme pixels. If this increases heavily, there might be a lot of bleaching",
    }, {
        "id": "DYNAMIC_RANGE_L",
        "label": "Dynamic Range LAB Lightness [1-100]",
        "group": "Brightness",
        "explanation": "'How wide is the brightness distribution? How much contrast exists within the coral?': Difference between the brightest and darkest coral pixels in the LAB L channel. Indicates the range of perceived brightness within the coral tissue. Calculated by 95th Percentile - 5th Percentile. Small=Everything roughly same brightness. Large=eg. Dark Crevices, bright tops",
    }, {
        "id": "MEAN_A",
        "label": "Mean Red-Green Color Value [-127-127]",
        "group": "Color",
        "explanation": "'How green/red is the image?': Average LAB a-channel value. Represents the green-to-red colour axis with negative numbers=greenish, positive numbers=redish. Changes may indicate shifts in coral pigmentation or imaging conditions.",
    }, {
        "id": "MEAN_B",
        "label": "Mean Blue-Yellow Color Value [-127-127]",
        "group": "Color",
        "explanation": "'How blue/yellow is the image?': Average LAB b-channel value. Represents the blue-to-yellow colour axis with negative numbers=blueish, positive numbers=yellowish. Changes may indicate shifts in coral pigmentation or environmental appearance.",
    }, {
        "id": "STD_A",
        "label": "Red-Green Variation",
        "group": "Color",
        "explanation": "'Is the coral uniformly coloured, or does it contain patches with different colour tones?': Standard deviation of LAB a-channel values. Measures variation along the green-red colour axis.",
    }, {
        "id": "STD_B",
        "label": "Blue-Yellow Variation",
        "group": "Color",
        "explanation": "'Is the coral uniformly coloured, or does it contain patches with different colour tones?': Standard deviation of LAB b-channel values. Measures variation along the blue-yellow colour axis.",
    }, {
        "id": "SOBEL_MEAN",
        "label": "Sobel Gradient Mean value",
        "group": "Texture",
        "explanation": "Average Sobel gradient magnitude. Measures overall edge strength and structural complexity within the coral image. Changes between coral images can indicate its texture is smoothening (or that the image is not sharp)",
    }, {
        "id": "SOBEL_STD",
        "label": "Sobel Gradient Standard Deviation",
        "group": "Texture",
        "explanation": "Standard deviation of Sobel gradient magnitude. Measures how variable the structural complexity is across the coral surface. Low values=smooth overall. High values=Lots of textural changes",
    }, {
        "id": "SOBEL_MEDIAN",
        "label": "Sobel Gradient Median",
        "group": "Texture",
        "explanation": "Median Sobel gradient magnitude. Represents the typical edge strength while being less affected by isolated sharp boundaries. Changes between coral images can indicate its texture is smoothening (or that the image is not sharp)",
    }, {
        "id": "SOBEL_P95",
        "label": "Sobel 95th Percentile",
        "group": "Texture",
        "explanation": "95th percentile of Sobel gradient magnitude. Highlights the strongest edges and fine structural details present in the coral. This is interesting because it captures the crispiest structural features",
    }, {
        "id": "LAPLACIAN_VARIANCE",
        "label": "Laplacian Variable",
        "group": "Texture",
        "explanation": "Measures variation in the Laplacian response, which captures fine intensity changes. Higher values usually indicate more small-scale structural detail or texture. Also subject to sharpness of coral image.",
    }

];