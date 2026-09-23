###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import re
import threading

import requests
from bs4 import BeautifulSoup
from odoo import fields, models

_log = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_read_product(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.product',
            'res_id': self.id,
        }

    def _clean_isbn(self, isbn):
        return ''.join(filter(str.isalnum, isbn))

    def search_or_create_product_by_isbn(self, isbn):
        isbn = self._clean_isbn(isbn)
        barcode = self.env['product.barcode'].search([('name', '=', isbn)])
        if barcode:
            return barcode.product_id
        vals = self.request_isbn_info(isbn)
        if not vals:
            return False
        barcode = self.env['product.barcode'].search(
            [('name', 'in', [b[2]['name'] for b in vals['barcode_ids']])])
        if barcode:
            return barcode.product_id
        return self.create(vals)

    def update_product_by_isbn(self, isbn):
        self.ensure_one()
        isbn = self._clean_isbn(isbn)
        vals = self.request_isbn_info(isbn)
        if not vals:
            return False
        barcodes = self.barcode_ids.mapped('name')
        vals['barcode_ids'] = [
            b for b in vals['barcode_ids'] if b[2]['name'] not in barcodes]
        if not vals['barcode_ids']:
            del vals['barcode_ids']
        return self.write(vals)

    def request_isbn_info(self, isbn):
        isbn = self._clean_isbn(isbn)
        data = {}

        def fetch_from_googleapi():
            data['googleapi'] = self._request_isbn_from_googleapi(isbn)

        def fetch_from_openlibrary():
            data['openlibrary'] = self._request_isbn_from_openlibrary(isbn)

        def fetch_from_isbndb():
            data['isbndb'] = self._request_isbn_from_isbndb(isbn)

        def fetch_from_cultura_gob_es():
            data['isbndb'] = self._request_isbn_from_cultura_gob_es(isbn)

        def fetch_from_dnb_de():
            data['isbndb'] = self._request_isbn_from_dnb_de(isbn)

        threads = [
            threading.Thread(target=fetch_from_googleapi),
            threading.Thread(target=fetch_from_openlibrary),
            threading.Thread(target=fetch_from_isbndb),
            threading.Thread(target=fetch_from_cultura_gob_es),
            threading.Thread(target=fetch_from_dnb_de),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        vals = {}
        for api_name, info in data.items():
            if 'error' in info:
                continue
            for key in info.keys():
                if key in vals:
                    continue
                if isinstance(info[key], list):
                    try:
                        vals[key] = ', '.join(info[key])
                    except Exception as e:
                        _log.error(
                            f'Error joining list for api {api_name} and key '
                            f'{key}: {e}')
                        raise e
                else:
                    vals[key] = info[key]
        if not vals:
            return False
        return {
            'name': vals.get('title'),
            'barcode_ids': [(0, 0, {'name': isbn})],
            'type': 'product',
            'description_sale': vals.get('description'),
            'authors': vals.get('authors'),
            'categories': vals.get('categories'),
            'description': vals.get('description'),
            'language': vals.get('language'),
            'page_count': vals.get('page_count'),
            'published_date': vals.get('published_date'),
            'publishers': vals.get('publishers'),
        }

    def _safe_request(self, url, headers=None):
        try:
            response = requests.get(
                url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {e}'}

    def _request_isbn_from_googleapi(self, isbn):
        response = self._safe_request(
            f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
        )
        if isinstance(response, dict):
            return response
        data = response.json()
        if 'items' not in data:
            return {'error': 'Book not found'}
        info = data['items'][0]['volumeInfo']
        published_date = info.get('publishedDate')
        try:
            published_date = (
                fields.Date.to_date(info.get('publishedDate'))
                if info.get('publishedDate') else False
            )
        except Exception:
            published_date = info.get('publishedDate')
        return {
            'title': info.get('title'),
            'authors': info.get('authors', []),
            'categories': info.get('categories'),
            'description': info.get('description'),
            'barcodes': [
                b['identifier'][0]
                for b in info.get('industryIdentifiers', [])
            ],
            'language': info.get('language'),
            'page_count': info.get('pageCount'),
            'published_date': published_date,
            'publishers': info.get('publishers'),
        }

    def _request_isbn_from_openlibrary(self, isbn):
        response = self._safe_request(
            f'https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&'
            'format=json&jscmd=data'
        )
        if isinstance(response, dict):
            return response
        data = response.json()
        if f'ISBN:{isbn}' not in data:
            return {'error': 'Book not found'}
        info = data[f'ISBN:{isbn}']
        published_date = info.get('publishedDate')
        try:
            published_date = (
                fields.Date.to_date(
                    info.get('publishedDate').replace('\\', '-')
                ) if info.get('publishedDate') else False
            )
        except Exception:
            published_date = info.get('publishedDate')
        return {
            'title': info.get('title'),
            'authors': [a['name'] for a in info.get('authors', [])],
            'categories': info.get('categories'),
            'description': info.get('description'),
            'barcodes': [b[0] for b in info.get('identifiers', []).values()],
            'language': info.get('language'),
            'page_count': info.get('pageCount'),
            'published_date': published_date,
            'publishers': [p['name'] for p in info.get('publishers', [])],
        }

    def _request_isbn_from_isbndb(self, isbn):
        isbndb_token = self.env['ir.config_parameter'].get_param(
            'isbndb_token', default='57816_6334ea3c435b4dd68c92e420a129fc3e')
        response = self._safe_request(
            f'https://api2.isbndb.com/book/{isbn}',
            headers={
                'Authorization': isbndb_token,
                'Accept': 'application/json',
            }
        )
        info = response.json().get('book', {})
        published_date = info.get('publishedDate')
        try:
            published_date = (
                fields.Date.to_date(info.get('publishedDate'))
                if info.get('publishedDate') else False
            )
        except Exception:
            published_date = info.get('publishedDate')
        barcodes = [
            info.get('isbn13'),
            info.get('isbn10'),
        ]
        return {
            'title': info.get('title'),
            'authors': [a for a in info.get('authors', [])],
            'categories': ', '.join(info.get('subjects', [])),
            'description': info.get('description'),
            'barcodes': [b[0] for b in barcodes if b],
            'language': info.get('language'),
            'page_count': info.get('pages'),
            'published_date': published_date,
            'publisher': info.get('publisher'),
        }

    def _request_isbn_from_cultura_gob_es(self, isbn):
        def title_ok(response):
            soup = BeautifulSoup(response.text, 'html.parser')
            title = (
                soup.select('title')[0].get_text(strip=True)
                if soup.select('title') else ''
            )
            if '' == title or 'no encontrada' in title:
                return False
            return True

        with requests.Session() as session:
            res_hi = session.get(
                'https://www.cultura.gob.es/webISBN/tituloSimpleFilter.do'
                '?cache=init&layout=busquedaisbn&language=es',
                verify=False)
            if not title_ok(res_hi):
                return {'error': 'Book not found, request hi failed'}
            data = {
                'params.forzaQuery': 'N',
                'params.cdispo': 'A',
                'params.cisbnExt': isbn,
                'params.orderByFormId': 1,
                'action': 'Buscar',
                'language': 'es',
                'prev_layout': 'busquedaisbn',
                'layout': 'busquedaisbn',
            }
            res_search = session.post(
                'https://www.cultura.gob.es/webISBN/tituloSimpleDispatch.do',
                data=data, verify=False)
            if not title_ok(res_search):
                return {'error': 'Book not found, request search failed'}
            soup = BeautifulSoup(res_search.text, 'html.parser')
            links = soup.select(
                'a[href^="/webISBN/tituloDetalle.do?sidTitul="]')
            if not links:
                return {'error': 'Book not found, no links found'}
            link = links[0]
            res_detail = session.get(
                f'https://www.cultura.gob.es{link["href"]}', verify=False)
            if not title_ok(res_detail):
                return {'error': 'Book not found, request detail failed'}
        soup = BeautifulSoup(res_detail.text, 'html.parser')
        result = {}
        table = soup.find('table')
        for row in table.find_all('tr'):
            key = row.find_all('th')[0].get_text(strip=True)
            key = key.lower().replace(':', '')
            value = row.find_all('td')[0].get_text(strip=True)
            result[key] = value

        def clean_text(value):
            if not value:
                return None
            value = re.sub(r'\[.*?\]', ', ', value)
            value = re.sub(r'\s+', ' ', value).strip()
            value = value.replace('\xa0', ' ')
            return value.strip()

        return {
            'title': clean_text(result.get('título')),
            'authors': clean_text(result.get('autor/es')),
            'categories': clean_text(result.get('materia/s')),
            'description': clean_text(result.get('descripción')),
            'barcodes': [isbn],
            'language': clean_text(result.get('lengua de publicación')),
            'page_count': (
                result.get('descripción').split(' ')[0]
                if 'descripción' in result else None
            ),
            'published_date': clean_text(result.get('fecha edición')),
            'publisher': clean_text(result.get('publicación')),
        }

    def _request_isbn_from_dnb_de(self, isbn):
        res = requests.get(
            f'https://portal.dnb.de/opac/simpleSearch?query={isbn}',
            verify=False)
        if 'im Bestand: Gesamter Bestand' in res.text:
            return {'error': 'Book not found'}
        soup = BeautifulSoup(res.text, 'html.parser')
        result = {}
        table = soup.find('table', id='fullRecordTable')
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) != 2:
                continue
            key = cols[0].get_text(strip=True).lower()
            value = cols[1].get_text(strip=True)
            result[key] = value

        def clean_text(value):
            if not value:
                return None
            value = re.sub(r'\[.*?\]', '', value)
            value = re.sub(r'\s+', ' ', value).strip()
            return [
                value.strip() for value in value.split(';') if value.strip()]

        return {
            'title': clean_text(result.get('titel')),
            'authors': clean_text(result.get('person(en)')),
            'categories': clean_text(result.get('sachgruppe(n)')),
            'description': '',
            'barcodes': [isbn],
            'language': '',
            'page_count': clean_text(result.get('umfang/format')),
            'published_date': clean_text(result.get('zeitliche einordnung')),
            'publisher': clean_text(result.get('verlag')),
        }
