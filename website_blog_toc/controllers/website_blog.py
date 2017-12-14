# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp.addons.website.models.website import slugify
from openerp.addons.website_blog.controllers import main
from openerp import http
import logging
_log = logging.getLogger(__name__)
try:
    from bs4 import BeautifulSoup
except ImportError:
    _log.error('Module python "bs4" is not installed, please install '
               'with "pip install BeautifulSoup4"')

TOC_TAGS = ['h2', 'h3', 'h4', 'h5', 'h6']


class WebsiteBlog(main.WebsiteBlog):
    def get_toc(self, html):
        toc = []
        content = BeautifulSoup(html, 'html.parser')
        for tag in content.findAll(TOC_TAGS):
            toc.append({
                'id': slugify(tag.string),
                'name': slugify(tag.name),
                'string': tag.string})
            tag['id'] = slugify(tag.string)
        return toc, content

    @http.route()
    def blog_post(self, blog, blog_post, tag_id=None, page=1,
                  enable_editor=None, **post):
        res = super(WebsiteBlog, self).blog_post(
            blog, blog_post, tag_id=tag_id, page=page,
            enable_editor=enable_editor, **post)
        toc, content = self.get_toc(blog_post.content)
        res.qcontext['toc'] = toc
        blog_post.sudo().content = unicode(content)
        return res
