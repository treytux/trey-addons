###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductPricelistItemCondition(models.Model):
    _name = 'product.pricelist.item.condition'
    _order = 'price_from, price_to'

    name = fields.Char(
        string='Empty',
    )
    pricelist_item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        string='Pricelist item',
    )
    price_from = fields.Float(
        string='Price from',
        compute='_compute_price_from',
        store=True,
    )
    price_to = fields.Float(
        string='Price to',
    )
    percent_increase = fields.Float(
        string='Percent increase/decrease',
        help='This field indicates the percentage to which the price will '
             'increase or decrease. Its value must always be positive.\n'
             'The formula used to calculate the price is:\n'
             'price * Increase/decrease percentage / 100\n'
             'If the value is greater than 100, the price will be increased '
             'by that percentage.\n'
             'If, on the other hand, the value is less than 100, the price '
             'will decrease by that percentage.\n'
             'Example:\n'
             'Let\'s say we have a product whose price is 10.\n'
             'If "Percentage increase/decrease" = 200, the final price will '
             'be: 10 * 200 / 100 = 20, that is, the price is increased to '
             '200%.\n'
             'If, on the contrary, "Percentage increase/decrease" = 50, the '
             'final price will be: 10 * 50 / 100 = 5, that is, the price has '
             'decreased to 50%.'
    )

    @api.depends('pricelist_item_id')
    def _compute_price_from(self):
        for item_condition in self:
            all_conditions = item_condition.pricelist_item_id.condition_ids
            for count, condition in enumerate(all_conditions):
                if count == 0:
                    condition.price_from = 0
                else:
                    previous_condition = all_conditions[count - 1]
                    condition.price_from = previous_condition.price_to + 0.01

    @api.constrains('price_from', 'price_to')
    def check_price_from_to(self):
        for condition in self:
            if condition.price_from >= condition.price_to:
                raise ValidationError(_(
                    'Wrong condition, \'Price from\' must be less than '
                    '\'Price to\''))

    @api.constrains('percent_increase')
    def check_percent_increase(self):
        for condition in self:
            if condition.percent_increase <= 0:
                raise ValidationError(_(
                    'Wrong condition, \'Percent increase/decrease\' must be '
                    'greater than zero.'))
