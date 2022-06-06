###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, models


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    def create_simulate_stock_picking(self):
        picking = super().create_simulate_stock_picking()
        partners = list(set(self.picking_ids.mapped('partner_id')))
        carriers = list(set(self.picking_ids.mapped('carrier_id')))
        if len(partners) == 1 and len(carriers) == 1 and (
                carriers[0].delivery_type == 'dachser'):
            attachments = self.env['ir.attachment'].search([
                ('res_id', '=', self.id),
                ('res_model', '=', self._name),
                ('mimetype', '=', 'application/csv'),
            ])
            if not attachments:
                raise exceptions.ValidationError(
                    _('Dachser: you have to create the Dachser file using '
                        'the button "Create Dachser file"'))
            if len(attachments) > 1:
                raise exceptions.ValidationError(_(
                    'Dachser: error when adding the file to shipment request'))
            self.env['ir.attachment'].create({
                'name': attachments[0].name,
                'datas': attachments[0].datas,
                'datas_fname': attachments[0].datas_fname,
                'res_model': picking._name,
                'res_id': picking.id,
                'mimetype': attachments[0].mimetype,
            })
        return picking

    def add_shipping_info(self, picking, info):
        res = super().add_shipping_info(picking, info)
        if picking.delivery_type == 'dachser':
            dachser_key_list = [
                'dachser_expedition_code',
                'dachser_shipment_date',
                'dachser_token',
            ]
            if not any(key in info[0] for key in dachser_key_list):
                raise exceptions.ValidationError(_(
                    'Dachser: An error occurred in the connection to the '
                    'Dachser API. Delete the shipment just registered with '
                    'reference %s from Aidaweb and re-register the shipment '
                    'from the delivery note grouping.' % (
                        picking.batch_id.name)))
            picking.write({
                'dachser_expedition_code': info[0]['dachser_expedition_code'],
                'dachser_shipment_date': info[0]['dachser_shipment_date'],
                'dachser_token': info[0]['dachser_token'],
            })
        return res

    def get_picking_attachments(self, picking):
        attachments = super().get_picking_attachments(picking)
        if picking.carrier_id.delivery_type == 'dachser':
            if picking.not_dachser_delivery_label:
                picking.carrier_id.get_dachser_label(
                    picking, picking.dachser_token)
            attachments = self.env['ir.attachment'].search([
                ('res_id', '=', picking.id),
                ('res_model', '=', picking._name),
            ])
        return attachments

    def _prepare_dachser_wizard(self):
        self.ensure_one()
        return {
            'picking_batch_id': self.id,
        }

    def action_open_dachser_stock_picking_batch_wizard(self):
        self.ensure_one()
        vals = self._prepare_dachser_wizard()
        context = self.env.context.copy()
        context['picking_batch_id'] = vals['picking_batch_id']
        self.env.context = context
        wizard = self.env['delivery.dachser.stock.picking.batch'].create(vals)
        action = self.env.ref(
            'delivery_dachser.delivery_dachser_stock_picking_batch_action')
        action = action.read()[0]
        action['res_id'] = wizard.id
        action['context'] = self._context.copy()
        return action
