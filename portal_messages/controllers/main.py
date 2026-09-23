from collections import OrderedDict

from odoo import _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessDenied, AccessError, MissingError
from odoo.http import request, route
from odoo.osv.expression import OR


class PortalMessage(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(PortalMessage, self)._prepare_portal_layout_values()
        messages_obj = request.env['mail.message']
        values['message_count'] = (
            messages_obj.check_access_rights('read', raise_exception=False)
            and messages_obj.search_count([
                ('message_type', '!=', ''),
                ('message_type', '!=', False),
                ('message_type', '!=', 'notification'),
                ('subtype_id.name', '!=', 'Note')
            ])
            or 0
        )
        return values

    @route(
        ['/my/messages', '/my/messages/page/<int:page>'],
        type='http',
        auth='user',
        website=True)
    def portal_my_messages(
            self, page=1, date_begin=None, date_end=None, sortby=None,
            filterby=None, search=None, search_in=None, **kw):
        values = self._prepare_portal_layout_values()
        Message = request.env['mail.message']
        domain = [
            ('message_type', '!=', ''),
            ('message_type', '!=', False),
            ('message_type', '!=', 'notification'),
            ('subtype_id.name', '!=', 'Note'),
        ]
        searchbar_sortings = {
            'date_desc': {
                'label': _('Newest'),
                'order': 'date desc'
            },
            'date_asc': {
                'label': _('Oldest'),
                'order': 'date asc'
            },
            'subject': {
                'label': _('Subject'),
                'order': 'subject asc, description asc'
            },
        }
        searchbar_filters = {
            'all': {
                'label': _('All'),
                'domain': []
            },
            'attachment': {
                'label': _('With Attachments'),
                'domain': [('attachment_ids', '!=', False)]
            }
        }
        searchbar_inputs = {
            'subject': {
                'input': 'subject',
                'label': _('Search in Subject')
            },
            'content': {
                'input': 'content',
                'label': _('Search in Content')
            },
            'author': {
                'input': 'author',
                'label': _('Search in Author')
            },
            'all': {
                'input': 'all',
                'label': _('Search in All')
            },
        }
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        if not sortby:
            sortby = 'date_desc'
        order = searchbar_sortings[sortby]['order']
        if search:
            search_domain = []
            if search_in in ('subject', 'all', False):
                search_domain = OR(
                    [search_domain, [('subject', 'ilike', search)]])
            if search_in in ('content', 'all'):
                search_domain = OR(
                    [search_domain, [('body', 'ilike', search)]])
            if search_in in ('author', 'all'):
                search_domain = OR(
                    [search_domain, [('author_id.name', 'ilike', search)]])
            domain += search_domain
        message_count = Message.search_count(domain)
        pager = portal_pager(
            url='/my/messages',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
                'filterby': filterby,
                'search_in': search_in,
                'search': search,
            },
            total=message_count,
            page=page,
            step=self._items_per_page
        )
        messages = Message.search(domain)
        messages = Message.search(
            [('id', 'in', messages.ids)], order=order, limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_messages_history'] = messages.ids[:100]
        values.update({
            'date': date_begin,
            'messages': messages,
            'pager': pager,
            'page_name': 'messages',
            'default_url': '/my/messages',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'filterby': filterby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items()))
        })
        return request.render('portal_messages.portal_my_messages', values)

    @route(
        ['/my/message/<int:email_id>'],
        type='http',
        auth="public",
        website=True)
    def portal_my_message(
            self, email_id, access_token=None, report_type=None,
            download=False, **kw):
        try:
            message = self._document_check_access(
                'mail.message', email_id, access_token)
        except (AccessError, MissingError, AccessDenied):
            return request.redirect('/my')
        mimetypes = []
        if message.attachment_ids:
            for attachment in message.attachment_ids:
                mimetype = attachment.mimetype
                mimetype = mimetype.split('/')[1]
                images = ['png', 'jpg', 'jpeg', 'webp']
                if mimetype in images:
                    mimetypes.append('image')
                elif mimetype == 'pdf':
                    mimetypes.append('image')
                else:
                    mimetypes.append('unknown')
        values = {
            'message': message,
            'mimetype': mimetypes,
            'page_name': 'message',
        }
        return request.render('portal_messages.portal_my_message', values)
