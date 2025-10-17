from pydantic import BaseModel, ConfigDict, Field


class CrawledBookDto(BaseModel):
    model_config = ConfigDict(frozen=True)  # Make it immutable

    name: str = Field(..., description="Book title")
    description: str = Field(default="", description="Book description")
    category: str = Field(default="Unknown", description="Book category")
    price_excl_tax: float = Field(..., ge=0, description="Price excluding tax")
    price_incl_tax: float = Field(..., ge=0, description="Price including tax")
    availability: str = Field(..., description="Availability status")
    num_reviews: int = Field(default=0, ge=0, description="Number of reviews")
    image_url: str = Field(default="", description="URL to book cover image")
    rating: int = Field(..., ge=0, le=5, description="Book rating (0-5)")
    source_url: str = Field(..., description="Original URL of the book page")
    html_snapshot: str = Field(default="", description="Raw HTML snapshot")
    content_hash: str = Field(..., description="Hash of important content fields")
