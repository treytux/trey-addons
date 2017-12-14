# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import openerp.addons.website_blog.controllers.main as main
from openerp import http
from openerp.http import request


class WebsiteBlog(main.WebsiteBlog):
    @http.route()
    def blog_post(self, blog, blog_post, tag_id=None, page=1,
                  enable_editor=None, **post):
        res = super(WebsiteBlog, self).blog_post(
            blog, blog_post, tag_id=tag_id, page=page,
            enable_editor=enable_editor, **post)
        env = request.env
        all_post_ids = env['blog.post'].search([('blog_id', '=', blog.id)])
        current_blog_post_index = all_post_ids.ids.index(blog_post.id)
        previous_post = (
            False if current_blog_post_index == len(all_post_ids) - 1
            else all_post_ids[current_blog_post_index + 1])
        next_post = (
            False if current_blog_post_index == 0
            else all_post_ids[current_blog_post_index - 1])
        res.qcontext['previous_post'] = previous_post
        res.qcontext['next_post'] = next_post
        return res
