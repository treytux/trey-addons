.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================================
Account Analytic Line Sale Salesman
===================================

- Añade el campo `sale_user_id` (comercial del pedido de venta) como campo
  almacenado en las líneas analíticas, para poder filtrar, agrupar y pivotar
  por comercial.

Cómo se determina el comercial
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

El campo `sale_user_id` se calcula a partir de la cuenta analítica de la línea
analítica (`account_id`): se busca el pedido de venta cuya cuenta analítica
(`sale.order.analytic_account_id`) coincide con la de la línea y se toma su
comercial (`user_id`).

Funcionamiento:

* La línea analítica queda vinculada al pedido de venta a través de su cuenta
  analítica (`account_id` -> `sale.order.analytic_account_id`), no a través de
  la línea de pedido (`so_line`).
* Si no existe ningún pedido de venta con esa cuenta analítica, o la línea
  analítica no tiene cuenta (`account_id`), el valor de `sale_user_id` es vacío.

Motivo de la decisión
~~~~~~~~~~~~~~~~~~~~~

La cuenta analítica se crea desde el pedido de venta y se asume que no puede
haber dos pedidos de venta con la misma cuenta analítica: cada pedido de venta
genera su propia cuenta analítica cuando se confirma. Por tanto, la cuenta
analítica identifica de forma inequívoca un único pedido de venta y, con él, a
su comercial.

Enlazar por la cuenta analítica en lugar de por la línea de pedido tiene dos
ventajas:

* Es más robusto: no depende de que el apunte analítico tenga seteada la línea
  de pedido (`so_line`). Muchos apuntes analíticos generados por el sistema
  referencian la cuenta analítica pero no la línea de pedido, y con el enfoque
  anterior el comercial quedaba vacío o se enlazaba mal.
* Resulta suficiente: como la cuenta analítica es única por pedido, buscar por
  ella devuelve un único pedido y la resolución es determinista.

Autor
~~~~~

* `Trey <https://www.trey.es>`__: