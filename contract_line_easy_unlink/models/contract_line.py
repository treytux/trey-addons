###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    def stop(self, date_end, manual_renew_needed=False, post_message=True):
        for record in self:
            record.cancel()
        return True

    def cancel(self):
        for contract in self.mapped('contract_id'):
            lines = self.filtered(
                lambda line, c=contract: line.contract_id == c)
            msg = _(
                'Contract line canceled: %s',
                '<br/>- '.join([
                    '<strong>%(product)s</strong>' % {'product': name}
                    for name in lines.mapped('name')
                ])
            )
            contract.message_post(body=msg)
        self.mapped('predecessor_contract_line_id').write(
            {'successor_contract_line_id': False}
        )
        return self.write({'is_canceled': True, 'is_auto_renew': False})

    def unlink(self):
        for record in self:
            record.cancel()
        return super().unlink()
