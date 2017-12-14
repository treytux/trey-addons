# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, exceptions, _
import logging
_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def button_cancel_extend(self):
        '''Allow cancel a sales order although has associated a transfer
        picking, creating a reverse picking to return all goods.'''
        if len(self.picking_ids) == 0:
            return True
        # Si el pedido tiene algun albaran de entrada, pasa al siguiente pedido
        # (porque de salida e interno tendra)
        for picking in self.picking_ids:
            if picking.picking_type_id.code == 'incoming':
                break
        for picking in self.picking_ids:
            if picking.state == 'cancel':
                continue
            elif picking.state in ('draft', 'waiting', 'confirmed',
                                   'partially_available', 'assigned'):
                picking.action_cancel()
            elif picking.state == 'done':
                # Revertir transferencia creando un nuevo albaran y modificando
                # sus movimientos para que vayan en sentido contrario
                ret_picktype = picking.picking_type_id.return_picking_type_id
                wh_id = ret_picktype.warehouse_id.id
                if ret_picktype and ret_picktype.code == 'incoming':
                    pickings_type_ret = self.env['stock.picking.type'].search([
                        ('code', '=', 'incoming'),
                        ('warehouse_id', '=', wh_id)])
                elif not ret_picktype.exists():
                    pickings_type_ret = picking.picking_type_id
                data = {'picking_type_id': pickings_type_ret[0].id}
                reverse_picking = picking.copy(data)
                for move in reverse_picking.move_lines:
                    reverse_loc_dst_id = move.location_id.id
                    reverse_loc_src_id = move.location_dest_id.id
                    move.write({'location_id': reverse_loc_src_id})
                    move.write({'location_dest_id': reverse_loc_dst_id})
                # Marcar como 'Por hacer'
                # Pasamos en el contexto el parametro 'no_apply_rules' para que
                # se salte las reglas pull
                reverse_picking.with_context(
                    no_apply_rules=True).action_confirm()
                # Forzar disponibilidad (porque haya o no stock disponible, hay
                # que devolver la mercancia)
                reverse_picking.force_assign()
                # Transferir
                if not self.env.context:
                    context = {}
                else:
                    context = self.env.context.copy()
                context.update({
                    'active_model': 'stock.picking',
                    'active_ids': [reverse_picking[0].id],
                    'active_id': (len(reverse_picking) and
                                  reverse_picking[0].id or False)})
                reverse_picking_id = (
                    len(reverse_picking) and reverse_picking[0].id or False)
                transfer_detail = self.env[
                    'stock.transfer_details'].with_context(
                        context).create({'picking_id': reverse_picking_id})
                # Aplicar
                transfer_detail.do_detailed_transfer()
                # Relacionar ambos albaranes
                picking.write({'reverse_picking_id': reverse_picking.id})
                reverse_picking.write({'reverse_picking_id': picking.id})

    @api.one
    def action_cancel(self):
        '''Inherit the function to cancel the picking/s first.'''
        self.button_cancel_extend()
        return super(SaleOrder, self).action_cancel()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def button_cancel(self):
        '''Override function to allow cancel a sales order line when the state
        of move is 'done' if it has completely returned the goods.'''
        lines = self
        for line in lines:
            if line.invoiced:
                raise exceptions.Warning(_(
                    'You cannot cancel a sale order line that has already '
                    'been invoiced.'))
        procurements = self.env['procurement.order'].browse(
            sum([l.procurement_ids.ids for l in lines], []))
        procurements.cancel()
        for procurement in lines.mapped('procurement_ids'):
            for move in procurement.move_ids:
                if (move.state == 'done' and not move.scrapped) and (
                        not move.picking_id.reverse_picking_id.exists()):
                    raise exceptions.Warning(_(
                        'You can not cancel a sales order line that is linked '
                        'to a stock movement has done if it is not a return.'))
        return self.write({'state': 'cancel'})
