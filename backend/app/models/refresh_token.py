from app.models.common import CreatedAtDocument, PyObjectId, UTCDatetime


class RefreshTokenModel(CreatedAtDocument):
    user_id: PyObjectId
    token_hash: str
    user_agent: str | None = None
    ip_address: str | None = None
    expires_at: UTCDatetime
    revoked: bool = False
    revoked_at: UTCDatetime | None = None
