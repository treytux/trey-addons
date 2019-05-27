# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    users_to_inform_ids = fields.Many2many(
        comodel_name="res.users",
        string="Users whose will be informed of their the blocked partners",
        store=True)
