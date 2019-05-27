###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_report_group_by = fields.Selection(
        selection=[
            ('order', 'Order'),
            ('picking', 'Picking')],
        string='Invoice Report Group By')
