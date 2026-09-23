===========================
Stock Barcode Fix User Scope
===========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * ``stock_barcodes`` emite sus notificaciones de bus (``stock_barcodes_scan``,
      ``stock_barcodes_form_update`` y ``stock_barcodes_kanban_update``) como
      canales globales de texto. Toda sesión que tenga abierta una vista de un
      modelo "barcode" (albarán, tipo de operación, asistentes de lectura...)
      queda suscrita a esos canales, por lo que cualquier usuario recibe los
      avisos de los escaneos y ajustes de inventario de los demás.

    * El síntoma más visible es que, cuando un usuario o un proceso automático
      (por ejemplo la sincronización de stock de KAIS) aplica un ajuste de
      inventario, a cualquier compañero que tenga abierto un albarán se le
      redirige a la vista "Barcodes" a pantalla completa sin haber hecho nada.

    * Este módulo reencamina esas notificaciones al ``res.partner`` del usuario
      que ejecuta la acción. Cada sesión autenticada está suscrita a su propio
      partner, así que el aviso sigue llegando a quien realiza el escaneo o el
      ajuste y deja de llegar al resto de usuarios.

    * No cambia el comportamiento del flujo de códigos de barras: quien aplica
      el inventario desde el asistente sigue volviendo al menú de "Barcodes".

**Tabla de contenidos**

.. contents::
   :local:


Configuración
~~~~~~~~~~~~~

No requiere configuración. Basta con instalar el módulo.


Autor
~~~~~

* `Trey <https://www.trey.es>`__
