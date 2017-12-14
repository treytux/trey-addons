# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
import logging
_log = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _signup_create_user(self, values):
        res = super(ResUsers, self)._signup_create_user(values)
        user = self.browse(res)
        parent = user.partner_id.copy()
        parent.name = user.name
        parent.is_company = True
        parent.email = None
        user.partner_id.parent_id = parent.id
        user.partner_id.use_parent_address = True
        return res
