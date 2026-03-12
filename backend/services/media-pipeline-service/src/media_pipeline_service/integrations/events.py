from __future__ import annotations

from typing import Dict

from media_pipeline_service.models import EventRecord


class EventPublisher:
    def publish(self, event_name: str, media_asset_id: str, payload: Dict[str, str]) -> EventRecord:
        return EventRecord(event_name=event_name, media_asset_id=media_asset_id, payload=payload)
