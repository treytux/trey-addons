###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    last_modified_fields = fields.Text(
        string='Last Modified Fields',
        translate=False,
    )

    @api.multi
    def write(self, vals):
        if self.env.user.partner_id == self.env.ref('base.partner_root'):
            return super().write(vals)
        mod_fields = self.last_modified_fields or []
        try:
            mod_fields = json.loads(self.last_modified_fields or [])
        except Exception:
            mod_fields = []
        mod_fields = list(set(mod_fields + list(vals.keys()).copy()))
        vals.update({'last_modified_fields': json.dumps(mod_fields)})
        return super().write(vals)
