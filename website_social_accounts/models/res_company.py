###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Company(models.Model):
    _inherit = 'res.company'

    social_flickr = fields.Char('Flickr Account')
    social_instagram = fields.Char('Instagram Account')
    social_pinterest = fields.Char('Pinterest Account')
    social_reddit = fields.Char('Reddit Account')
    social_skype = fields.Char('Skype Account')
    social_tumblr = fields.Char('Tumblr Account')
    social_twitch = fields.Char('Twitch Account')
    social_vimeo = fields.Char('Vimeo Account')
    social_whatsapp = fields.Char('Whatsapp Number')

    @api.constrains('social_whatsapp')
    def _check_whatsapp_number(self):
        if self.social_whatsapp and not self.social_whatsapp.isdigit():
            raise UserError(_("WhatsApp number can only contain digits"))
