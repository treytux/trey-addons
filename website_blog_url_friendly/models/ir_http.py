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
        self.FORBIDDEN_PATHS.append('/blog')

    def compute_path(self, path):
        computed_path = None

        # Slicing setting directly the pattern (no var stored) is the fastest
        # method to search than find and startswith
        if path[:len('/blog/')] == '/blog/':
            ids = self._find_ids_in_path('/blog/<slug>/post/<slug>', path)
            if not ids:
                ids = self._find_ids_in_path('/blog/<id>/post/<id>', path)
            if ids:
                computed_path = u'/blog/{}/post/{}'.format(ids[0], ids[1])

            ids = self._find_ids_in_path('/blog/<slug>/tag/<slug>', path)
            if not ids:
                ids = self._find_ids_in_path('/blog/<id>/tag/<id>', path)
            if ids:
                computed_path = u'/blog/{}/tag/{}'.format(ids[0], ids[1])

            ids = self._find_ids_in_path('/blog/<slug>', path)
            if not ids:
                ids = self._find_ids_in_path('/blog/<id>', path)
            if ids:
                computed_path = u'/blog/{}'.format(ids[0])

        return (
            computed_path
            if computed_path
            else super(SlugManager, self).compute_path(path))
