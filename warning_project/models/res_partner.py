# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields
from openerp.addons.warning.warning import WARNING_MESSAGE, WARNING_HELP


class ResPartner(models.Model):
    _inherit = 'res.partner'

    issue_warn = fields.Selection(
        selection=WARNING_MESSAGE,
        string='Project Issues',
        help=WARNING_HELP,
        default='no-message')
    issue_warn_msg = fields.Text(
        string='Message for Project Issue')
    task_warn = fields.Selection(
        selection=WARNING_MESSAGE,
        string='Project Task',
        help=WARNING_HELP,
        default='no-message')
    task_warn_msg = fields.Text(
        string='Message for Project Task')
