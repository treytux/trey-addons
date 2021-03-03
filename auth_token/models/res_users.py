###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import random
import string

from odoo import _, api, exceptions, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _get_default_token(self):
        return ''.join(
            random.choice(
                string.ascii_uppercase + string.digits
            ) for i in range(1, 33))

    token = fields.Char(
        string='Token',
        help='Alphanumeric key to login into Odoo',
        default=_get_default_token,
    )

    @api.multi
    def _set_default_token(self):
        self.token = self._get_default_token()

    @api.constrains('token')
    def _check_token_unique(self):
        ids = self.search([
            ('id', '!=', self.id),
            ('token', '=', self.token),
        ])
        if ids:
            raise exceptions.Warning(_('User token must be unique'))
