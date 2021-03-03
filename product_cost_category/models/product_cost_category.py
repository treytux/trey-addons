###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCostCategory(models.Model):
    _name = 'product.cost.category'
    _description = 'Product Cost Category'
    _order = 'date_end desc, date_start asc, name'

    name = fields.Char(
        string='Name',
        translate=True,
        required=True,
        index=True,
    )
    date_start = fields.Date(
        string='From Date',
        required=True,
        default=fields.Date.today(),
        index=True,
    )
    date_end = fields.Date(
        string='To Date',
        required=True,
        default=fields.Date.today(),
        index=True,
    )
    item_ids = fields.One2many(
        comodel_name='product.cost.category.item',
        inverse_name='category_id',
        string='Lines',
        copy=True,
        auto_join=True,
    )
    description = fields.Text(
        string='Description',
    )

    @api.constrains('date_start', 'date_end')
    def check_category_overload_date(self):
        for category in self:
            overlap = self.env['product.cost.category'].search([
                ('date_start', '>=', category.date_start),
                ('date_end', '<=', category.date_end)], limit=1)
            if not overlap or overlap.id == category.id:
                continue
            raise ValidationError(_(
                'Cost Category OverLap with: %s' % overlap.name))
