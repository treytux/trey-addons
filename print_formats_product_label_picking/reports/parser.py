# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
from functools import partial


class ProductLabelReport(models.AbstractModel):
    _inherit = 'report.print_formats_product_label.label'

    @api.model
    def get_partner(self, obj):
        picking = obj.picking_id
        partner = None
        if (picking.picking_type_id and
                picking.picking_type_id.code == 'incoming'):
            if (picking.group_id and picking.group_id.partner_id and
                    picking.group_id.partner_id.customer is True):
                partner = picking.group_id.partner_id
        return partner

    @api.multi
    def get_price_unit(self, obj):
        if obj._name == 'stock.pack.operation':
            price_unit = (
                obj.linked_move_operation_ids and
                obj.linked_move_operation_ids[0] and
                obj.linked_move_operation_ids[0].move_id and
                obj.linked_move_operation_ids[0].move_id.price_unit or 0)
        else:
            price_unit = obj.price_unit
        return price_unit

    @api.model
    def get_variant_name(self, product):
        return '%s %s' % (
            product.name,
            '-'.join([v.name for v in product.attribute_value_ids]))

    @api.multi
    def render_product_picking_label(self, docargs, data):
        model = 'stock.move'
        if data['picking_quantity'] == 'total':
            model = 'stock.pack.operation'
        docargs.update({
            'docs': self.ids,
            'doc_model': model,
            'tmpl_name': (
                'print_formats_product_label_picking.label_picking_document'),
            'get_partner': partial(self.get_partner),
            'get_price_unit': partial(self.get_price_unit),
            'get_variant_name': partial(self.get_variant_name),
            'picking_quantity': data['picking_quantity']})
        return docargs
