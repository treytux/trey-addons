##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
import re

from odoo import models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    def _replace_email_logo(self, body_html):
        self.ensure_one()
        if not body_html or 'logo' not in self._fields or not self.logo:
            return body_html
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url') or ''
        base_url = base_url.rstrip('/')
        team_logo_path = f'/team_logo/{self.id}'
        team_logo_url = (
            f"{base_url}{team_logo_path}" if base_url else team_logo_path)
        src_patterns = [
            (
                r'(?P<prefix>\bsrc\s*=\s*["\'])'
                r'(?:https?://[^"\']+)?/logo\.png(?:\?[^"\']*)?'
                r'(?P<suffix>["\'])'
            ),
            (
                r'(?P<prefix>\bsrc\s*=\s*["\'])'
                r'https?://[^"\']+#https?://[^"\']+/logo\.png(?:\?[^"\']*)?'
                r'(?P<suffix>["\'])'
            )
        ]
        for pattern in src_patterns:
            body_html = re.sub(
                pattern, rf'\g<prefix>{team_logo_url}\g<suffix>',
                body_html, flags=re.IGNORECASE)
        return body_html
