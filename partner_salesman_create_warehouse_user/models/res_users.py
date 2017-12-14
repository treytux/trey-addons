# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_id = fields.Many2one(
        string='Warehouse',
        comodel_name='stock.warehouse',
        help="You can choose an existent warehouse or create a new from "
        "'More/Create warehouse' menu.")
    partner_is_salesman = fields.Boolean(
        string='Partner is salesman',
        related="partner_id.is_salesman")
