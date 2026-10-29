"""Central configuration. Nothing business-rule-shaped should be hardcoded elsewhere."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "app" / "data"

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

FUELHH_CACHE_FILE = DATA_DIR / "fuelhh_wind.parquet"
WINDFOR_CACHE_FILE = DATA_DIR / "windfor.parquet"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = "http://localhost:5173"
    cache_dir: str = str(DATA_DIR)

    # Decision-time forecast rule — the business rule the whole product hinges on.
    # Gate closure is 11:00 UK time the day before delivery. These are the ONLY
    # knobs that should ever need to move if the business rule changes.
    decision_cutoff_time: str = "11:00"
    decision_cutoff_timezone: str = "Europe/London"
    decision_cutoff_days_before: int = 1

    default_confidence: float = 0.9

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
