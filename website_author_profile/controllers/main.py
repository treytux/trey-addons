###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request


class AuthorProfile(http.Controller):

    @http.route('/author/profile/<int:author_id>',
                type='http', auth='public', website=True)
    def author_profile(self, author_id):
        author = request.env['res.partner'].sudo().browse(author_id)
        if not author.exists():
            return request.render('website_author_profile.author_not_found', {
                'author_id': author_id,
            })
        blog_posts = request.env['blog.post'].sudo().search([
            ('author_id', '=', author.id),
        ])
        return request.render('website_author_profile.author_profile', {
            'author': author,
            'blog_posts': blog_posts,
        })
