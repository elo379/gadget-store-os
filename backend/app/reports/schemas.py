from datetime import datetime

from pydantic import BaseModel


class ReportPeriod(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
