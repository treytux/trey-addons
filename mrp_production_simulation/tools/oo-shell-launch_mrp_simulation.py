# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import logging
_log = logging.getLogger(__name__)


# For ignore PEP8 error for self undefined, this script is for odoo shell
if 'self' not in globals():
    self = None

###############################################################################
# SCRIPT PARA PRUEBAS
# Parar detectar los posibles errores del ḿodulo mrp_production_simulation con
# las peculiaridades de la bd de virena, recorremos todas las ordenes de
# fabricacion y lanzamos el asistente de simulacion de fabricacion
###############################################################################

# Desde ordenes de abastecimiento
mrp_productions = self.env['mrp.production'].search([], order='id desc')
count = 0
total_mrps = len(mrp_productions)
for mrp_prod in mrp_productions:
    count += 1
    _log.info('X' * 80)
    _log.info(('Ejecutando mrp [%s/%s]' % (count, total_mrps)))
    _log.info(('Mrp production %s' % mrp_prod))
    _log.info('X' * 80)
    try:
        wiz = self.env['wiz.mrp.simulation'].with_context({
            'active_ids': [mrp_prod.id],
            'active_model': 'mrp.production',
            'active_id': mrp_prod.id}).create({})
        wiz.button_accept()
        self.commit()
    except Exception as e:
        _log.info('X' * 80)
        _log.info(('Excepcion: ', e))
        _log.info('X' * 80)
_log.info('X' * 80)
_log.info('FIN: Simulaciones de fabricacion desde mrp.production ejecutadas.')
_log.info('X' * 80)

# Desde lista de materiales
mrp_boms = self.env['mrp.bom'].search([], order='id desc')
count = 0
total_mrps = len(mrp_boms)
for mrp_prod in mrp_boms:
    count += 1
    _log.info('X' * 80)
    _log.info(('Ejecutando mrp [%s/%s]' % (count, total_mrps)))
    _log.info(('Mrp bom %s' % mrp_prod))
    _log.info('X' * 80)
    try:
        wiz = self.env['wiz.mrp.simulation'].with_context({
            'active_ids': [mrp_prod.id],
            'active_model': 'mrp.bom',
            'active_id': mrp_prod.id}).create({})
        wiz.button_accept()
        self.commit()
    except Exception as e:
        _log.info('X' * 80)
        _log.info(('Excepcion: ', e))
        _log.info('X' * 80)
_log.info('X' * 80)
_log.info('FIN: Simulaciones de fabricacion desde mrp.bom ejecutadas.')
_log.info('X' * 80)
