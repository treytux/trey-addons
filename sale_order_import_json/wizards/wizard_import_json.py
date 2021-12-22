###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json

from odoo import api, fields, models


class WizardImportJson(models.TransientModel):
    _name = 'wizard.import.json'
    _description = 'Wizard to create sales orders with JSON import'

    json_file = fields.Binary(
        string='JSON file',
        help='JSON file to create a sale order',
        required=True,
    )

    @api.multi
    def button_accept(self):
        self.ensure_one()
        data = base64.b64decode(self.json_file)
        data = data.decode('utf-8').replace("'", '"')
        data = json.loads(data)
        self.env['sale.order'].json_import(data)
