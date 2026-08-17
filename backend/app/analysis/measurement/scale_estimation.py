from .models import TickPositions, RulerScale

class ScaleEstimation:
    """
    Detects repeated interval by detected ticks pattern
    <br />
    <br />
    Produces a debug image showing
    * detected ticks
    * ticks used to establish scale
    * inferred/derived repeating interval
    """
    def estimate_ruler_scale(
    self,
    tick_positions: TickPositions,
) -> RulerScale:
        ...