# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    journal_ids = fields.One2many(
        comodel_name='booking.journal',
        inverse_name='company_id',
        string="Account Journals",
        required=False)
