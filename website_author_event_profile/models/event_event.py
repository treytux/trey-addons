###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class Event(models.Model):
    _inherit = 'event.event'

    def get_clean_background_url(self, width=800, height=600):
        self.ensure_one()
        bg = self._get_background(width=width, height=height)
        if bg:
            return bg.replace('url(', '').replace(')', '').replace(
                '\'', '').replace('\"', '')
        return ''
