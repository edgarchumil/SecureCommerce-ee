from enum import StrEnum

from app.models.identity import RoleCode


class Permission(StrEnum):
    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_UPDATE = "organization:update"
    MEMBERSHIP_READ = "membership:read"
    MEMBERSHIP_MANAGE = "membership:manage"
    AUDIT_READ = "audit:read"
    SESSION_READ_SELF = "session:read:self"
    SESSION_REVOKE_SELF = "session:revoke:self"
    ASSET_READ = "asset:read"
    ASSET_CREATE = "asset:create"
    ASSET_UPDATE = "asset:update"
    ASSET_DELETE = "asset:delete"
    EVALUATION_READ = "evaluation:read"
    EVALUATION_CREATE = "evaluation:create"
    EVALUATION_ANSWER = "evaluation:answer"
    EVALUATION_REVIEW = "evaluation:review"
    RISK_READ = "risk:read"
    RISK_WRITE = "risk:write"
    RISK_DELETE = "risk:delete"
    RISK_SETTINGS = "risk:settings"
    DASHBOARD_READ = "dashboard:read"
    AI_READ = "ai:read"
    AI_GENERATE = "ai:generate"
    AI_REVIEW = "ai:review"
    REPORT_READ = "report:read"
    REPORT_CREATE = "report:create"
    INCIDENT_READ = "incident:read"
    INCIDENT_WRITE = "incident:write"
    NOTIFICATION_READ = "notification:read"


ROLE_PERMISSIONS: dict[RoleCode, frozenset[Permission]] = {
    RoleCode.SUPERADMIN: frozenset(Permission),
    RoleCode.ORG_ADMIN: frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.ORGANIZATION_UPDATE,
            Permission.MEMBERSHIP_READ,
            Permission.MEMBERSHIP_MANAGE,
            Permission.AUDIT_READ,
            Permission.SESSION_READ_SELF,
            Permission.SESSION_REVOKE_SELF,
            Permission.ASSET_READ,
            Permission.ASSET_CREATE,
            Permission.ASSET_UPDATE,
            Permission.ASSET_DELETE,
            Permission.EVALUATION_READ,
            Permission.EVALUATION_CREATE,
            Permission.EVALUATION_ANSWER,
            Permission.EVALUATION_REVIEW,
            Permission.RISK_READ,
            Permission.RISK_WRITE,
            Permission.RISK_DELETE,
            Permission.RISK_SETTINGS,
            Permission.DASHBOARD_READ,
            Permission.AI_READ,
            Permission.AI_GENERATE,
            Permission.AI_REVIEW,
            Permission.REPORT_READ,
            Permission.REPORT_CREATE,
            Permission.INCIDENT_READ,
            Permission.INCIDENT_WRITE,
            Permission.NOTIFICATION_READ,
        }
    ),
    RoleCode.ANALYST: frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.MEMBERSHIP_READ,
            Permission.SESSION_READ_SELF,
            Permission.SESSION_REVOKE_SELF,
            Permission.ASSET_READ,
            Permission.ASSET_CREATE,
            Permission.ASSET_UPDATE,
            Permission.ASSET_DELETE,
            Permission.EVALUATION_READ,
            Permission.EVALUATION_CREATE,
            Permission.EVALUATION_ANSWER,
            Permission.RISK_READ,
            Permission.RISK_WRITE,
            Permission.RISK_DELETE,
            Permission.DASHBOARD_READ,
            Permission.AI_READ,
            Permission.AI_GENERATE,
            Permission.REPORT_READ,
            Permission.REPORT_CREATE,
            Permission.INCIDENT_READ,
            Permission.INCIDENT_WRITE,
            Permission.NOTIFICATION_READ,
        }
    ),
    RoleCode.VIEWER: frozenset(
        {
            Permission.ORGANIZATION_READ,
            Permission.SESSION_READ_SELF,
            Permission.SESSION_REVOKE_SELF,
            Permission.ASSET_READ,
            Permission.EVALUATION_READ,
            Permission.RISK_READ,
            Permission.DASHBOARD_READ,
            Permission.AI_READ,
            Permission.REPORT_READ,
            Permission.INCIDENT_READ,
            Permission.NOTIFICATION_READ,
        }
    ),
}


def has_permission(role: RoleCode, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
