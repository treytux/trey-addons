###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = 'res.partner'

    allowed = fields.Boolean(
        string='Allowed',
        help='Allow or block contact user for login into system.',
        default=True)

    @api.multi
    def _allowed_message_get(self, change_from='partner'):
        self.ensure_one()
        messages = {
            ('partner', False): _('Has blocked partner'),
            ('partner', True): _('Partner has unblocked'),
            ('user', False): _('Has blocked partner from user'),
            ('user', True): _('Partner has unblocked from user'),
            ('child', False): _('Has blocked partner from a child'),
            ('child', True): _('Partner has unblocked from a child'),
            ('parent', False): _('Has blocked parent partner'),
            ('parent', True): _('Parent partner has unblocked')}
        return messages[(change_from, self.allowed)]

    @api.multi
    def _allowed_message_post(self, change_from='partner'):
        self.message_post(self._allowed_message_get(change_from))

    @api.one
    def _allowed_set(self, allowed, change_from='partner'):
        if self.allowed != allowed:
            self.allowed = allowed
            self._allowed_message_post(change_from)
        for child in self.child_ids:
            if child.allowed == allowed:
                continue
            child.allowed = allowed
            child._allowed_message_post('parent')
        if self.parent_id and self.parent_id.allowed != allowed:
            self.parent_id._allowed_set(allowed, 'child')

    @api.multi
    def toggle_allowed(self):
        for record in self:
            record._allowed_set(not record.allowed)
