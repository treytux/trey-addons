###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import html_translate


class ProductTemplateBuilder(models.Model):
    _name = 'product.template.builder'
    _description = 'Product Template'

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id

    name = fields.Char(
        string='Product Template',
        required=True,
    )
    image_medium = fields.Binary(
        string='Medium-sized image',
        attachment=True,
    )
    sale_ok = fields.Boolean(
        string='Can be Sold',
        default=True,
    )
    purchase_ok = fields.Boolean(
        string='Can be Purchased',
        default=True,
    )
    type = fields.Selection(
        selection=[
            ('consu', 'Consumable'),
            ('service', 'Service'),
            ('product', 'Product'),
        ],
        string='Product Type',
    )
    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        default=_get_default_uom_id,
        required=True,
    )
    taxes_id = fields.Many2many(
        comodel_name='account.tax',
        relation='product_builder_tax_rel',
        column1='product_template_builder_id',
        column2='tax_id',
        string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale')],
    )
    route_ids = fields.Many2many(
        comodel_name='stock.location.route',
        relation='product_builder_route_rel',
        column1='product_template_builder_id',
        column2='route_id',
        string='Routes',
        domain=[('product_selectable', '=', True)],
    )
    description_sale = fields.Text(
        string='Sale Description',
        translate=True,
    )
    website_description = fields.Html(
        string='Description for the website',
        sanitize_attributes=False,
        translate=html_translate,
    )
    active = fields.Boolean(
        default=True,
        help='''If unchecked, it will allow you to hide the
        product template without removing it.''',
    )

    def write(self, vals):
        if 'active' in vals and not vals.get('active'):
            template_id = self.env['ir.default'].get(
                'product.template', 'product_template_builder_id')
            for template in self:
                if template_id and template_id == template.id:
                    raise UserError(_(
                        '''Before archiving "%s" please select another default
                        template in the settings.''') % template.name)
        return super(ProductTemplateBuilder, self).write(vals)
