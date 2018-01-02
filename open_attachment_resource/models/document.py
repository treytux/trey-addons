# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, _
import logging
_log = logging.getLogger(__name__)


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    @api.multi
    def action_open_res(self):
        assert self.res_model is not False, (
            'This attachment has no assigned resource model!')
        assert self.res_id != 0, 'This attachment has no assigned id!'
        return {
            'name': _('%s (id=%s)' % (self.res_model, self.res_id)),
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.res_id,
        }
