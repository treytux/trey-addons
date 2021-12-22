###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    project_template_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Project Template',
    )
    issue_sale_type_id = fields.Many2one(
        comodel_name='sale.order.type',
        string='Issue Sale Type',
    )
    project_sale_type_id = fields.Many2one(
        comodel_name='sale.order.type',
        string='Project Sale Type',
    )
