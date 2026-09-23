###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class IrAttachment(models.Model):
    _name = 'ir.attachment'
    _inherit = ['ir.attachment', 'image.optimizer']

    def check_conditions_mimetype(self):
        if not self.mimetype:
            return False
        mimetype = self.mimetype.split('/')[0]
        max_size = 1024 * 1024
        conditions = self.file_size > max_size and mimetype == 'image'
        return False if not conditions else True

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for record in res:
            if record.check_conditions_mimetype():
                record.optimize_images(record.datas)
        return res

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            if record.check_conditions_mimetype():
                record.optimize_images(record.datas)
        return res
