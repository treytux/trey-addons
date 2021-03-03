###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ContractAbstractContractLine(models.AbstractModel):
    _inherit = 'contract.abstract.contract.line'

    multiple_discount = fields.Char(
        string='Disc. Applied',
    )
    discount_name = fields.Char(
        string='Discount Name',
    )
    discount = fields.Float(
        compute='_compute_discount',
    )

    @api.multi
    @api.depends('multiple_discount')
    def _compute_discount(self):
        def _normalize_discount(discount):
            discount = discount.replace(' ', '')
            discount = discount.replace(',', '.')
            if discount and discount[0] == '+':
                discount = discount[1:]
            return discount

        for line in self:
            if not line.multiple_discount:
                line.discount = 0
                continue
            if self._validate_discount(line.multiple_discount):
                normalized_discount = _normalize_discount(
                    line.multiple_discount)
            else:
                line.discount = 0
                raise UserError(
                    _('Warning! The discount format is not recognized.'))
            tokens = re.split(r'([+-])', normalized_discount)
            numeric_tokens = []
            last_sign = 1
            for token in tokens:
                if not token:
                    continue
                if token == '-':
                    last_sign = -1
                elif token == '+':
                    last_sign = 1
                else:
                    numeric_tokens.append(float(token) * last_sign)
            marginal_discount = 1
            for token in numeric_tokens:
                marginal_discount = marginal_discount * (1 - (token / 100))
            total_discount = 1 - marginal_discount
            line.discount = total_discount * 100
            if normalized_discount != line.multiple_discount:
                line.multiple_discount = normalized_discount

    @staticmethod
    def _validate_discount(discount):
        discount_regex = re.compile(
            r'^(\s*[-+]{0,1}\s*\d+([,.]\d+)?){1}'
            r'(\s*[-+]\s*\d+([,.]\d+)?\s*)*$'
        )
        if discount and not discount_regex.match(discount):
            return False
        return True

    @api.constrains('multiple_discount')
    def validate_discount(self):
        for line in self:
            if line.multiple_discount and not self._validate_discount(
                    line.multiple_discount):
                raise ValidationError(
                    _('Warning! The discount format is not recognized.'))
