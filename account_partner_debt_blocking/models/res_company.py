# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    users_to_inform_ids = fields.Many2many(
        comodel_name="res.users",
        string="Users to inform")
