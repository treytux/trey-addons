# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    project_template_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Project Template",
        required=False)
    issue_sale_type_id = fields.Many2one(
        comodel_name="sale.order.type",
        string="Issue Sale Type",
        required=False)
    project_sale_type_id = fields.Many2one(
        comodel_name="sale.order.type",
        string="Project Sale Type",
        required=False)
