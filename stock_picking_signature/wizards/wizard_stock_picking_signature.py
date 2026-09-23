###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WizardStockPickingSignature(models.TransientModel):
    _name = 'wizard.stock.picking.signature'
    _description = 'Wizard to sign pickings'

    capture_mode = fields.Selection(
        selection=[
            ('sign', 'Handwritten signature'),
            ('photo', 'Stamped delivery note photo'),
        ],
        string='Capture mode',
        default='sign',
        required=True,
    )
    signature = fields.Binary(
        string='Signature',
    )
    proof_image = fields.Image(
        string='Stamped delivery note photo',
    )
    filename = fields.Char(
        string='Filename',
    )
    signed_by = fields.Char(
        string='Signed by',
        required=True,
    )

    @api.constrains('capture_mode', 'signature', 'filename', 'proof_image')
    def _check_capture(self):
        for wizard in self:
            if wizard.capture_mode == 'sign' and not wizard.signature:
                raise ValidationError(_(
                    'A handwritten signature is required.'))
            if wizard.capture_mode == 'sign' and not wizard.filename:
                raise ValidationError(_(
                    'A filename is required.'))
            if wizard.capture_mode == 'photo' and not wizard.proof_image:
                raise ValidationError(_(
                    'A photo of the delivery note is required.'))

    def button_accept_sign(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id')
        picking = self.env['stock.picking'].browse(active_id)
        if self.capture_mode == 'photo':
            picking.store_delivery_proof_photo(self.proof_image, self.filename)
            picking.write({
                'signature_datetime': fields.Datetime.now(),
                'signed_by': self.signed_by,
            })
            return {
                'type': 'ir.actions.act_window_close',
            }
        picking.write({
            'signature': self.signature,
            'signature_datetime': fields.Datetime.now(),
            'signed_by': self.signed_by,
            'signature_filename': self.filename,
        })
        self.env['ir.attachment'].create({
            'name': self.filename,
            'datas': self.signature,
            'res_model': 'stock.picking',
            'res_id': active_id,
        })
        return {
            'type': 'ir.actions.act_window_close',
        }
