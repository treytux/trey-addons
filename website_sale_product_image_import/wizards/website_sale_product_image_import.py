###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging
import re
import zipfile
from collections import defaultdict

from odoo import _, fields, models
from odoo.exceptions import UserError
from PIL import Image

_logger = logging.getLogger(__name__)


class WebsitesaleProductImageImport(models.TransientModel):
    _name = 'website.sale.product.image.import'
    _description = 'Product Image Import Wizard'

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('validated', 'Validated'),
            ('done', 'Done'),
        ],
        default='draft',
        required=True,
    )
    zip_file = fields.Binary(
        string='ZIP File',
        required=True,
    )
    image_destination = fields.Selection(
        selection=[
            ('template', 'Product template'),
            ('variant', 'Product variant'),
        ],
        string='Image destination',
        default='template',
        required=True,
    )
    filename = fields.Char(
        string='Filename',
    )
    summary = fields.Text(
        string='Summary',
        readonly=True,
    )
    loaded_images = fields.Text(
        string='Image results',
        readonly=True,
    )
    not_found_references = fields.Text(
        string='References not found',
        readonly=True,
    )
    invalid_files = fields.Text(
        string='Incorrect filenames',
        readonly=True,
    )
    errors = fields.Text(
        string='Processing errors',
        readonly=True,
    )
    loaded_count = fields.Integer(
        string='Processed images',
        readonly=True,
    )
    loaded_product_count = fields.Integer(
        string='Processed products',
        readonly=True,
    )
    not_found_count = fields.Integer(
        string='References not found',
        readonly=True,
    )
    invalid_count = fields.Integer(
        string='Invalid files',
        readonly=True,
    )
    error_count = fields.Integer(
        string='Errors',
        readonly=True,
    )

    def action_validate(self):
        self.ensure_one()
        return self._process_import(False)

    def action_import(self):
        self.ensure_one()
        return self._process_import(True)

    def _process_import(self, apply_changes):
        self.ensure_one()
        if not self.zip_file:
            raise UserError(_('Please select a ZIP file.'))
        self._clear_result()
        try:
            archive_data = base64.b64decode(self.zip_file)
            archive = zipfile.ZipFile(io.BytesIO(archive_data))
        except (ValueError, zipfile.BadZipFile) as error:
            raise UserError(
                _('The selected file is not a valid ZIP archive.')) from error
        archive_result = self._read_archive(archive)
        grouped_files, invalid_files, invalid_references = archive_result
        loaded = []
        loaded_products = 0
        loaded_image_count = 0
        not_found = []
        errors = []
        references = sorted(set(grouped_files) | invalid_references)
        product_model = self.env['product.product'].with_company(
            self.env.company).with_context(active_test=True)
        products_by_reference = defaultdict(list)
        products = product_model.search([
            ('default_code', 'in', references),
            ('company_id', '=', self.env.company.id),
        ])
        for product in products:
            products_by_reference[product.default_code].append(product)
        conflicting_references = set()
        if self.image_destination == 'template':
            conflicts = self._get_template_reference_conflicts(
                products_by_reference)
            for template, template_references in conflicts:
                conflicting_references.update(template_references)
                errors.append(_(
                    'Product template %(template)s (ID %(id)s): multiple '
                    'ZIP references target this template: %(references)s. '
                    'This template is skipped.',
                    template=template.display_name, id=template.id,
                    references=', '.join(template_references)))
        for reference in references:
            files = grouped_files.get(reference, {})
            if not files and reference in invalid_references:
                continue
            numbering_error = self._validate_numbering(files)
            if numbering_error:
                invalid_files.append('%s: %s' % (reference, numbering_error))
                continue
            if reference in invalid_references:
                continue
            if reference in conflicting_references:
                continue
            products = products_by_reference.get(reference, [])
            if not products:
                not_found.append(_(
                    '%(reference)s: no active product found with this exact '
                    'internal reference in company %(company)s.',
                    reference=reference, company=self.env.company.display_name))
                continue
            templates = products[0].product_tmpl_id.browse(
                list(set(product.product_tmpl_id.id for product in products)))
            if self.image_destination == 'template' and len(templates) > 1:
                errors.append(_(
                    '%(reference)s: the internal reference belongs to '
                    'multiple product templates: %(templates)s',
                    reference=reference,
                    templates=', '.join(
                        'ID %s' % template.id for template in templates)))
                continue
            if self.image_destination == 'variant' and len(products) > 1:
                errors.append(_(
                    '%(reference)s: multiple active products have this '
                    'internal reference: %(products)s',
                    reference=reference,
                    products=self._format_product_details(products)))
                continue
            try:
                with self.env.cr.savepoint():
                    if apply_changes:
                        self._replace_product_images(
                            products[0] if self.image_destination == 'variant'
                            else templates[0], files, self.image_destination)
                values = {
                    'reference': reference,
                    'count': len(files),
                    'target': self._get_load_target(
                        products[0] if self.image_destination == 'variant'
                        else templates[0], self.image_destination),
                    'files': ', '.join(item[0] for item in files.values()),
                }
                if apply_changes:
                    loaded.append(_(
                        '%(reference)s: %(count)s images loaded for '
                        '%(target)s (%(files)s)', **values))
                else:
                    loaded.append(_(
                        '%(reference)s: %(count)s images validated for '
                        '%(target)s (%(files)s)', **values))
                loaded_products += 1
                loaded_image_count += len(files)
            except Exception as error:
                log_message = 'Could not import images for product %s.'
                _logger.exception(log_message, reference)
                errors.append(_(
                    '%(reference)s: could not update %(products)s: %(error)s',
                    reference=reference,
                    products=self._format_product_details(products),
                    error=str(error)))
        summary = self._get_summary(
            loaded_products, loaded_image_count, len(not_found),
            len(invalid_files), len(errors), apply_changes=apply_changes)
        self.write({
            'state': 'done' if apply_changes else 'validated',
            'summary': summary,
            'loaded_images': self._format_lines(loaded),
            'not_found_references': self._format_lines(not_found),
            'invalid_files': self._format_lines(invalid_files),
            'errors': self._format_lines(errors),
            'loaded_count': loaded_image_count,
            'loaded_product_count': loaded_products,
            'not_found_count': len(not_found),
            'invalid_count': len(invalid_files),
            'error_count': len(errors),
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product Image Import Result'),
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {
                'import_done': apply_changes,
                'validation_done': not apply_changes,
            },
        }

    def _get_template_reference_conflicts(self, products_by_reference):
        references_by_template = defaultdict(set)
        for reference, products in products_by_reference.items():
            templates = {product.product_tmpl_id for product in products}
            if len(templates) == 1:
                template = next(iter(templates))
                references_by_template[template].add(reference)
        return [
            (template, sorted(references))
            for template, references in sorted(
                references_by_template.items(), key=lambda item: item[0].id)
            if len(references) > 1
        ]

    def _clear_result(self):
        self.write({
            'state': 'draft',
            'summary': False,
            'loaded_images': False,
            'not_found_references': False,
            'invalid_files': False,
            'errors': False,
            'loaded_count': 0,
            'loaded_product_count': 0,
            'not_found_count': 0,
            'invalid_count': 0,
            'error_count': 0,
        })

    def _read_archive(self, archive):
        grouped_files = defaultdict(dict)
        invalid_files = []
        invalid_references = set()
        entries = [item for item in archive.infolist() if not item.is_dir()]
        _filename_pattern = re.compile(r'^(.+)-(\d+)\.([^.]+)$', re.IGNORECASE)
        _accepted_extensions = {'jpg', 'jpeg', 'png', 'webp'}
        if not entries:
            raise UserError(_('The ZIP file does not contain any files.'))
        for item in entries:
            name = item.filename
            match = _filename_pattern.match(name)
            if not match:
                invalid_files.append(name)
                continue
            reference, number_text, extension = match.groups()
            extension = extension.lower()
            number = int(number_text)
            if extension not in _accepted_extensions or number < 1:
                invalid_files.append(name)
                invalid_references.add(reference)
                continue
            try:
                content = archive.read(item)
                self._validate_image(content)
            except Exception as error:
                invalid_references.add(reference)
                invalid_files.append('%s: %s' % (name, str(error)))
                continue
            if number in grouped_files[reference]:
                invalid_references.add(reference)
                duplicate_message = _(
                    '%(reference)s: duplicate image number %(number)s.',
                    reference=reference, number=number)
                invalid_files.append(duplicate_message)
            grouped_files[reference][number] = (name, content)
        return grouped_files, invalid_files, invalid_references

    def _validate_image(self, content):
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
        except Exception as error:
            raise UserError(_('The file is not a valid image.')) from error

    def _validate_numbering(self, files):
        numbers = sorted(files)
        if not numbers or numbers[0] != 1:
            return _('Image number 1 is required.')
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            return _('Image numbering must be consecutive.')
        return False

    def _replace_product_images(self, record, files, image_destination):
        template = (
            record if image_destination == 'template'
            else record.product_tmpl_id)
        if image_destination == 'template':
            template.product_template_image_ids.unlink()
            template.write({
                'image_1920': base64.b64encode(files[1][1]),
            })
            image_field = 'product_tmpl_id'
        else:
            record.product_variant_image_ids.unlink()
            record.write({
                'image_variant_1920': base64.b64encode(files[1][1]),
            })
            image_field = 'product_variant_id'
        extra_values = [{
            'name': files[number][0],
            'sequence': (number - 1) * 10,
            'image_1920': base64.b64encode(files[number][1]),
            image_field: template.id if image_destination == 'template'
            else record.id,
        } for number in sorted(files) if number > 1]
        if extra_values:
            self.env['product.image'].create(extra_values)

    @staticmethod
    def _format_lines(lines):
        return '\n'.join(lines) or False

    def _format_product_details(self, products):
        return '; '.join(
            _(
                'ID %(id)s, %(name)s, company %(company)s, %(status)s',
                id=product.id, name=product.display_name,
                company=product.company_id.display_name or _('Global'),
                status=_('active') if product.active else _('archived'))
            for product in products)

    def _get_load_target(self, record, image_destination):
        if image_destination == 'template':
            return _('product template ID %(id)s', id=record.id)
        return _('product variant ID %(id)s', id=record.id)

    def _get_summary(
            self, loaded_products, loaded, not_found, invalid, errors,
            apply_changes=True):
        values = {
            'loaded_products': loaded_products,
            'loaded': loaded,
            'not_found': not_found,
            'invalid': invalid,
            'errors': errors,
        }
        if not apply_changes:
            return _(
                'Products validated: %(loaded_products)s\n'
                'Images validated: %(loaded)s\n'
                'References not found: %(not_found)s\n'
                'Invalid files: %(invalid)s\n'
                'Errors: %(errors)s', **values)
        return _(
            'Products loaded: %(loaded_products)s\n'
            'Images loaded: %(loaded)s\n'
            'References not found: %(not_found)s\n'
            'Invalid files: %(invalid)s\n'
            'Errors: %(errors)s', **values)
