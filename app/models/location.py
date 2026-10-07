from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Location:
    id: int
    lat: float
    lon: float
    category: str  # normalised (casefolded, stripped)
