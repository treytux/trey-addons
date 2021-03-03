###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    google_feed_expiry_time = fields.Integer(
        related=['company_id', 'google_feed_expiry_time'])
    google_image_height = fields.Integer(
        related=['company_id', 'google_image_height'])
    google_image_width = fields.Integer(
        related=['company_id', 'google_image_width'])
    google_use_shipping_settings = fields.Boolean(
        related=['company_id', 'google_use_shipping_settings'])
    google_shipping_country = fields.Char(
        related=['company_id', 'google_shipping_country'])
    google_shipping_service = fields.Char(
        related=['company_id', 'google_shipping_service'])
    google_shipping_price = fields.Float(
        related=['company_id', 'google_shipping_price'])
