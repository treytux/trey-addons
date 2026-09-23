###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class ContractLine(models.Model):
    _inherit = 'contract.line'

    @api.constrains(
        'date_start', 'date_end', 'last_date_invoiced', 'recurring_next_date')
    def _check_last_date_invoiced(self):
        if self.env.context.get('skip_date_start_last_date_invoiced_check'):
            for rec in self.filtered('last_date_invoiced'):
                if rec.date_end and rec.date_end < rec.last_date_invoiced:
                    raise ValidationError(_(
                        'You can\'t have the end date before the date '
                        'of last invoice for the contract line \'%s\'')
                        % rec.name)
                if (
                    rec.recurring_next_date
                    and rec.recurring_next_date <= rec.last_date_invoiced
                ):
                    raise ValidationError(_(
                        'You can\'t have the next invoice date before '
                        'the date of last invoice for the contract line '
                        '\'%s\'') % rec.name)
            return
        return super()._check_last_date_invoiced()
