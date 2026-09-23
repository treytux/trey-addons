========================
Account Invoice Warnings
========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Muestra avisos en el formulario de la factura sin bloquear el flujo de
trabajo.

Características
~~~~~~~~~~~~~~~

* Muestra avisos visuales en el formulario de las facturas y abonos de
  clientes y proveedores.
* Comprueba si todas las líneas de factura tienen impuestos asignados.
* Comprueba si falta el IVA del contacto, teniendo en cuenta los clientes
  anónimos de efectivo.
* Comprueba si las cuentas contables de las líneas corresponden al tipo de
  factura: cuentas que empiezan por ``7`` para ventas y por ``6`` para
  compras.
* Los avisos son informativos y no impiden guardar, confirmar ni modificar
  la factura.


**Tabla de contenidos**

.. contents::
   :local:

Configuración
~~~~~~~~~~~~~

Después de instalar el módulo, abre la configuración de la compañía y busca
el grupo **Invoice Warnings**. Activa las comprobaciones que quieras mostrar
en los formularios de factura:

* **Show Wrong Accounts Warning**: avisa cuando las cuentas de las líneas no
  coinciden con el tipo de factura.
* **Show Wrong Taxes Warning**: avisa cuando alguna línea no tiene impuestos.
* **Show Wrong VAT Warning**: avisa cuando el contacto no tiene IVA.

Uso
~~~

Con las comprobaciones activadas, los avisos aparecen automáticamente en la
parte superior del formulario de la factura cuando se detecta alguno de los
casos anteriores. Se recalculan al cambiar el contacto, los impuestos o las
cuentas de las líneas.

El módulo depende de ``l10n_es_aeat`` para disponer de la información de IVA y
de clientes anónimos de efectivo.

Autor
~~~~~

* `Trey Kilobytes de Soluciones SL <https://www.trey.es>`__
