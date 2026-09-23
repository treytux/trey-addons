###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import api, fields, models
from odoo.tools import image_process

DELIVERY_PROOF_MAX_SIZE = (1920, 1920)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    signature = fields.Binary(
        string='Signature',
        attachment=True,
        copy=False,
    )
    signature_datetime = fields.Datetime(
        string='Signature datetime',
        copy=False,
    )
    signature_filename = fields.Char(
        string='Signature filename',
        copy=False,
    )
    signed_by = fields.Char(
        string='Signed by',
        copy=False,
    )
    delivery_proof_attachment_id = fields.Many2one(
        string='Stamped delivery note photo attachment',
        comodel_name='ir.attachment',
        copy=False,
        ondelete='set null',
    )
    delivery_proof_filename = fields.Char(
        string='Stamped delivery note photo filename',
        copy=False,
    )
    delivery_proof_image = fields.Image(
        string='Stamped delivery note photo',
        compute='_compute_delivery_proof_image',
        store=False,
    )

    @api.depends(
        'delivery_proof_attachment_id', 'delivery_proof_attachment_id.datas')
    def _compute_delivery_proof_image(self):
        for picking in self:
            picking.delivery_proof_image = (
                picking.delivery_proof_attachment_id.datas or False)

    @api.depends('signature', 'delivery_proof_attachment_id')
    def _compute_is_signed(self):
        super()._compute_is_signed()
        for picking in self:
            picking.is_signed = picking.is_signed or bool(
                picking.delivery_proof_attachment_id)

    def store_delivery_proof_photo(self, image, filename=None):
        self.ensure_one()
        image = base64.b64encode(image_process(
            base64.b64decode(image or b''), size=DELIVERY_PROOF_MAX_SIZE))
        filename = filename or 'stamped_delivery_note.jpg'
        vals = {
            'name': filename,
            'datas': image,
            'res_model': 'stock.picking',
            'res_id': self.id,
        }
        attachment = self.delivery_proof_attachment_id
        if attachment:
            attachment.write(vals)
        else:
            attachment = self.env['ir.attachment'].create(vals)
        self.write({
            'delivery_proof_attachment_id': attachment.id,
            'delivery_proof_filename': filename,
        })
        return attachment

    def action_sign(self):
        self.ensure_one()
        return self.env['ir.actions.actions']._for_xml_id(
            'stock_picking_signature.stock_picking_signature_wizard_action')
