###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api, fields


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    is_fsdd = fields.Boolean(
        string='Anticipos de crédito (FSDD)',
        states={
            'draft': [('readonly', False)],
            'open': [('readonly', False)]})

    @api.model
    def _prepare_field(self, field_name, field_value, eval_ctx,
                       max_size=0, gen_args=None):
        res = super()._prepare_field(
            field_name, field_value, eval_ctx, max_size, gen_args)
        if field_name == 'Message Identification' and self.is_fsdd:
            res = 'FSDD%s' % res
        return res

    @api.multi
    def finalize_sepa_file_creation(self, xml_root, gen_args):
        if self.is_fsdd:
            gen_args['file_prefix'] = 'fsdd_'
        return super().finalize_sepa_file_creation(xml_root, gen_args)
