###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Company(models.Model):
    _inherit = 'res.company'

    social_flickr = fields.Char(
        string='Flickr Account',
    )
    social_pinterest = fields.Char(
        string='Pinterest Account',
    )
    social_reddit = fields.Char(
        string='Reddit Account',
    )
    social_skype = fields.Char(
        string='Skype Account',
    )
    social_tumblr = fields.Char(
        string='Tumblr Account',
    )
    social_twitch = fields.Char(
        string='Twitch Account',
    )
    social_vimeo = fields.Char(
        string='Vimeo Account',
    )
    social_whatsapp = fields.Char(
        string='Whatsapp Number',
    )

    @api.constrains('social_whatsapp')
    def _check_whatsapp_number(self):
        if self.social_whatsapp and not self.social_whatsapp.isdigit():
            raise UserError(_('WhatsApp number can only contain digits'))
