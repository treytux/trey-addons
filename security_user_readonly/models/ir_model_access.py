###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models, tools
from odoo.exceptions import AccessError


class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'

    @api.model
    @tools.ormcache_context('self._uid', 'model', 'mode', 'raise_exception',
                            keys=('lang',))
    def check(self, model, mode='read', raise_exception=True):
        result = super().check(model, mode, raise_exception=raise_exception)
        if not result:
            return result
        if mode == 'read':
            return result
        group_xmlid = 'security_user_readonly.group_user_readonly'
        if not self.env.user.has_group(group_xmlid):
            return result
        exclude_models = self._readonly_exclude_models()
        if raise_exception and model not in exclude_models:
            raise AccessError(_('Your user has read-only permissions.'))
        return False

    def _readonly_exclude_models(self):
        return self.sudo().search([
            ('group_id', '=', False),
            '|',
            ('perm_write', '=', True),
            '|',
            ('perm_create', '=', True),
            ('perm_unlink', '=', True),
        ]).mapped('model_id.model')
