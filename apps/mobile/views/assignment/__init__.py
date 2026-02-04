# Import des vues d'assignment
from .status_view import AssignmentStatusView
from .close_job_view import CloseJobView
from .block_view import BlockAssignmentView
from .unblock_view import UnblockAssignmentView

__all__ = [
    'AssignmentStatusView',
    'CloseJobView',
    'BlockAssignmentView',
    'UnblockAssignmentView'
]
