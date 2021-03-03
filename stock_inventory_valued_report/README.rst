.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock inventory valued report
=============================

Crea un informe para analizar el valor del inventario. El informe es muy útil
cuando el método de cálculo del coste está establecido como FIFO.

Si necesita realizar cambios en los movimientos actuales para aplicar el
método de coste FIFO puede usar el siguiente script de Odoo Shell

```
def recompute(moves):
    moves.product_price_update_before_done()
    for move in moves:
        if move._is_in() and move._is_out():
            raise Exception(
                'The move lines are not in a consistent state: some are '
                'entering and other are leaving the company.')
        company_src = move.mapped('move_line_ids.location_id.company_id')
        company_dst = move.mapped('move_line_ids.location_dest_id.company_id')
        try:
            if company_src:
                company_src.ensure_one()
            if company_dst:
                company_dst.ensure_one()
        except ValueError:
            raise Exception(
                'The move lines are not in a consistent states: they do not '
                'share the same origin or destination company.')
        if company_src and company_dst and company_src.id != company_dst.id:
            raise Exception(
                'The move lines are not in a consistent states: they are '
                'doing an intercompany in a single step while they should '
                'go through the intercompany transit location.')
        move._run_valuation()
    entry_moves = moves.filtered(lambda m: (
        m.product_id.valuation == 'real_time'
        and (
            m._is_in()
            or m._is_out()
            or m._is_dropshipped()
            or m._is_dropshipped_returned()
        )
    ))
    for move in entry_moves:
        move._account_entry_move()
    return moves


print('Update categories method cost to FIFO')
categs = self.env['product.category'].search([])
categs.write({'property_cost_method': 'fifo'})

print('Recompute moves')
moves = self.env['stock.move'].search([], order='date asc')
recompute(moves)
```


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
