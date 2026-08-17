from .models import TickDetection, TickPositions

class TickPositioning:
    """
    Identifies individual tick marks and their thickness.
    Does not know metric units, just identifies where individual
    ticks are.
    <br />
    <br />
    Produces a debug image showing detected ticks as vertical 
    line and their intensity/thickness
    """
    def find_tick_positions(
        self,
        detection: TickDetection,
    ) -> TickPositions:
        ...