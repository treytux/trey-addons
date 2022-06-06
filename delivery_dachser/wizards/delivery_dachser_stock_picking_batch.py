###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import _, exceptions, fields, models


class DeliveryDachserStockPickingBatch(models.TransientModel):
    _name = 'delivery.dachser.stock.picking.batch'
    _description = 'Wizard to create file for Dachser in stock picking batch'

    def _get_default_dachser_product(self):
        batch_id = self.env.context.get('picking_batch_id', False)
        if batch_id:
            picking_batch = self.env['stock.picking.batch'].browse(batch_id)
            carriers = list(set(picking_batch.picking_ids.mapped(
                'carrier_id').ids))
            if len(carriers) == 1:
                carrier = picking_batch.picking_ids.mapped('carrier_id')[0]
                if carrier.delivery_type == 'dachser':
                    return carrier.dachser_delivery_product
        return None

    def _get_default_sender_code(self):
        batch_id = self.env.context.get('picking_batch_id', False)
        if batch_id:
            picking_batch = self.env['stock.picking.batch'].browse(batch_id)
            carriers = list(set(picking_batch.picking_ids.mapped(
                'carrier_id').ids))
            if len(carriers) == 1:
                carrier = picking_batch.picking_ids.mapped('carrier_id')[0]
                if carrier.delivery_type == 'dachser':
                    return carrier.dachser_customer_code

    def _get_default_dachser_country_code(self):
        return self.env['res.country'].search([('code', '=', 'ES')]).id

    picking_batch_id = fields.Many2one(
        comodel_name='stock.picking.batch',
        string='Picking batch',
    )
    dachser_sender_code = fields.Char(
        string='Sender code',
        size=9,
        default=_get_default_sender_code,
    )
    dachser_postponed_delivery_date = fields.Date(
        string='Postponed delivery date',
    )
    dachser_product = fields.Selection(
        selection=[
            ('001', 'FLEX'),
            ('002', 'SPEED'),
            ('013', 'FIX'),
            ('014', '10'),
            ('016', 'ON SITE PLUS'),
            ('017', 'ON SITE'),
        ],
        default=_get_default_dachser_product,
        string='Dachser product',
    )
    dachser_arrange_delivery = fields.Boolean(
        string='Arrange delivery',
    )
    dachser_lifting_platform = fields.Boolean(
        string='Lifting platform',
    )
    dachser_country_code = fields.Many2one(
        comodel_name='res.country',
        string='Country code',
        default=_get_default_dachser_country_code,
    )

    def attach_file_to_record(self, picking_batch, content):
        self.env['ir.attachment'].create({
            'name': 'DACHSER_%s' % picking_batch.name,
            'datas': base64.b64encode(content.encode('utf-8')),
            'datas_fname': 'dachser_%s.csv' % picking_batch.name,
            'res_model': 'stock.picking.batch',
            'res_id': picking_batch.id,
            'mimetype': 'application/csv',
        })

    def get_partner_info(self, picking_batch):
        partners = list(set(
            self.picking_batch_id.picking_ids.mapped('partner_id')))
        if len(partners) != 1:
            raise exceptions.ValidationError(
                _('Delivery: Different partners in the same group'))
        return partners[0]

    def get_delivery_note(self, picking_batch):
        delivery_note = ''
        for picking in self.picking_batch_id.picking_ids:
            if picking.delivery_note:
                delivery_note += picking.delivery_note + ' '
        return delivery_note

    def get_info_shipping(self, picking_batch):
        lines = self.picking_batch_id.picking_ids.mapped(
            'move_lines').filtered(lambda p: p.state == 'assigned')
        qty = 0
        for line in lines:
            if line.product_packaging:
                qty += line.product_qty / line.product_packaging.qty
                continue
            qty += line.product_qty
        shipping_weight = sum(
            line.product_id.weight * line.product_qty for line in lines)
        max_length = max(lines.mapped('product_id.product_length'))
        max_height = max(lines.mapped('product_id.product_height'))
        max_width = max(lines.mapped('product_id.product_width'))
        volume = max_length * max_height * max_width
        return qty, shipping_weight, volume

    def action_create_dachser_file(self):
        self.ensure_one()
        delivery_note = self.get_delivery_note(self.picking_batch_id)
        partner = self.get_partner_info(self.picking_batch_id)
        qty, shipping_weight, volume = self.get_info_shipping(
            self.picking_batch_id)
        string_format = (
            'TRS|%s||%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s%s')
        file_content = string_format % (
            self.picking_batch_id.name[:24].replace('/', '_'),
            self.dachser_sender_code,
            partner.name and partner.name[:32].upper() or '',
            partner.street and partner.street[:40].upper() or '',
            partner.city and partner.city[:27].upper() or '',
            partner.zip and partner.zip[:12] or '',
            self.dachser_country_code.code,
            str(int(qty)).zfill(3),
            str(int(shipping_weight)).zfill(5),
            ('%6.3f' % volume).lstrip().zfill(6),
            delivery_note and delivery_note[:38] or '',
            delivery_note and delivery_note[:38] or '',
            'P|00000.00|P|00000.00|',
            self.dachser_product,
            self.dachser_postponed_delivery_date.strftime('%Y%m%d'),
            partner.phone and partner.phone[:14] or '',
            partner.email and partner.email[:80] or '',
            'S|' if self.dachser_arrange_delivery else 'N|',
            'S|' if self.dachser_lifting_platform else 'N|',
        )
        self.attach_file_to_record(self.picking_batch_id, file_content)
