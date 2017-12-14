# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
from functools import partial


class ProductLabelReport(models.AbstractModel):
    _inherit = 'report.product_label.label'

    @api.multi
    def render_product_picking_label(self, docargs, data):
        model = 'stock.move'
        if data['quantity_picking'] == 'total':
            model = 'stock.pack.operation'
        docargs.update({
            'docs': self.ids,
            'doc_model': model,
            'tmpl_name': 'product_label_picking.label_picking_document',
            'getPartner': partial(self.getPartner),
            'get_price_unit': partial(self.get_price_unit),
            'quantity_picking': data['quantity_picking']})
        return docargs

    @api.model
    def getPartner(self, obj):
        picking = obj.picking_id
        partner = None
        # Si el albaran es de entrada
        if picking.picking_type_id and \
           picking.picking_type_id.code == 'incoming':
            # Obtener el cliente a traves del grupo de abastecimiento del alb
            # de entrada (si partner_id es cliente, proviene del pedido de un
            # cliente, por lo que sera bajo demanda)
            if picking.group_id and picking.group_id.partner_id and \
               picking.group_id.partner_id.customer is True:
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
