###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoiceTag(models.Model):
    _name = 'account.invoice.tag'
    _description = 'Invoice Tag'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    color = fields.Integer(
        string='Color Index',
    )
    invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        string='Invoices',
        relation='account_invoice_tag_rel',
        column1='tag_id',
        column2='invoice_id',
    )
    invoices_count = fields.Integer(
        string='# of Invoices',
        compute='_compute_invoices_count',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self._default_company(),
    )

    @api.model
    def _default_company(self):
        return self.env['res.users']._get_company()

    @api.depends('invoice_ids')
    def _compute_invoices_count(self):
        for tag in self:
            tag.invoices_count = len(tag.invoice_ids)
