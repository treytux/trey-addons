###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'is_default desc, display_name'

    is_default = fields.Boolean(
        string='Default')

    @api.one
    def _propage_is_default(self):
        if not self.is_default:
            return
        partners = self.parent_id.child_ids.filtered(
            lambda p:
            p.id != self.id and self.type == p.type and not p.child_ids)
        partners.write({'is_default': False})

    @api.model
    def create(self, vals):
        res = super().create(vals)
        self._propage_is_default()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        self._propage_is_default()
        return res

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        self._propage_is_default()
        return super().onchange_parent_id()

    @api.onchange('is_default')
    def onchange_is_default(self):
        self._propage_is_default()
