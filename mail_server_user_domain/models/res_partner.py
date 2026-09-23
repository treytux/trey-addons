###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _notify_prepare_template_context(
            self, message, record, model_description=False,
            mail_auto_delete=True):
        res = super()._notify_prepare_template_context(
            message, record, model_description, mail_auto_delete)
        domain_email_from = (
            '@' in message.email_from and message.email_from.split('@')[-1:]
            or False)
        if domain_email_from:
            company = self.env['res.company'].search([
                ('email', 'ilike', domain_email_from),
            ], limit=1)
            if company:
                res['company'] = company
        return res
