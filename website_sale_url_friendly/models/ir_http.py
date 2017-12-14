# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp.osv import orm
import logging
_log = logging.getLogger(__name__)


class SlugManager(orm.AbstractModel):
    _inherit = 'ir.http'

    def __init__(self, *args, **kwargs):
        super(SlugManager, self).__init__(*args, **kwargs)
        self.FORBIDDEN_PATHS.append('/shop')
        self.FORBIDDEN_PATHS.append('/shop/product')
        self.FORBIDDEN_PATHS.append('/shop/category')

    def compute_path(self, path):
        computed_path = None

        # Slicing setting directly the pattern (no var stored) is the fastest
        # method to search than find and startswith
        if path[:len('/shop/product/')] == '/shop/product/':
            ids = self._find_ids_in_path('/shop/product/<slug>', path)
            if not ids:
                ids = self._find_ids_in_path('/shop/product/<id>', path)
            if ids:
                computed_path = u'/shop/product/{}'.format(ids[0])

        # Slicing setting directly the pattern (no var stored) is the fastest
        # method to search than find and startswith
        if path[:len('/shop/category/')] == '/shop/category/':
            ids = self._find_ids_in_path('/shop/category/<slug>', path)
            if not ids:
                ids = self._find_ids_in_path('/shop/category/<id>', path)
            if ids:
                computed_path = u'/shop/category/{}'.format(ids[0])

        return (
            computed_path
            if computed_path
            else super(SlugManager, self).compute_path(path))
