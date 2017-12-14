# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import datetime
from openerp import tools
from openerp.addons.web.http import request
from openerp.addons.website_blog.controllers.main import WebsiteBlog


class WebsiteBlog(WebsiteBlog):
    def nav_list(self):
        env = request.env
        groups = env['blog.post'].read_group(
            [], ['name', 'website_publication_date'],
            groupby='website_publication_date',
            orderby='website_publication_date desc')
        nav_list = []
        for group in groups:
            if group['__domain'][0][2] and group['__domain'][1][2]:
                begin_date = datetime.datetime.strptime(
                    group['__domain'][0][2],
                    tools.DEFAULT_SERVER_DATETIME_FORMAT).date()
                end_date = datetime.datetime.strptime(
                    group['__domain'][1][2],
                    tools.DEFAULT_SERVER_DATETIME_FORMAT).date()
                group['date_begin'] = '%s' % datetime.date.strftime(
                    begin_date, tools.DEFAULT_SERVER_DATE_FORMAT)
                group['date_end'] = '%s' % datetime.date.strftime(
                    end_date, tools.DEFAULT_SERVER_DATE_FORMAT)
                nav_list.append(group)
        return nav_list
