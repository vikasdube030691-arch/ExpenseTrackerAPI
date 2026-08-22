from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.dashboard_preference import DashboardPreferenceModel
from app.repositories.dashboard_repository import DashboardPreferenceRepository
from app.schemas.dashboard import DashboardPreferenceUpdate


class DashboardService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._preferences = DashboardPreferenceRepository(database)

    async def get_preferences(self, user_id: str) -> DashboardPreferenceModel:
        existing = await self._preferences.get_by_user(user_id)
        if existing is not None:
            return existing
        return await self._preferences.upsert_for_user(user_id, {})

    async def update_preferences(
        self, user_id: str, payload: DashboardPreferenceUpdate
    ) -> DashboardPreferenceModel:
        return await self._preferences.upsert_for_user(user_id, payload.model_dump(exclude_unset=True))
