###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleCustomizationAddFile(models.TransientModel):
    _name = 'sale.customization.add.file'
    _description = 'Sale customization add file wizard'

    ffile = fields.Binary(
        string='Design file',
        required=True,
    )
    filename = fields.Char(
        string='Filename',
        required=True,
    )

    @api.multi
    def action_add(self):
        self.env['ir.attachment'].create({
            'res_model': 'sale.customization',
            'res_id': self.env.context.get('active_id', []),
            'name': self.filename,
            'datas': self.ffile})
        return {'type': 'ir.actions.act_window_close'}
