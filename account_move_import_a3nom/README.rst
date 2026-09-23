=========================
Account move import A3Nom
=========================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: Licencia: AGPL-3

Descripción
===========

Este módulo permite importar asientos contables de nóminas desde ficheros de
texto generados por **A3Nom**. Amplía el asistente de importación de asientos
del módulo ``account_move_import`` con el tipo de fichero **A3Nom**.

Durante la importación, las líneas se agrupan por el usuario asociado a cada
trabajador y se crea un asiento por cada usuario. El asiento utiliza como
referencia ``Payroll <nombre del contacto>``.

Características
===============

* Añade **A3Nom** como tipo de importación de ficheros.
* Añade a los empleados los campos:

  * **A3Nom empresa**: identificador numérico de la empresa en A3Nom.
  * **A3Nom código de trabajador**: identificador numérico del trabajador en
    A3Nom.

* Relaciona cada línea importada con el contacto del usuario del empleado.
* Busca las cuentas contables a partir del código incluido en el fichero:

  * Primero intenta localizar una cuenta cuyo código empiece por los cuatro
    primeros dígitos seguidos de ``00``.
  * Si no existe, busca cuentas que empiecen por los cuatro primeros dígitos.
  * La cuenta seleccionada debe terminar en ``0`` y la búsqueda debe devolver
    una única cuenta.

* Aplica el tratamiento fiscal español a las cuentas de nómina:

  * Las cuentas que empiezan por ``640`` reciben el impuesto y la etiqueta
    fiscal correspondientes al modelo 111.
  * Las cuentas que empiezan por ``4751`` se identifican como líneas de
    impuesto de IRPF.

Requisitos del fichero
======================

El fichero debe ser un fichero de texto detallado por trabajador, con el
formato de posiciones fijas esperado por A3Nom. Entre otros datos, el
importador utiliza estas posiciones:

* Posición 2, longitud 5: empresa A3Nom.
* Posición 7, longitud 8: fecha en formato ``AAAAMMDD``.
* Posición 16, longitud 12: código de cuenta contable.
* Posición 28, longitud 30: concepto.
* Posición 58, longitud 1: tipo de importe (``D`` para debe o ``H`` para
  haber).
* Posición 61, longitud 6: código de trabajador A3Nom.
* Posición 100, longitud 14: importe.

El fichero debe contener el identificador del trabajador. Para cada empleado
incluido en el fichero debe existir una coincidencia por empresa y código, y
el empleado debe tener un usuario de Odoo asignado.

Uso
===

Configuración de empleados
--------------------------

1. Vaya a **Empleados** y abra la ficha de cada trabajador incluido en el
   fichero.
2. En el grupo **A3Nom**, introduzca la empresa y el código de trabajador que
   utiliza A3Nom.
3. Asigne un usuario de Odoo al empleado. El usuario se utiliza para obtener
   el contacto asociado al asiento importado.

Importación
-----------

1. Instale y configure el módulo ``account_move_import``.
2. Active la importación de asientos en el diario contable que recibirá las
   nóminas.
3. Desde el diario, abra el asistente **Import Moves**.
4. Seleccione el tipo **A3Nom**, adjunte el fichero y pulse **Importar**.
5. Revise los asientos creados desde la vista de asientos contables.

El asistente muestra un error si falta el impuesto de IRPF, no existe la
cuenta contable correspondiente, no se encuentra el empleado o el empleado no
tiene usuario asignado.

Autor
=====

* `Trey <https://www.trey.es>`__
