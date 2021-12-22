###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import fields, models


class DeliveryDachser(models.TransientModel):
    _name = 'delivery.dachser'
    _description = 'Wizard to create file for Dachser'

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    dachser_sender_code = fields.Char(
        string='Sender code',
        size=9,
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
        default='001',
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
    )

    def attach_file_to_record(self, picking, content):
        self.env['ir.attachment'].create({
            'name': 'DACHSER_%s' % picking.name,
            'datas': base64.b64encode(content.encode('utf-8')),
            'datas_fname': 'dachser_%s.csv' % picking.name,
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'mimetype': 'application/csv',
        })

    def action_create_dachser_file(self):
        self.ensure_one()
        string_format = (
            'TRS|%s||%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s%s')
        file_content = string_format % (
            self.picking_id.name[:24],
            self.dachser_sender_code,
            self.picking_id.partner_id.name
            and self.picking_id.partner_id.name[:32] or '',
            self.picking_id.partner_id.street
            and self.picking_id.partner_id.street[:40] or '',
            self.picking_id.partner_id.city
            and self.picking_id.partner_id.city[:27] or '',
            self.picking_id.partner_id.zip
            and self.picking_id.partner_id.zip[:12] or '',
            self.dachser_country_code.code,
            str(self.picking_id.number_of_packages).zfill(3),
            str(int(self.picking_id.shipping_weight)).zfill(5),
            ('%6.3f' % self.picking_id.volume).lstrip().zfill(6),
            self.picking_id.delivery_note
            and self.picking_id.delivery_note[:38] or '',
            self.picking_id.delivery_note
            and self.picking_id.delivery_note[:38] or '',
            'P|00000.00|P|00000.00|',
            self.dachser_product,
            self.dachser_postponed_delivery_date.strftime('%Y%m%d'),
            self.picking_id.partner_id.phone
            and self.picking_id.partner_id.phone[:14] or '',
            self.picking_id.partner_id.email
            and self.picking_id.partner_id.email[:80] or '',
            'S|' if self.dachser_arrange_delivery else 'N|',
            'S|' if self.dachser_lifting_platform else 'N|',
        )
        self.attach_file_to_record(self.picking_id, file_content)
