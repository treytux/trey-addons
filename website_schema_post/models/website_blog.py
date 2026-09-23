import json

from markupsafe import Markup
from odoo import models


class BlogPost(models.Model):
    _inherit = 'blog.post'

    def post_schema_get(self):
        self.ensure_one()
        return Markup(json.dumps({
            '@context': 'https://schema.org',
            '@type': 'NewsArticle',
            'headline': self.name,
            'image': [
                self._get_background(width=800, height=800),
                self._get_background(width=800, height=600),
                self._get_background(width=800, height=450),
            ],
            'datePublished': self.published_date.replace(microsecond=0).isoformat(),
            'dateModified': self.write_date.replace(microsecond=0).isoformat(),
            'author': [{
                '@type': 'Person',
                'name': self.author_name,
                'url': f'/author/profile/{self.author_id.id}',
            }],
        }, indent=4))
