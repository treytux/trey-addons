###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.queue_job.exception import FailedJobError
except ImportError:
    _logger.debug('Can not `import queue_job`.')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def cron_ede_update_product_prices(self, domain=None):
        company = self.env.user.company_id
        ede_supplier = company.ede_supplier_id
        if not ede_supplier:
            raise ValidationError(_('EDE supplier not configured'))
        product_templates = self.search([
            ('seller_ids.name', '=', ede_supplier.id),
            ('barcode', '!=', ''),
        ] + (domain or []), order='id desc')
        if not product_templates:
            raise ValidationError(_('No products found with EDE supplier'))
        _logger.info(
            'Creating EDE update price jobs for %s product templates' % (
                len(product_templates)))
        batch = company.ede_batch_size
        queue_job_obj = self.env['queue.job']
        for count, start in enumerate(range(0, len(product_templates), batch)):
            product_templates_batch = product_templates[start:start + batch]
            _logger.info(
                'PROCESS: Creating EDE update price job for product templates: '
                '%s-%s of %s' % (
                    count + 1, min(count + 1, batch), len(product_templates)))
            last_queue_job = queue_job_obj.search([
                ('model_name', '=', 'product.template'),
                ('method_name', '=', 'job_ede_update_price'),
                ('channel', '=', 'root.ede_prices'),
            ], order='date_created desc', limit=1)
            start_date = (last_queue_job and (
                last_queue_job.date_created
                + timedelta(minutes=count * company.ede_delay_between_requests)
            ) or fields.Datetime.now())
            product_templates_batch.with_delay(
                channel='root.ede_prices', eta=start_date
            ).job_ede_update_price()
        _logger.info(
            'FINISHED: EDE update price jobs created for %s product templates'
            % len(product_templates))
        return True

    def update_product_price_ede(
            self, sequence, supplier_info, simulation_prices, log_msgs):
        _logger.info(
            '%s EDE price update for product %s with barcode %s' % (
                sequence,
                supplier_info.product_id.display_name
                or supplier_info.product_tmpl_id.display_name,
                supplier_info.product_id.barcode
                or supplier_info.product_tmpl_id.barcode))
        sline = simulation_prices.get(sequence)
        if sline is None:
            log_msgs.append(_(
                'ERROR: EDE not return data for barcode: %s') % (
                supplier_info.product_id.barcode
                or supplier_info.product_tmpl_id.barcode))
            return log_msgs
        price = float(sline.find('Price').text)
        price_units = float(sline.find('PriceUnit').text)
        if price_units != 1:
            price = price / price_units
        price_previous = supplier_info.price
        if float_compare(supplier_info.price, price, 2) == 0:
            log_msgs.append(_(
                'INFO: EDE price not changed for product %s, price: %s') % (
                    supplier_info.product_id.display_name
                    or supplier_info.product_tmpl_id.display_name, price))
            return log_msgs
        lst_price_previous = (
            supplier_info.product_id and supplier_info.product_id.lst_price
            or supplier_info.product_tmpl_id.lst_price)
        supplier_info.price = price
        if supplier_info.product_id:
            supplier_info.product_id.sudo().lst_price = lst_price_previous
        else:
            supplier_info.product_tmpl_id.sudo().product_variant_ids.write({
                'lst_price': lst_price_previous
            })
        log_msgs.append(_(
            'INFO: EDE price updated for product %s, price old: %s, price '
            'new: %s') % (
                supplier_info.product_id.display_name
                or supplier_info.product_tmpl_id.display_name,
                price_previous, price))
        return log_msgs

    def job_ede_update_price(self):
        log_msgs = []
        company = self.env.user.company_id
        ede_supplier = company.ede_supplier_id
        if not ede_supplier:
            raise FailedJobError(_('EDE supplier not configured'))
        items = []
        supplier_info_by_sequence = {}
        for sequence, product in enumerate(self):
            supplier_infos = product.seller_ids.filtered(
                lambda seller: seller.name == ede_supplier)
            if not supplier_infos:
                log_msgs.append(_(
                    'ERROR: No EDE supplier info found for product: %s') % (
                        product.display_name))
                continue
            elif len(supplier_infos) > 1:
                log_msgs.append(_(
                    'ERROR: Multiple EDE supplier info found for product: %s '
                    'selected the first one') % product.display_name)
                supplier_infos = supplier_infos[:1]
                continue
            product = (
                supplier_infos.product_id or supplier_infos.product_tmpl_id)
            if not product.barcode:
                log_msgs.append(_(
                    'ERROR: Skip EDE price update for product %s because it has'
                    ' no barcode') % product.display_name)
                continue
            items.append({
                'ID': sequence,
                'ProductID': product.barcode,
                'Quantity': supplier_infos.min_qty or 1,
                'Date': fields.Datetime.now(),
            })
            supplier_info_by_sequence[sequence] = supplier_infos
        ede = company.ede_client()
        client = ede.wsd_connection()
        payload = {
            'ShipmentTypeCode': '13',
            'Items': {
                'Item': items,
            },
        }
        credentials = company.ede_credentials()
        simulation = ede.simulate_order(
            client=client, credentials=credentials, payload=payload)
        if simulation is None:
            raise FailedJobError(_('EDE not return data'))
        slines = simulation.findall(
            './/SalesOrderSimulateConfirmation/Items/Item')
        if not len(slines):
            raise FailedJobError(_('EDE not return data'))
        simulation_prices = {
            int(sline.find('ID').text): sline for sline in slines
        }
        for sequence, supplier_info in supplier_info_by_sequence.items():
            log_msgs = self.update_product_price_ede(
                sequence, supplier_info, simulation_prices, log_msgs)
        return '\n'.join(log_msgs)
