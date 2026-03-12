from media_service.integrations.cdn import CDNClient
from media_service.integrations.events import EventPublisher
from media_service.integrations.storage import ObjectStorageClient
from media_service.integrations.transcoder import TranscoderClient
from media_service.service import MediaService


def build_service() -> MediaService:
    return MediaService(
        storage_client=ObjectStorageClient(),
        transcoder_client=TranscoderClient(),
        cdn_client=CDNClient(),
        event_publisher=EventPublisher(),
    )
