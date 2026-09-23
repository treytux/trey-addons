###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class WizardStockPickingSignature(models.TransientModel):
    _name = 'wizard.stock.picking.signature'
    _description = 'Wizard to sign pickings'

    signature = fields.Binary(
        string='Signature',
        required=True,
    )
    filename = fields.Char(
        string='Filename',
        required=True,
    )

    def button_accept_sign(self):
        self.ensure_one()
        picking = self.env['stock.picking'].browse(
            self.env.context.get('active_id', []))
        picking.write({
            'signature': self.signature,
            'signature_datetime': fields.Datetime.now(),
            'signature_filename': self.filename,
        })
        self.env['ir.attachment'].create({
            'name': self.filename,
            'datas_fname': self.filename,
            'datas': self.signature,
            'res_model': 'stock.picking',
            'res_id': self.env.context.get('active_id', []),
        })
        return {
            'type': 'ir.actions.act_window_close',
        }
