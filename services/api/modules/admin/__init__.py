"""Backend-enforced administrative APIs and service controls."""
from .service import AdminService, AdminError

__all__ = ["AdminService", "AdminError"]
