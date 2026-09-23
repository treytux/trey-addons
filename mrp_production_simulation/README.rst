=========================
MRP production simulation
=========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Asistente para simular una orden de fabricación, mostrando en una ventana los productos disponibles en el almacén y la cantidad que se puede fabricar actualmente.

Para ello, mostrará:

- La cantidad que se desea fabricar.

- La cantidad real disponible (stock real) de los componentes.

- La cantidad virtual disponible (stock virtual) de los componentes.

- La cantidad pendiente de compra de los componentes.

- La cantidad pendiente de fabricación de los componentes.

Y se calculará:

- El número de unidades que se pueden fabricar actualmente, considerando el stock real.

- El número de unidades que se pueden fabricar actualmente, considerando el stock virtual.

Las líneas están marcadas con diferentes colores según su significado:

- Negro: líneas con cantidad disponible.

- Azul: líneas con cantidad pendiente de compra.

- Violeta: líneas con cantidad pendiente de producción.

Además, si un producto fabricado tiene stock disponible, no se muestran las líneas de nivel inferior que lo componen. Si, por el contrario, el producto fabricado no tiene stock disponible, sí se muestran las líneas de nivel inferior que lo componen, ya que es importante saber si tienen stock para la fabricación.

También se muestra el resumen de las compras necesarias para producir el producto principal.

**Tabla de contenidos**

.. contents::
   :local:

Uso
===

#. Ir a *Fabricación > Órdenes de fabricación*.
#. Abrir cualquier orden.
#. Se mostrará un nuevo botón inteligente llamado *Simulación de fabricación* que permite visualizar o acceder al desglose del producto.

#. Ir a *Fabricación > Lista de materiales*.
#. Abrir cualquier lista.
#. Se mostrará un nuevo botón inteligente llamado *Simulación de fabricación* que permite visualizar o acceder al desglose del producto.

Créditos
========

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
