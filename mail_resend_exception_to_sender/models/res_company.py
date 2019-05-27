# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    exception_sender_options = fields.Selection(
        selection=[
            ('none', 'To nobody'),
            ('email_from', 'To the sender'),
            ('user_except_sender', 'To the exception users'),
            ('both', 'To both')],
        string='Exception sender options',
        default='email_from',
        required=True,
        help="Options to select the recipient to which the messages in "
        "\'Delivery Failed\' state:\n"
        "- To nobody: no email will be sent to anyone.\n"
        "- To the sender: an email will be sent to the sender of the email.\n"
        "- To the exception users: a warning mail will be sent to the users "
        "defined in the 'User exception senders' field.\n"
        "- To both: a warning mail will be sent to the sender of the mail and "
        "to the users defined in the 'User exception senders' field.")
    user_except_sender_ids = fields.Many2many(
        comodel_name='res.users',
        relation='company2user_rel',
        column1='company_id',
        column2='user_id',
        help="Users to notify by mail when an email is in the \'Delivery "
             "Failed\' state.\nThis emails will be obtained from the company "
             "related to the users.")
