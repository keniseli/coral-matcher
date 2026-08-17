from .models import RulerScale

class UnitConversion:
    """
    Converts the RulerScale mm to cm
    """
    def pixels_per_cm(
        self,
        scale: RulerScale,
    ) -> float:
        return scale.pixels_per_mm * 10