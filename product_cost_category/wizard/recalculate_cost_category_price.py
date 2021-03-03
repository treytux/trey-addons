###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, fields, models
from odoo.tools import float_compare, float_is_zero


class RecalculateCostCategoryPrice(models.TransientModel):
    _name = 'recalculate.cost.category.price'
    _description = 'Recalculate Cost Category Price'

    category_id = fields.Many2one(
        comodel_name='product.cost.category',
        string='Category',
    )
    log = fields.Text(
        string='Log',
    )
    state = fields.Selection(
        string='State',
        selection=[('step1', 'Step1'),
                   ('step2', 'Step2'),
                   ('done', 'Done')],
        required=True,
        default='step1')

    def recalculate_cost_category_price(self):
        self.ensure_one()
        active_ids = self.env.context['active_ids']
        if not active_ids:
            return
        active_model = self.env.context.get('active_model', False)
        if active_model == 'product.template':
            templates = self.env['product.template'].browse(active_ids)
            [self.compute_price(template=template) for template in templates]
        self.write({'state': 'step2'})
        self._reopen_view()

    def compute_price(self, template=None):
        if not template:
            return
        update_type = self.env['ir.config_parameter'].sudo().get_param(
            key='product_cost_category.cost_category_price_setting',
            default='manual')
        if update_type != 'manual':
            raise exceptions.Warning(_('Please Select Manual mode to Update'))
        if not self.category_id:
            category_id = self.env['product.cost.category'].search([
                ('date_start', '<=', fields.Date.today()),
                ('date_end', '>=', fields.Date.today())], limit=1)
        else:
            category_id = self.category_id
        if not category_id:
            raise exceptions.Warning(_('Product Cost Category not found'))
        rounding = self.env.user.company_id.currency_id.rounding
        log = ''
        if len(template.product_variant_ids) <= 1:
            if float_is_zero(
                    template.standard_price, precision_rounding=rounding):
                return False
            category_item = category_id.mapped('item_ids').filtered(
                lambda i:
                i.from_standard_price
                <= template.standard_price
                <= i.to_standard_price)
            if not category_item:
                return
            template.cost_category_price = eval(
                category_item.formula.replace(
                    'standard_price', str(template.standard_price)))
            log = _('Update cost category price template: %s\n' %
                    template.name)
        else:
            for variant in template.product_variant_ids:
                if float_is_zero(
                        variant.standard_price, precision_rounding=rounding):
                    variant.cost_category_price = template.cost_category_price
                    log += _('Cost Variant: %s is Zero\n' % variant.name)
                    continue
                if float_compare(variant.standard_price,
                                 template.standard_price,
                                 precision_rounding=rounding) == 0:
                    variant.cost_category_price = template.cost_category_price
                    log += _(
                        'Cost Variant: %s is Equal Template\n' % variant.name)
                    continue
                variant_cost_category_item = category_id.mapped(
                    'item_ids').filtered(
                    lambda i:
                    i.from_standard_price
                    <= variant.standard_price
                    <= i.to_standard_price)
                if not variant_cost_category_item:
                    continue
                variant.cost_category_price = eval(
                    variant_cost_category_item.formula.replace(
                        'standard_price', str(variant.standard_price)))
                log += _('Update Variant: %s\n' % variant.name)
        self.log = log
