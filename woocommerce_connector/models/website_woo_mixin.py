###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json
import logging
from datetime import datetime

from odoo import _, api, fields, models, tools

_log = logging.getLogger(__name__)

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    job = None


class WooError(Exception):
    pass


class WebsiteWooMixin(models.AbstractModel):
    _name = 'website.woo.mixin'
    _description = 'Website Woocommerce Mixin'

    woo_ids = fields.Text(
        string='JSON Woocommerce IDs',
        help='A dict python serializaded with web ID key and ID woo how value',
    )

    def woo_endpoint_get(self, woo_id=None):
        raise NotImplementedError

    def woo_upload_dict_get(self, update_fields=None):
        raise NotImplementedError

    def woo_sync_export_records(self, website, products=None):
        raise NotImplementedError

    def woo_sync_import_record(self, website, data):
        raise NotImplementedError

    @api.model
    def _website_get(self):
        website = self._context.get('website')
        if website:
            return website
        website_id = self._context.get('website_id')
        if website_id:
            return self.env['website'].browse(website_id)
        raise Exception(
            'Developer error: no website has been passed to context how '
            'object with key "website" or with id with key "website_id".'
            f'Context: {self._context}')

    def woo_format_str_to_date(self, value):
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')

    def woo_format_date_to_str(self, value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%dT%H:%M:%S')
        return False

    def woo_ids_get(self):
        self.ensure_one()
        return eval(self.woo_ids or '{}')

    def woo_set_id(self, woo_id):
        website = self._website_get()
        woo_ids = self.woo_ids_get()
        woo_ids[website.id] = woo_id
        self.woo_ids = str(woo_ids)

    def woo_get_id(self):
        website = self._website_get()
        woo_ids = self.woo_ids_get()
        return woo_ids.get(website.id)

    @api.model
    def woo_rpc_call(self, method, endpoint, data=None, website=None):
        def message(txt):
            return f'({endpoint}) {txt} | {data}'

        if not data:
            data = {}
        website = website or self._website_get()
        woo_api = website.woo_api_get()
        fnc = getattr(woo_api, method)
        if method in ('post', 'put'):
            res = fnc(endpoint, data)
        else:
            res = fnc(endpoint, **data)
        try:
            res_data = res.json()
        except Exception:
            raise WooError(
                message(f'Not return JSON {res.content}'), res.content)
        if 200 <= res.status_code >= 299:
            msg = message(_(
                f'{self._name} error in the {method} operation to {endpoint}: '
                f'{res_data["message"]}'))
            raise WooError(msg, res_data)
        if isinstance(res_data, dict) and res_data.get('code'):
            msg = message(f'[{res_data["code"]}] {res_data["message"]}')
            raise WooError(msg, res_data)
        _log.info(message(f'{res.status_code}'))
        return res_data

    @api.model
    def woo_rpc_get(self, woo_id=None, params=None):
        if not params:
            params = {}
        return self.woo_rpc_call('get', self.woo_endpoint_get(woo_id), params)

    @api.model
    def _woo_rpc_upload(self, data):
        if not data:
            return False
        woo_id = self.woo_get_id()
        if woo_id:
            return self.woo_rpc_call(
                'put', self.woo_endpoint_get(woo_id), data)
        return self.woo_rpc_call('post', self.woo_endpoint_get(), data)

    def _woo_is_upload_exception(self, code, message, data):
        return True

    def woo_rpc_upload(self, update_fields=None, retry=True):
        response = {}
        website = self._website_get()
        self = self.with_context(
            website=website, lang=website.default_lang_id.code)
        for record in self:
            data = record.woo_upload_dict_get(update_fields)
            if not data:
                continue
            try:
                data = record._woo_rpc_upload(data) or {}
            except WooError as exception:
                if not retry:
                    raise exception
                args = exception.args[1]
                is_exception = record._woo_is_upload_exception(
                    args.get('code') if isinstance(args, dict) else '',
                    args.get('message') if isinstance(args, dict) else '',
                    args.get('data') if isinstance(args, dict) else [])
                if not is_exception:
                    continue
                raise exception
            response[record.id] = data
            if data.get('id'):
                record.woo_set_id(response[record.id]['id'])
        return response

    def woo_rpc_upload_job(self, website_id, ids, update_fields=None):
        record = self.env[self._name].with_context(website_id=website_id)
        record = record.browse(ids)
        return record.woo_rpc_upload(update_fields)

    def woo_upload(self, website, update_fields=None):
        if not update_fields:
            update_fields = []
        for record in self.with_context(website=website):
            if website.woo_export_method == 'queue':
                record.with_delay().woo_rpc_upload_job(
                    website.id, record.id, update_fields)
                continue
            record.woo_rpc_upload(update_fields)

    @api.model
    def _woo_rpc_delete(self, woo_ids, force=True):
        params = {'params': {'force': force}}
        response = {}
        for id in woo_ids:
            try:
                response[id] = self.woo_rpc_call(
                    'delete', self.woo_endpoint_get(id), params)
            except WooError as exception:
                args = exception.args[1]
                code = args.get('code') if isinstance(args, dict) else ''
                ignore_errors = [
                    'woocommerce_rest_term_invalid',
                    'woocommerce_rest_product_invalid',
                    'woocommerce_rest_customer_invalid',
                ]
                if code in ignore_errors:
                    continue
                raise exception
        return response

    def woo_rpc_delete(self, force=True):
        woo_ids = [r.woo_get_id() for r in self]
        response = self._woo_rpc_delete(woo_ids)
        for record in self:
            record.woo_set_id(None)
        return response

    def woo_rpc_delete_job(self, website_id, woo_ids):
        return self.with_context(website_id=website_id)._woo_rpc_delete(
            woo_ids)

    @api.model
    def woo_delete(self, website, woo_ids=None):
        if not woo_ids:
            ids = {r.id: r.woo_ids_get() for r in self}
            woo_ids = [
                ids[r.id][website.id]
                for r in self if website.id in ids[r.id]
            ]
        if not woo_ids:
            return
        if website.woo_export_method == 'queue':
            self.with_delay().woo_rpc_delete_job(website.id, woo_ids)
            return
        self.with_context(website=website)._woo_rpc_delete(woo_ids)

    @api.model
    def woo_search_id(self, woo_id):
        website = self._website_get()
        domain = [
            '|', '|', '|',
            ('woo_ids', 'like', '{%s: %s,' % (website.id, woo_id)),
            ('woo_ids', 'like', '{%s: %s}' % (website.id, woo_id)),
            ('woo_ids', 'like', ' %s: %s}' % (website.id, woo_id)),
            ('woo_ids', 'like', ' %s: %s,' % (website.id, woo_id)),
        ]
        return self.search(domain)

    def woo_post_error(self, message):
        _log.error(message)
        message += _(
            f'<br/>This error is referenced with {self._description} '
            f'<a href=# data-oe-model={self._name} data-oe-id={self.id}>'
            f'{self["name"]}</a>')
        website = self._website_get()
        website.salesteam_id.message_post(
            body=message,
            subject=f'Woocommere {website.name} connector error')

    def _context_ignore_woo_upload_key_get(self):
        self.ensure_one()
        return ':'.join([self._name, str(self.id)])

    def _context_ignore_woo_upload_add(self):
        ignore_woo_upload = self._context.get('ignore_woo_upload', [])
        for record in self:
            key = record._context_ignore_woo_upload_key_get()
            if key not in ignore_woo_upload:
                ignore_woo_upload.append(key)
        return self.with_context(ignore_woo_upload=ignore_woo_upload)

    def _context_ignore_woo_upload_remove(self, keys=None):
        ignore_woo_upload = self._context.get('ignore_woo_upload', [])
        if not keys:
            keys = [r._context_ignore_woo_upload_key_get() for r in self]
        for key in keys:
            if key in ignore_woo_upload:
                ignore_woo_upload.remove(key)
        self = self.with_context(ignore_woo_upload=ignore_woo_upload)
        return self

    def _context_ignore_woo_upload_exists(self):
        self.ensure_one()
        ignore_woo_upload = self._context.get('ignore_woo_upload', [])
        key = self._context_ignore_woo_upload_key_get()
        return key in ignore_woo_upload

    def copy(self, default=None):
        ignore_woo_upload = self._context_ignore_woo_upload_exists()
        self = self._context_ignore_woo_upload_add()
        response = super().copy(default)
        if ignore_woo_upload:
            return response
        websites = self.env['website'].search([
            ('is_woo', '=', True),
            ('woo_export_method', '!=', 'manual'),
        ])
        for website in websites:
            response.woo_upload(website)
        key = self._context_ignore_woo_upload_key_get()
        self._context_ignore_woo_upload_remove([key])
        return response._context_ignore_woo_upload_remove([key])

    @api.model
    def create(self, vals):
        ignore_woo_upload = self._context.get('ignore_woo_upload', False)
        self = self.with_context(ignore_woo_upload=True)
        response = super().create(vals)
        # Odoo 16: website_published doesn't propagate to is_published
        # on product.product during create; force it here so that
        # woo_sync_export_records and woo_upload_dict_get work correctly
        if vals.get('website_published'):
            try:
                response.product_tmpl_id.is_published = True
            except Exception:
                pass
        if ignore_woo_upload:
            return response
        self = self.with_context(ignore_woo_upload=False)
        websites = self.env['website'].search([
            ('is_woo', '=', True),
            ('woo_export_method', '!=', 'manual'),
        ])
        for website in websites:
            if self.woo_sync_export_records(website, products=response):
                response.woo_upload(website)
        return response

    def write(self, vals):
        ignore_woo_upload = self._context.get('ignore_woo_upload', False)
        self = self.with_context(ignore_woo_upload=True)
        response = super().write(vals)
        if ignore_woo_upload:
            return response
        if 'woo_ids' in vals:
            return response
        websites = self.env['website'].search([
            ('is_woo', '=', True),
            ('woo_export_method', '!=', 'manual'),
        ])
        update_fields = list(vals.keys())
        for website in websites:
            self.woo_upload(website, update_fields)
        return response

    def unlink(self):
        woo_ids = {r.id: r.woo_ids_get() for r in self}
        response = super().unlink()
        websites = self.env['website'].search([
            ('is_woo', '=', True),
            ('woo_export_method', '!=', 'manual'),
        ])
        for website in websites:
            delete_ids = [
                woo_ids[r.id][website.id]
                for r in self if website.id in woo_ids[r.id]
            ]
            if not delete_ids:
                continue
            self.woo_delete(website, delete_ids)
        return response

    def _woo_sync_export_get(self, website, products=None):
        to_upload = self.woo_sync_export_records(website, products)
        if products:
            return {
                'upload': to_upload,
                'delete': [],
            }
        to_delete = self.search([
            ('id', 'not in', to_upload.ids),
            '|',
            ('woo_ids', 'like', '{%s:' % website.id),
            ('woo_ids', 'like', ' %s:' % website.id),
        ])
        return {
            'upload': to_upload,
            'delete': to_delete,
        }

    @api.model
    def woo_sync_export(self, website, products=None):
        records = self._woo_sync_export_get(website, products)
        for index, record in enumerate(records['upload']):
            _log.info(
                f'[{index + 1}/{len(records["upload"])}] '
                f'{record._name} "{record.name}" upload to website '
                f'"{website.name}"')
            record.woo_upload(website)
        for index, record in enumerate(records['delete']):
            _log.info(
                f'[{index + 1}/{len(records["delete"])}] '
                f'{record._name} "{record.name}" delete to website '
                f'"{website.name}"')
            record.woo_delete(website)
        return records

    def _woo_sync_import_get(self, website, woo_id=None, params=None):
        if not params:
            params = {}
        datas = res = []
        page = 1
        self = self.with_context(website=website)
        while page == 1 or datas:
            datas = self.woo_rpc_call(
                'get', self.woo_endpoint_get(woo_id),
                {'params': {**params, **{'per_page': 100, 'page': page}}},
                website=website)
            if isinstance(datas, dict):
                datas = [datas]
            for data in datas:
                record = self.woo_search_id(data['id'])
                if not record:
                    res.append(data)
            if not params:
                datas = []
            page += 1
        return res

    def woo_sync_import(self, website, woo_id=None, params=None, datas=None):
        if not params:
            params = {}
        if datas is None:
            datas = self._woo_sync_import_get(
                website, woo_id=woo_id, params=params)
        IrAttachment = self.env['ir.attachment']
        IrModelLog = self.env['ir.model.log']
        log_vals = {
            'website_id': website.id,
            'name': f'Import {self._description}',
            'res_model': self.env.context.get('active_model', self._name),
        }
        log = IrModelLog.get_or_create_log(log_vals)
        res = self.browse()
        for index, data in enumerate(datas):
            name = data.get('number', data.get('name'))
            content = json.dumps(data, indent=4, sort_keys=True)
            log.info(f'[{index + 1}/{len(datas)}] Import {self._name}: {name}')
            try:
                with self.env.cr.savepoint():
                    record = self.woo_sync_import_record(website, data)
                log = IrModelLog.get_or_create_log(log_vals)
                if record:
                    log.add_id(record.id)
            except Exception as ex:
                log = IrModelLog.get_or_create_log(log_vals)
                self = self.with_context(active_log_id=log.id)
                log.exception(ex.args[0], ex)
                log.attach(name, content)
                continue
            if not record:
                continue
            IrAttachment.create({
                'name': f'json_{name}.json',
                'datas': base64.b64encode(content.encode()),
                'res_model': record._name,
                'res_id': record.id,
                'mimetype': 'application/json',
            })
            record.with_context(website=website).woo_set_id(data['id'])
            res |= record
            if not tools.config.get('test_enable'):
                self.env.cr.commit()
        log = IrModelLog.get_or_create_log(log_vals)
        log.finish()
        return res
