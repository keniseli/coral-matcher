from .models import RotatedRuler, TickSignals

class TickDetection:
    """
    Detects the metric ticks on the given ruler. Does not qualify
    cm or mm, just identifies signals.
    <br />
    <br />
    Produces a debug image visualizing the detected signal. This stage achieves detecting
    * in/sufficient contrast
    * hand/finger/coral occlusion
    * duplicate edges
    * false peaks
    """
    def detect_ticks(
        self,
        rotated_ruler: RotatedRuler,
        name_for_debug: str | None = None,
    ) -> TickSignals:
        ...