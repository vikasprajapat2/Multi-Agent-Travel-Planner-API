import os
import sys 
import random 
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.diename(os.path.abspath(__file__)))

from config import USE_MOCK_APIS

# hotelOption dataclass

@dataclass
class HotelOption:
    name: str
    stars: int
    area: str
    price_per_night: int
    total_price: int
    rating: float 
    amenities: str 
    cancellation: str
    breakfast: bool 
    category: str

    def to_dect(self) -> dict:
        return asdict(self)
    
    def summary(self) -> str:
        start_str ="*" * self.stars
        bkfstn =" | Breakfast incl." if self.breakfast else ""
        return (
            f"{self.name} {starts_str} | {self.area} |"
            f"₹{self.price_per_night:,}/night | "
            f"Rating: {self.rating}/10{bkfst}"
        )
    
