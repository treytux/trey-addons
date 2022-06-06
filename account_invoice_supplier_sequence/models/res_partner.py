###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_supplier_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Invoice sequence',
        company_dependent=True,
        help='This sequence is used only for new supplier invoices',
    )
