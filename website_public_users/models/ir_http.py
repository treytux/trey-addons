###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_public(cls):
        super()._auth_method_public()
        if request.context.get('set_profile'):
            request.uid = request.context['set_profile']
