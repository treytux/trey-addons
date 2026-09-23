###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields, models, tools

_log = logging.getLogger(__name__)


class ProjectUpdateProgressReport(models.Model):
    _name = 'project.update.progress.report'
    _description = 'Project update progress report'
    _order = 'name desc, project_id'
    _auto = False

    def _get_selection_values_for_status(self):
        return self.env['project.update']._fields['status'].selection

    name = fields.Char(
        string='Progress name',
        readonly=True,
    )
    date = fields.Date(
        string='Progress date',
        readonly=True,
    )
    progress = fields.Integer(
        string='Progress',
        readonly=True,
        group_operator='max',
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        readonly=True,
    )
    status = fields.Selection(
        selection='_get_selection_values_for_status',
        string='Progress status',
        readonly=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Progress autor',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    date_start = fields.Date(
        string='Project date start',
        readonly=True,
    )
    date_end = fields.Date(
        string='Project date end',
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        readonly=True,
    )
    stage_id = fields.Many2one(
        comodel_name='project.project.stage',
        string='Project stage',
        readonly=True,
    )
    project_manager_id = fields.Many2one(
        comodel_name='res.users',
        string='Project Manager',
        readonly=True,
    )
    allow_billable = fields.Boolean(
        string='Billable',
        readonly=True,
    )

    def _select(self):
        return '''
            u.id,
            u.name,
            u.date,
            u.progress,
            u.project_id,
            u.status,
            u.user_id,
            p.company_id,
            p.date_start,
            p.date AS date_end,
            p.partner_id,
            p.stage_id,
            p.user_id AS project_manager_id,
            p.allow_billable
        '''

    def _group_by(self):
        return '''
            u.id,
            u.name,
            u.date,
            u.progress,
            u.project_id,
            u.status,
            u.user_id,
            p.company_id,
            p.date_start,
            p.date,
            p.partner_id,
            p.stage_id,
            p.user_id,
            p.allow_billable
        '''

    def _from(self):
        return '''
            project_update AS u
            LEFT JOIN project_project AS p ON p.id = u.project_id
        '''

    def _where(self):
        return '''
            p.is_template IS NOT TRUE
        '''

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        sql = f'''
            CREATE VIEW {self._table} AS (
                SELECT {self._select()}
                FROM {self._from()}
                WHERE {self._where()}
                GROUP BY {self._group_by()}
            )
        '''
        try:
            self._cr.execute(sql)
        except Exception as error:
            _log.critical(f'The SQL: "{sql}" failed with error: {error}')
            raise error
