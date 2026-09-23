###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def cron_reyher_update_product_prices(self, domain=None):
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'reyher'),
        ], limit=1)
        reyher_supplier = connector.supplier_id
        if not connector or not reyher_supplier:
            raise ValidationError(_('Reyher supplier not configured'))
        daily_limit = connector.daily_limit_reyher * connector.reyher_batch_size
        product_templates = self.search([
            ('seller_ids.partner_id', '=', connector.supplier_id.id),
        ] + (domain or []), order='id desc', limit=daily_limit)
        if not product_templates:
            raise ValidationError(_('No products found with Reyher supplier'))
        _logger.info(
            'Creating Reyher update price jobs for %s product templates' % (
                len(product_templates)))
        batch = connector.reyher_batch_size
        queue_job_obj = self.env['queue.job']
        for count, start in enumerate(range(0, len(product_templates), batch)):
            product_templates_batch = product_templates[start:start + batch]
            _logger.info(
                'PROCESS: Creating Reyher update price job for products: '
                '%s-%s of %s' % (
                    count + 1, min(count + 1, batch), len(product_templates)))
            last_queue_job = queue_job_obj.search([
                ('model_name', '=', 'product.template'),
                ('method_name', '=', 'job_reyher_update_price'),
                ('channel', '=', 'root.reyher_prices'),
            ], order='date_created desc', limit=1)
            start_date = (last_queue_job and (
                last_queue_job.date_created
                + timedelta(
                    minutes=count * connector.reyher_delay_between_requests)
            ) or fields.Datetime.now())
            product_templates_batch.with_delay(
                channel='root.reyher_prices', eta=start_date
            ).job_reyher_update_price()
        _logger.info(
            'FINISHED: Reyher update price jobs created for %s products' % len(
                product_templates))
        return True

    def update_product_price_reyher(self, supplier_info, item, log_msgs):
        price_previous = supplier_info.price
        price_reyher = item.get('Price')
        if not price_reyher:
            log_msgs.append(_(
                'ERROR: No price obtained by API Reyher for product %s'
                ' with code %s') % (
                    supplier_info.product_id.display_name
                    or supplier_info.product_tmpl_id.display_name,
                    supplier_info.product_code))
        elif float_compare(
                supplier_info.price, price_reyher / 100, 2) == 0:
            log_msgs.append(_(
                'INFO: Reyher price not changed for product %s, price: %s') % (
                    supplier_info.product_id.display_name
                    or supplier_info.product_tmpl_id.display_name,
                    price_reyher / 100))
        else:
            supplier_info.price = price_reyher / 100
            log_msgs.append(_(
                'INFO: Reyher price updated for product %s, price old: %s, '
                'price new: %s') % (
                    supplier_info.product_id.display_name
                    or supplier_info.product_tmpl_id.display_name,
                    price_previous, price_reyher / 100))
        return log_msgs

    def job_reyher_update_price(self):
        log_msgs = []
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'reyher'),
        ], limit=1)
        reyher_supplier = connector.supplier_id
        if not connector or not reyher_supplier:
            raise ValidationError(_('Reyher supplier not configured'))
        data = {
            'items': [],
        }
        supplier_info_by_sequence = {}
        for sequence, product in enumerate(self, start=1):
            supplier_infos = product.seller_ids.filtered(
                lambda seller: seller.partner_id == reyher_supplier)
            if not supplier_infos:
                log_msgs.append(_(
                    'ERROR: No Reyher supplier info found for product: %s') % (
                        product.display_name))
                continue
            elif len(supplier_infos) > 1:
                log_msgs.append(_(
                    'ERROR: Multiple Reyher supplier info found for product: %s'
                    ' selected the first one') % product.display_name)
                supplier_infos = supplier_infos[:1]
                continue
            product = (
                supplier_infos.product_id or supplier_infos.product_tmpl_id)
            product_code = supplier_infos.product_code
            if not product_code:
                log_msgs.append(_(
                    'ERROR: Skip Reyher price update for product %s because it '
                    'has no product code') % product.display_name)
                continue
            try:
                int(product_code)
            except ValueError:
                log_msgs.append(_(
                    'ERROR: Invalid Reyher code for product %s') % (
                        product.display_name))
                continue
            if len(product_code) < 18:
                log_msgs.append(_(
                    'ERROR: Reyher code for product %s is too short') % (
                        product.display_name))
                continue
            data['items'].append({
                'position': sequence,
                'sku': str(product_code),
                'quantity': supplier_infos.min_qty or 1,
            })
            supplier_info_by_sequence[sequence] = supplier_infos
        content = connector.reyher_get_order_simulate(data)
        if type(content) is not list or content[0].get('StatusCode') != 0:
            raise ValidationError(_(
                'Error when obtaining prices from API Reyher: %s') % (
                    content[0].get('StatusCode', content)
                    if type(content) is list else content))
        for item in content[0].get('Payload', {}).get('Items', []):
            supplier_info = supplier_info_by_sequence[item['Position']]
            log_msgs = self.update_product_price_reyher(
                supplier_info, item, log_msgs)
        return '\n'.join(log_msgs)
