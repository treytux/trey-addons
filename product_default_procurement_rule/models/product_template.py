# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        if res.type != 'product':
            return res
        if res.company_id:
            company = res.company_id
            if not company.is_reordering_default:
                return res
            self.env['stock.warehouse.orderpoint'].create({
                'name': '-default- %s' % res.name,
                'product_id': res.product_variant_ids[0].id,
                'warehouse_id': company.default_warehouse_id.id,
                'location_id': company.default_location_id.id,
                'product_min_qty': company.default_product_min_qty,
                'product_max_qty': company.default_product_max_qty,
                'qty_multiple': company.default_qty_multiple,
                'company_id': company.id})
        else:
            for company in self.env['res.company'].sudo().search([]):
                if not company.is_reordering_default:
                    continue
                self.env['stock.warehouse.orderpoint'].sudo().create({
                    'name': '-default- %s' % res.name,
                    'product_id': res.product_variant_ids[0].id,
                    'warehouse_id': company.default_warehouse_id.id,
                    'location_id': company.default_location_id.id,
                    'product_min_qty': company.default_product_min_qty,
                    'product_max_qty': company.default_product_max_qty,
                    'qty_multiple': company.default_qty_multiple,
                    'company_id': company.id})
        return res
