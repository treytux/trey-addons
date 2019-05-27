###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields
import base64
import io


class ProductPricelistImport(models.TransientModel):
    _name = 'product.pricelist.import'
    _description = 'Wizard to import pricelists'

    data_file = fields.Binary(
        string='Pricelist file',
        required=True)

    @api.multi
    def import_file(self):
        self.ensure_one()
        buf = io.BytesIO()
        buf.write(base64.b64decode(self.data_file))
        self.env['product.pricelist'].import_excel(buf)
