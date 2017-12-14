# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    _order = 'type,sequence,id'

    sequence = fields.Integer(
        'Sequence',
        help="Gives the sequence order when displaying a list of journals.")
