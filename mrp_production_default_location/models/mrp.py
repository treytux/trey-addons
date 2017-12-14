# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields
import logging
_log = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _src_id_default(self):
        cr, uid, context = self.env.args
        user = self.env['res.users'].browse(uid)
        if user.company_id.mrp_location_src_id.exists():
            return user.company_id.mrp_location_src_id.id
        return super(MrpProduction, self)._src_id_default()

    @api.multi
    def _dest_id_default(self):
        cr, uid, context = self.env.args
        user = self.env['res.users'].browse(uid)
        if user.company_id.mrp_location_dst_id.exists():
            return user.company_id.mrp_location_dst_id.id

        return super(MrpProduction, self)._dest_id_default()

    location_src_id = fields.Many2one(
        default=_src_id_default)
    location_dest_id = fields.Many2one(
        default=_dest_id_default)
