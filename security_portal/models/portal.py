# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.##
from openerp import models, fields


class PortalManager(models.Model):
    _inherit = 'res.groups'

    is_portalmanager = fields.Boolean(
        string='Portal Manager',
        help='If checked, this group is usable as a portal manager.')
