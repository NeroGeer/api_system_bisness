from sqladmin import ModelView
from sqladmin.filters import ForeignKeyFilter

from src.models.model_meeting import Meeting, MeetingParticipant
from src.models.model_team import Team
from src.models.model_user import User


class MeetingAdmin(ModelView, model=Meeting):
    name = "Meeting"
    name_plural = "Meetings"

    column_list = [
        Meeting.id,
        Meeting.title,
        Meeting.team_id,
        Meeting.creator,
        Meeting.start_time,
        Meeting.end_time,
    ]

    column_searchable_list = [
        Meeting.title,
        Meeting.description,
        Meeting.start_time,
    ]

    column_filters = [
        ForeignKeyFilter(Meeting.team_id, Team.name),
    ]

    def column_format(self, model, name):
        if name == "creator" and model.creator:
            return model.creator.email


class MeetingParticipantAdmin(ModelView, model=MeetingParticipant):
    name = "Meeting Participant"
    name_plural = "Meeting Participants"

    column_list = [
        MeetingParticipant.id,
        MeetingParticipant.meeting,
        MeetingParticipant.user,
    ]

    column_filters = [
        ForeignKeyFilter(MeetingParticipant.user_id, User.email),
        ForeignKeyFilter(MeetingParticipant.meeting_id, Meeting.id),
    ]

    def column_format(self, model, name):
        if name == "user":
            return model.user.email

        if name == "meeting":
            return model.meeting.title
