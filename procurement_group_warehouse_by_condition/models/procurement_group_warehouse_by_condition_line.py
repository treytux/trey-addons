###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProcurementGroupWarehouseByConditionLine(models.Model):
    _name = 'procurement.group.warehouse_by_condition.line'
    _description = 'Line procurement group warehouse by condition'
    _order = 'sequence'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
    )
    warehouse_by_condition_id = fields.Many2one(
        comodel_name='procurement.group.warehouse_by_condition',
        string='Warehouse by condition',
        required=True,
    )
    company_id = fields.Many2one(
        related='warehouse_by_condition_id.company_id',
        string='Company',
        store=True,
        readonly=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=1,
        required=True,
    )
    applied_on = fields.Selection(
        selection=[
            ('product_global', 'All products'),
            ('product_category', 'Product category'),
            ('product_template', 'Product template'),
            ('product_variant', 'Product variant'),
        ],
        string='Apply On',
        default='product_global',
        required=True,
        help='Condition line applicable on selected option.',
    )
    product_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Product category',
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
        domain="[('type', '=', 'product')]",
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain="[('type', '=', 'product')]",
    )
    sign = fields.Selection(
        selection=[
            ('>', '>'),
            ('>=', '>='),
            ('==', '='),
            ('<', '<'),
            ('<=', '<='),
        ],
        string='Sign',
        default='>=',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
    )
    zips = fields.Char(
        string='Zips',
        help=(
            'Zip codes by delivery address separated by comma.\n'
            'Ex: 28001, 28002'
        ),
    )
    main_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Main warehouse',
        required=True,
        domain="[('is_warehouse_by_condition', '=', False)]",
    )
    alternative_warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        string='Alternative warehouses',
        relation='warehouse_by_condition_alternative_warehouse_rel',
        column1='warehouse_by_condition_id',
        column2='alternative_warehouse_id',
        domain="[('is_warehouse_by_condition', '=', False)]",
    )

    @api.depends(
        'applied_on', 'product_category_id', 'product_tmpl_id', 'product_id')
    def _compute_name(self):
        for line in self:
            is_line_category = (
                line.applied_on == 'product_category'
                and line.product_category_id)
            is_line_product_tmpl = (
                line.applied_on == 'product_template'
                and line.product_tmpl_id)
            is_line_product_variant = (
                line.applied_on == 'product_variant'
                and line.product_id)
            if is_line_category:
                name = _('Category: %s') % (
                    line.product_category_id.display_name)
            elif is_line_product_tmpl:
                name = _(
                    'Product template: %s') % line.product_tmpl_id.display_name
            elif is_line_product_variant:
                name = _('Product variant: %s') % line.product_id.display_name
            else:
                name = _('All products')
            line.name = name

    @api.constrains('zips')
    def _check_zips(self):
        for line in self:
            if not line.zips:
                continue
            zips = line.zips.replace(' ', '')
            if not re.match(r'^[\d,]+$', zips):
                raise ValidationError(_(
                    'Zips must contain only numbers and commas.'))
            if ',,' in zips:
                raise ValidationError(_(
                    'Zips cannot contain consecutive commas.'))
            if zips.startswith(',') or zips.endswith(','):
                raise ValidationError(_(
                    'Zips cannot start or end with a comma.'))

    @api.constrains('main_warehouse_id', 'alternative_warehouse_ids')
    def _check_alternative_warehouse_ids(self):
        for line in self:
            if not line.alternative_warehouse_ids:
                continue
            for alternative_warehouse in line.alternative_warehouse_ids:
                if alternative_warehouse == line.main_warehouse_id:
                    raise ValidationError(_(
                        'You cannot add the warehouse defined as the main '
                        'warehouse to the same condition line as an '
                        'alternative warehouse. Select a different '
                        'warehouse(s).'))

    @api.constrains(
        'applied_on', 'product_category_id', 'product_tmpl_id', 'product_id')
    def _check_applied_on_fields(self):
        for line in self:
            if not line.applied_on:
                continue
            if (
                    line.applied_on == 'product_global'
                    and (
                        line.product_category_id or line.product_tmpl_id
                        or line.product_id
                    )
            ):
                raise ValidationError(_(
                    'If you select "Apply to all products" you must leave the '
                    '"Product category", "Product template" and "Product '
                    'variant" fields empty.'))
            if (
                line.applied_on == 'product_category'
                and (line.product_tmpl_id or line.product_id)
            ):
                raise ValidationError(_(
                    'If you select "Apply to product category" you must leave '
                    'the "Product template" and "Product variant" fields '
                    'empty.'))
            if (
                    line.applied_on == 'product_category'
                    and not line.product_category_id):

                raise ValidationError(_(
                    'If you select "Apply to product category" you must fill '
                    'the "Product category" field.'))
            if (
                line.applied_on == 'product_template'
                and (line.product_category_id or line.product_id)
            ):
                raise ValidationError(_(
                    'If you select "Apply to product template" you must leave '
                    'the "Product category" and "Product variant" fields '
                    'empty.'))
            if (
                    line.applied_on == 'product_template'
                    and not line.product_tmpl_id):
                raise ValidationError(_(
                    'If you select "Apply to product template" you must fill '
                    'the "Product template" field.'))
            if (
                line.applied_on == 'product_variant'
                and (line.product_category_id or line.product_tmpl_id)
            ):
                raise ValidationError(_(
                    'If you select "Apply to product variant" you must leave '
                    'the "Product category" and "Product template" fields '
                    'empty.'))
            if line.applied_on == 'product_variant' and not line.product_id:
                raise ValidationError(_(
                    'If you select "Apply to product variant" you must fill '
                    'the "Product variant" field.'))
