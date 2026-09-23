
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Product create orderpoint auto
==============================
Cuando se crea un producto, automáticamente se crea también una regla de
reabastecimiento para cada uno de los almacenes configurados en la compañía.

Uso
===
Al crear productos almacenables se crea automáticamente una orden de
reabastecimiento para cada almacén configurado en la compañía activa, los
servicios no generan reglas de abastecimiento.

En entornos de multicompañía no se generarán reabastecimientos en aquellas
compañías que no tengan configurada la opción.

Configuración
=============

- Acceda a **Ajustes/Usuarios y compañías/Compañías**
- Acceda a la compañía que desea configurar
- Acceda a la pestaña de **Almacén**
- En **Crear regla de reabastecimiento automáticamente** añada almacenes
- Ahora los productos generarán automáticamente las reglas de reabastecimiento

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
