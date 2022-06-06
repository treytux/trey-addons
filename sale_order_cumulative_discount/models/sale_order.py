# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    multiple_discount = fields.Char(
        string='Disc. Applied',
    )
    discount_name = fields.Char()

    @staticmethod
    def _validate_discount(discount):
        discount_regex = re.compile(
            r'^(\s*[-+]{0,1}\s*\d+([,.]\d+)?){1}'
            r'(\s*[-+]\s*\d+([,.]\d+)?\s*)*$'
        )

        # This regex is composed of 2 parts:
        # 1) A starting number which is mandatory {1} composed of:
        #    a) \s* = any number of starting spaces
        #    b) [-+]{0,1} = an optional symbol '+' or '-'
        #    c) \s* = any number of spaces
        #    d) \d+ = a digit sequence of length at least 1
        #    e) ([,.]\d+)? = an optional decimal part, composed of a '.' or ','
        #       symbol followed by a digital sequence of length at least 1
        # 2) An optional list of other numbers each one composed of:
        #    a) \s* = any number of starting spaces
        #    b) [-+] = a mandatory '+' or '-' symbol
        #    c) \s* = any number of spaces
        #    d) \d+ = a digit sequence of length at least 1
        #    e) ([,.]\d+)? = an optional decimal part, composed of a '.' or ','
        #       symbol followed by a digital sequence of length at least 1
        #    f) \s* = any number of ending spaces

        if discount and not discount_regex.match(discount):
            return False
        return True

    def _normalize_discount(self, discount):
        discount = discount.replace(" ", "")
        discount = discount.replace(",", ".")
        if discount and discount[0] == '+':
            discount = discount[1:]
        return discount

    def get_multiple_discount(self, model_obj, multiple_discount):
        for line in model_obj:
            if multiple_discount:
                if self._validate_discount(multiple_discount):
                    normalized_discount = self._normalize_discount(
                        multiple_discount)
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
                if normalized_discount != multiple_discount:
                    line.multiple_discount = normalized_discount
            else:
                line.discount = 0

    @api.onchange('multiple_discount')
    def onchange_multiple_discount(self):
        self.get_multiple_discount(self, self.multiple_discount)

    @api.constrains('multiple_discount')
    def validate_discount(self):
        for line in self:
            if line.multiple_discount and not self._validate_discount(
                    line.multiple_discount):
                raise ValidationError(
                    _('Warning! The discount format is not recognized.'))

    @api.model
    def create(self, vals):
        line = super().create(vals)
        if 'multiple_discount' in vals:
            line.onchange_multiple_discount()
        return line

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if 'multiple_discount' in vals:
            for line in self:
                line.onchange_multiple_discount()
        return res

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        res = super()._prepare_invoice_line(qty)
        res['multiple_discount'] = self.multiple_discount
        res['discount_name'] = self.discount_name
        return res

    @api.onchange('product_id')
    def product_id_change_multiple_discount(self):
        if not self.order_id.partner_id:
            raise UserError(_('You must first select a partner.'))
        if not self.product_id:
            return {'domain': {'product_uom': []}}
        rule = self.env['product.pricelist.item']
        product_context = dict(
            self.env.context,
            partner_id=self.order_id.partner_id.id,
            date=self.order_id.date_order,
            uom=self.product_uom.id)
        final_price, rule_id = self.order_id.pricelist_id.with_context(
            product_context).get_product_price_rule(
                self.product_id, self.product_uom_qty or 1.0,
                self.order_id.partner_id)
        rules = rule.browse(rule_id)
        if rules.exists() and not rules.without_discount:
            self.multiple_discount = rules._get_item_discount()
            self.discount_name = rules._get_item_name()
