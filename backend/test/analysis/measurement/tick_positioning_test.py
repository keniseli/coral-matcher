from pathlib import Path
from app.analysis.measurement.models import RotatedRuler, TickSignals, TickPositions
from app.analysis.measurement.tick_positioning import TickPositioning
import app.utils.fixtures as fixtures
import matplotlib.pyplot as plt
import numpy as np

tick_positioning = TickPositioning()
save_pickles = True

def test_position_ticks_algalpavona():
    coral_name = "unknown_algalpavona"
    specific = "20260811_1636"
    position_ticks_for(coral_name, specific)
    

def test_position_ticks_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    specific = "20260809_2059"
    position_ticks_for(coral_name, specific)


def test_position_ticks_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260809_2100"
    position_ticks_for(coral_name, specific)


def test_position_ticks_bright_pavona_ruler_visible_and_readable():
    coral_name = "unknown_brightpavona"
    specific = "20260811_1638"
    position_ticks_for(coral_name, specific)


def test_position_ticks_branchy_pavona_ruler_bright_hand_visible():
    coral_name = "unknown_branchypavona"
    specific = "20260811_1637_branchypavona"
    position_ticks_for(coral_name, specific)


def test_position_ticks_dark_pocillopora_scale_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260809_1943"
    position_ticks_for(coral_name, specific)


def test_position_ticks_dark_pocillopora_scale_non_obscured():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1638_darkpocillopora"
    position_ticks_for(coral_name, specific)


def test_position_ticks_dark_pocillopora_scale_non_obscured_two_fingers_visible():
    coral_name = "unknown_darkpocillopora"
    specific = "20260811_1639_darkpocillopora"
    position_ticks_for(coral_name, specific)


def test_position_ticks_green_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    specific = "20260809_2053"
    position_ticks_for(coral_name, specific)


def test_position_ticks_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    specific = "20260809_2101"
    position_ticks_for(coral_name, specific)


def test_position_ticks_leasoned_porites():
    coral_name = "unknown_lesionedporites"
    specific = "20260811_1642"
    position_ticks_for(coral_name, specific)


def test_position_ticks_tiger_pavona():
    coral_name = "unknown_tigerpavona"
    specific = "20260811_1646"
    position_ticks_for(coral_name, specific)


def test_position_ticks_octo_pavona():
    coral_name = "unknown_octopavona"
    specific = "20260811_1642"
    position_ticks_for(coral_name, specific)


def test_position_ticks_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    specific = "20260811_1644"
    position_ticks_for(coral_name, specific)


def test_position_ticks_darth_porites():
    coral_name = "unknown_darthporites"
    specific = "20260811_1639"
    position_ticks_for(coral_name, specific)


def test_position_ticks_spongy_pocillopora():
    coral_name = "unknown_spongypocillopora"
    specific = "20260811_1645"
    position_ticks_for(coral_name, specific)

def test_measure_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    instance_name = "20260819_1813"
    position_ticks_for(coral_name, instance_name)

def position_ticks_for(coral_name: str, instance: str):
    rotation = fixtures.load_pickle(coral_name, f"ruler_rotation_{instance}")
    detection = fixtures.load_pickle(coral_name, f"tick_detection_{instance}")
    debug_name = f"{coral_name}_{instance}"
    
    positions = tick_positioning.find_tick_positions(detection=detection, name_for_debug=debug_name)
    
    if save_pickles: fixtures.save_pickle(coral_name, f"tick_positioning_{instance}", positions)
    
    save_tick_positioning_debug_image(rotation, detection, positions, debug_name)

def debug_outputs(results: TickPositions):
    print(f"Positions: {results.positions}")
    print()
    print()
    
def save_tick_positioning_debug_image(
    rotated_ruler: RotatedRuler,
    signals: TickSignals,
    positions: TickPositions,
    name: str,
) -> None:
    """
    Saves a debug visualization of tick detection and positioning.

    Top:
        Rotated ruler with candidate peaks and final tick positions.

    Bottom:
        1D tick signal with threshold and candidate/final positions.

    Candidate peaks and final positions are intentionally shown separately
    so that positioning decisions can be visually inspected.
    """

    debug_dir = Path(
        "test/analysis/measurement/debug"
    )

    debug_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        debug_dir
        / f"tick_positioning_{name}.png"
    )

    image = rotated_ruler.image

    # ------------------------------------------------------------
    # Prepare image for matplotlib
    # ------------------------------------------------------------

    if image.ndim == 3:
        # OpenCV image is BGR, matplotlib expects RGB.
        display_image = image[:, :, ::-1]
    else:
        display_image = image

    signal = np.asarray(
        signals.signal,
        dtype=np.float32,
    )

    final_positions = np.asarray(
        positions.positions,
        dtype=np.float32,
    )

    strengths = np.asarray(
        positions.strengths,
        dtype=np.float32,
    )

    # ------------------------------------------------------------
    # Create figure
    # ------------------------------------------------------------

    fig, (image_ax, signal_ax) = plt.subplots(
        2,
        1,
        figsize=(16, 8),
        gridspec_kw={
            "height_ratios": [2, 1],
        },
    )

    # ============================================================
    # TOP: ruler image
    # ============================================================

    image_ax.imshow(display_image)

    image_ax.set_title(
        "Tick positioning"
    )

    image_ax.set_xlim(
        0,
        image.shape[1],
    )

    image_ax.set_ylim(
        image.shape[0],
        0,
    )

    # Final positions
    for x, strength in zip(
        final_positions,
        strengths,
    ):
        image_ax.axvline(
            x=float(x),
            linestyle="-",
            linewidth=2.0,
            alpha=0.9,
            label="positioned tick",
        )

        image_ax.text(
            float(x),
            10,
            f"{strength:.2f}",
            rotation=90,
            verticalalignment="top",
            horizontalalignment="right",
            fontsize=8,
        )

    # Avoid duplicate legend entries from every line.
    handles, labels = image_ax.get_legend_handles_labels()

    unique = dict(
        zip(labels, handles)
    )

    image_ax.legend(
        unique.values(),
        unique.keys(),
        loc="upper right",
    )

    image_ax.set_xlabel(
        "x position [px]"
    )

    image_ax.set_ylabel(
        "y position [px]"
    )

    # ============================================================
    # BOTTOM: signal
    # ============================================================

    x = np.arange(
        signal.size
    )

    signal_ax.plot(
        x,
        signal,
        linewidth=1.5,
        label="signal",
    )

    signal_ax.axhline(
        y=signals.threshold,
        linestyle="--",
        linewidth=1.5,
        label=f"threshold ({signals.threshold:.2f})",
    )

    # Final positions
    if final_positions.size > 0:
        # Positions are currently integer-like, but keeping this robust
        # also makes the visualization work if we later infer subpixel
        # positions.
        valid = (
            (final_positions >= 0)
            & (final_positions < signal.size)
        )

        final_x = final_positions[valid]

        final_y = np.interp(
            final_x,
            x,
            signal,
        )

        signal_ax.scatter(
            final_x,
            final_y,
            s=60,
            marker="x",
            linewidths=2,
            label="positioned ticks",
            zorder=4,
        )

    signal_ax.set_title(
        "Tick signal"
    )

    signal_ax.set_xlabel(
        "x position [px]"
    )

    signal_ax.set_ylabel(
        "signal strength"
    )

    signal_ax.set_xlim(
        0,
        signal.size - 1,
    )

    signal_ax.legend()

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)