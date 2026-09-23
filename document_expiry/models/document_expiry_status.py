###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class DocumentExpiryStatus(models.Model):
    _name = 'document.expiry.status'
    _description = 'Document Expiry Status'

    name = fields.Char(
        required=True,
    )
    color = fields.Selection(
        selection=[
            ('red', 'Red'),
            ('brown', 'Brown'),
            ('purple', 'Purple'),
            ('green', 'Green'),
            ('blue', 'Blue'),
            ('gray', 'Gray'),
        ],
        required=True,
    )
    warn = fields.Boolean(
        help='Warn user when document expiry',
    )
    days = fields.Integer(
        helps='How many days before warn user',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
    )
    owner_type = fields.Selection(
        selection='_selection_owner_type',
        help='If selected, this status will be used for all documents of this '
             'type.',
        string='Apply only to document type',
    )

    @api.onchange('warn')
    def _onchange_warn(self):
        if not self.warn:
            self.days = 0

    @api.model
    def _selection_owner_type(self):
        return self.env['document.expiry']._fields['owner_type'].selection
