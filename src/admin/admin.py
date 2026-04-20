from src.admin.view_admin_panel.meeting_class_admin import (
    MeetingAdmin,
    MeetingParticipantAdmin,
)
from src.admin.view_admin_panel.task_class_admin import TaskAdmin, TaskCommentAdmin
from src.admin.view_admin_panel.team_class_admin import TeamAdmin, TeamMemberAdmin
from src.admin.view_admin_panel.user_class_admin import (
    PermissionAdmin,
    RoleAdmin,
    UserAdmin,
)


def setup_admin(admin):
    admin.add_view(UserAdmin)
    admin.add_view(RoleAdmin)
    admin.add_view(PermissionAdmin)

    admin.add_view(TeamAdmin)
    admin.add_view(TeamMemberAdmin)

    admin.add_view(MeetingAdmin)
    admin.add_view(MeetingParticipantAdmin)

    admin.add_view(TaskAdmin)
    admin.add_view(TaskCommentAdmin)
