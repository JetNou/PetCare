from src.pets.routes.pets import router as pets_router
from src.pets.routes.medical_events import router as medical_events_router


__all__ = ["pets_router", "medical_events_router"]