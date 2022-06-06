###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import _, api, exceptions, fields, models


class ResPartnerGlobalDiscount(models.Model):
    _name = 'res.partner.global_discount'
    _description = 'Global discounts'

    name = fields.Char(
        string='Name',
    )
    percent = fields.Char(
        string='Percent',
    )
    total_percent = fields.Float(
        string='Total percent',
        compute='_compute_total_percent',
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='res_partner_global_discount2res_partner_rel',
        column1='discount_id',
        column2='partner_id',
    )
    partner_count = fields.Integer(
        string='Partner count',
        compute='_compute_partner_count',
    )

    @staticmethod
    def _validate_discount(discount):
        discount_regex = re.compile(
            r'^(\s*[-+]{0,1}\s*\d+([,.]\d+)?){1}'
            r'(\s*[-+]\s*\d+([,.]\d+)?\s*)*$'
        )
        if discount and not discount_regex.match(discount):
            return False
        return True

    @api.constrains('percent')
    def validate_discount(self):
        for discount in self:
            if not discount.percent:
                continue
            if not self._validate_discount(discount.percent):
                raise exceptions.ValidationError(
                    _('Warning! The discount format is not recognized.'))

    def action_partner_view(self):
        if not self.partner_ids:
            return {'type': 'ir.actions.act_window_close'}
        action = self.env.ref('contacts.action_contacts').read()[0]
        action['context'] = {
            'search_default_global_discount_ids': self.id,
        }
        return action

    @api.depends('partner_ids')
    def _compute_partner_count(self):
        for discount in self:
            discount.partner_count = len(discount.partner_ids)

    @api.depends('percent')
    def _compute_total_percent(self):
        def _normalize_discount(discount):
            discount = discount.replace(' ', '')
            discount = discount.replace(',', '.')
            if discount and discount[0] == '+':
                discount = discount[1:]
            return discount

        for discount in self:
            normalized_discount = _normalize_discount(discount.percent)
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
            discount.total_percent = round(total_discount * 100, 2)
