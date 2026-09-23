###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class DeliveryCarrierManifestSignature(models.TransientModel):
    _name = 'delivery.carrier.manifest.signature'
    _description = 'Wizard to sign manifest and pickings related to manifest'

    manifest_id = fields.Many2one(
        comodel_name='delivery.carrier.manifest',
        string='Manifest',
    )
    signature = fields.Binary(
        string='Signature',
        required=True,
    )
    is_signed = fields.Boolean(
        string='Is signed',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['manifest_id'] = self.env.context.get('active_id')
        manifest = self.env['delivery.carrier.manifest'].browse(
            self.env.context.get('active_id'))
        res['is_signed'] = manifest.is_signed
        return res

    def create_signature_attachment(self, name, datas, model, record_id):
        self.env['ir.attachment'].create({
            'name': name,
            'datas': datas,
            'res_model': model,
            'res_id': record_id,
        })

    def button_sign_manifest(self):
        self.ensure_one()
        manifest = self.env['delivery.carrier.manifest'].browse(
            self.env.context.get('active_id', []))
        manifest.write({
            'signature': self.signature,
            'signature_date': fields.Date.today(),
            'is_signed': True,
        })
        filename = 'Picking manifest signature by Carrier - %s' % (
            manifest.name),
        self.create_signature_attachment(
            filename, self.signature, 'delivery.carrier.manifest', manifest.id)
        for picking in manifest.picking_ids:
            picking.write({
                'signature': self.signature,
                'signature_date': fields.Date.today(),
            })
            self.create_signature_attachment(
                filename, self.signature, 'stock.picking', picking.id)
        return {
            'type': 'ir.actions.act_window_close',
        }
