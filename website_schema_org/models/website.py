###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from urllib.parse import urljoin

from markupsafe import Markup
from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def schema_get(self):
        self.ensure_one()
        domain = self.domain or self.get_base_url()
        return Markup(json.dumps({
            '@context': 'https://schema.org',
            '@type': 'Organization',
            'name': self.name,
            'legalName': self.company_id.name,
            'url': domain,
            'logo': urljoin(domain, '/logo'),
            'address': {
                '@type': 'PostalAddress',
                'streetAddress': self.company_id.street,
                'addressLocality': self.company_id.city,
                'addressRegion': self.company_id.state_id.name,
                'postalCode': self.company_id.zip,
                'addressCountry': self.company_id.country_id.code,
            },
            'contactPoint': {
                '@type': 'ContactPoint',
                'contactType': 'customer support',
                'telephone': self.company_id.phone,
                'email': self.company_id.email,
            },
            'sameAs': [
                self.company_id[f] for f in dir(self.company_id)
                if f.startswith('social_') and self.company_id[f]
            ],
        }))
