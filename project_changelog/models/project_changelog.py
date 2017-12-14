# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProjectChangelog(models.Model):
    _name = 'project.changelog'
    _order = "version desc, date_item desc"

    name = fields.Char(
        string='Name')
    version = fields.Char(
        string='Version')
    description = fields.Text(
        string='Description')
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        ondelete='cascade')
    date_item = fields.Datetime(
        string='Date item',
        default=fields.Datetime.now())
    item_type = fields.Selection(
        selection=[
            ('added', 'Added'),
            ('changed', 'Changed'),
            ('deprecated', 'Deprecated'),
            ('removed', 'Removed'),
            ('fixed', 'Fixed'),
            ('security', 'Security')
        ],
        string='Type',
        help='Added for new features. '
             'Changed for changes in existing functionality. '
             'Deprecated for once-stable features removed in upcoming '
             ' releases. '
             'Removed for deprecated features removed in this release. '
             'Fixed for any bug fixes. '
             'Security to invite users to upgrade in case of vulnerabilities.')
