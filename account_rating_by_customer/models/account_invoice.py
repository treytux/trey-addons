###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'rating.mixin']

    rating_ids = fields.One2many(
        comodel_name='rating.rating',
        inverse_name='invoice_id',
        domain=[('res_model', '=', 'account.invoice')],
        string='Ratings',
    )

    def send_satisfaction_survey(self):
        template = self.env.ref(
            'account_rating_by_customer.mail_template_invoice_survey')
        for invoice in self:
            template.with_context(
                invoice_id=invoice.id).send_mail(invoice.id, force_send=True)
