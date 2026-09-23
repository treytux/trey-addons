###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def create_exception_activity_analytic(self):
        activity_type = self.env.ref('mail.mail_activity_data_warning')
        self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('account.move'),
            'res_id': self.id,
            'activity_type_id': activity_type.id,
            'summary': _('Exception: missing analytical account'),
            'note': _('''One or more lines on this invoice do not have
            an analytical account assigned.'''),
            'user_id': self.invoice_user_id.id,
        })

    def _exception_activity_analytic_move_types(self):
        return [
            'out_invoice',
            'out_refund',
            'in_invoice',
            'in_refund',
        ]

    def action_post(self):
        res = super().action_post()
        move_types = self._exception_activity_analytic_move_types()
        block = self.env['ir.config_parameter'].sudo().get_param(
            'account_analytic_exception.block_missing_analytic')
        for move in self:
            if move.move_type not in move_types:
                continue
            missing_analytic = move.invoice_line_ids.filtered(
                lambda line: line.display_type == 'product'
                and not line.analytic_line_ids
                and not line.analytic_distribution
            )
            if missing_analytic:
                if block:
                    raise exceptions.UserError(
                        _('This invoice cannot be validated: there are'
                          ' lines without analytic account/distribution.'))
                move.create_exception_activity_analytic()
        return res
