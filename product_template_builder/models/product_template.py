###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_template_builder_id = fields.Many2one(
        comodel_name='product.template.builder',
        string='Product Template',
    )

    @api.onchange('product_template_builder_id')
    def onchange_product_template_builder_id(self):
        if not self.product_template_builder_id:
            return
        template = self.product_template_builder_id.with_context(
            lang=self.company_id.partner_id.lang)
        if template.image_medium:
            self.image_medium = template.image_medium
        if template.description_sale:
            self.description_sale = template.description_sale
        if template.website_description:
            self.website_description = template.website_description
        self.sale_ok = template.sale_ok
        self.purchase_ok = template.purchase_ok
        self.type = template.type
        self.categ_id = template.categ_id.id
        self.uom_id = template.uom_id.id
        self.taxes_id = template.taxes_id.ids
        self.route_ids = template.route_ids.ids
