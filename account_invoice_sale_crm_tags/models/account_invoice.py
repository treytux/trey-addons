###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    crm_tag_ids = fields.Many2many(
        string='CRM Tags',
        comodel_name='crm.lead.tag',
        relation='invoice2crm_tag_rel',
        column1='invoice_id',
        column2='tag_id',
    )
