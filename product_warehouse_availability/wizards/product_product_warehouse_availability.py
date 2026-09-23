# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models
import openerp.addons.decimal_precision as dp


class ProductProductWarehouseAvailability(models.TransientModel):
    _name = 'product.product.warehouse.availability'
    _description = 'Product warehouse availability'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template',
        required=True,
    )
    qty_available = fields.Float(
        string='Quantity On Hand',
        digits_compute=dp.get_precision('Product Unit of Measure'),
    )
    qty_virtual = fields.Float(
        digits_compute=dp.get_precision('Product Unit of Measure'),
        string='Forecast Quantity',
    )
    qty_incoming = fields.Float(
        digits_compute=dp.get_precision('Product Unit of Measure'),
        string='Incoming',
    )
    qty_outgoing = fields.Float(
        digits_compute=dp.get_precision('Product Unit of Measure'),
        string='Outgoing',
    )

    def product_availability(self, template=None, product=None, company=None):
        def create_product_availability(tmp_product):
            warehouses = self.env['stock.warehouse'].search([
                ('company_id', '=', company.id),
            ])
            for warehouse in warehouses:
                ctx = self.env.context.copy()
                ctx['force_company'] = company.id
                parent_locations = warehouse.view_location_id.mapped(
                    'child_ids').filtered(lambda l: not l.not_availability)
                for location in parent_locations:
                    locations = self.env['stock.location'].search([
                        ('parent_left', '>=', location.parent_left),
                        ('parent_left', '<', location.parent_right),
                        ('not_availability', '=', False),
                    ])
                    ctx['location'] = locations.ids
                    ctx['compute_child'] = False
                    res = tmp_product.with_context(ctx)._product_available()
                    data = {
                        'qty_available': res[tmp_product.id][
                            'qty_available'],
                        'qty_virtual': res[tmp_product.id][
                            'virtual_available'],
                        'qty_incoming': res[tmp_product.id][
                            'incoming_qty'],
                        'qty_outgoing': res[tmp_product.id][
                            'outgoing_qty'],
                    }
                    product_template_id = tmp_product.product_tmpl_id.id
                    availability = self.env['%s' % self._model].search([
                        ('company_id', '=', company.id),
                        ('warehouse_id', '=', warehouse.id),
                        ('location_id', '=', location.id),
                        ('product_id', '=', tmp_product.id),
                        ('product_tmpl_id', '=', product_template_id),
                    ])
                    if availability:
                        availability.write(data)
                        data.clear()
                        continue
                    data['company_id'] = company.id
                    data['warehouse_id'] = warehouse.id
                    data['location_id'] = location.id
                    data['product_id'] = tmp_product.id
                    data['product_tmpl_id'] = product_template_id
                    self.create(data)
                    data.clear()
        if template:
            for variant in template.product_variant_ids:
                create_product_availability(variant)
        elif product and not template:
            create_product_availability(product)
