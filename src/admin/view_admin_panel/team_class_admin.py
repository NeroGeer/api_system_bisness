from sqladmin import ModelView
from sqladmin.filters import ForeignKeyFilter
from src.models.model_team import Team, TeamMember
from src.models.model_user import User


class TeamAdmin(ModelView, model=Team):
    name = "Team"
    name_plural = "Teams"

    column_list = [
        Team.id,
        Team.name,
        Team.invite_code,
    ]

    column_searchable_list = [
        Team.name,
        Team.invite_code,
    ]


class TeamMemberAdmin(ModelView, model=TeamMember):
    name = "Team Member"
    name_plural = "Team Members"

    column_list = [
        TeamMember.id,
        TeamMember.user,
        TeamMember.team,
        TeamMember.role,
    ]

    column_searchable_list = [
        TeamMember.role,
    ]

    column_filters = [
        ForeignKeyFilter(TeamMember.team_id, Team.name),
        ForeignKeyFilter(TeamMember.user_id, User.email),
    ]

    def column_format(self, model, name):
        if name == "user":
            return model.user.email
        if name == "team":
            return model.team.name
