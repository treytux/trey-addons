###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class DocumentExpiryAbstract(models.AbstractModel):
    _name = 'document.expiry.abstract'
    _description = 'Abstract document expiry'
    _order = 'start_date, end_date'

    @api.model
    def _selection_document_type(self):
        return [
            ('custom', _('Custom')),
            ('attachment', _('Attachment')),
        ]

    owner_type = fields.Selection(
        selection=[
            ('other', 'Other'),
        ],
        default='other',
    )
    document_name = fields.Char(
        string='Name',
    )
    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Document',
    )
    start_date = fields.Date(
        required=True,
    )
    end_date = fields.Date(
        required=True,
    )
    document_type = fields.Selection(
        selection='_selection_document_type',
        default='custom',
        required=True,
    )
    status_id = fields.Many2one(
        comodel_name='document.expiry.status',
        default=lambda self: self.env.ref(
            'document_expiry.document_expiry_status_valid'),
        required=True,
    )
    color = fields.Selection(
        related='status_id.color',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.company,
    )
    _sql_constraints = [
        ('start_date_end_date_check', 'CHECK (start_date <= end_date)',
         'The start date must be before the end date.'),
    ]

    def _get_document_type(self):
        return self.DOCUMENT_TYPE
