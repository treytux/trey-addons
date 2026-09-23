.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

stock picking pending rereserve
===============================

Para evitar que, cuando tenemos un albarán "Parcialmente disponible" y pinchemos en el botón "Comprobar de nuevo disponibilidad", se desreserven los quants de los movimientos en estado reservado, eliminando los posibles cambios de reserva hechos manualmente por el usuario, este módulo:

   - Oculta el botón "Comprobar de nuevo disponibilidad" de los albaranes en estado "Parcialmente disponible".

   - Añade un nuevo botón a los albaranes en estado "Parcialmente disponible" llamado "Comprobar disponibilidad de lo pendiente" que vuelve a reservar los quants de los movimientos de stock, excluyendo los que están ya reservados (además de los realizados o cancelados, que es lo que hacía por defecto el botón "Comprobar de nuevo disponibilidad" que se oculta).

   - Hay que tener en cuenta que, para que se mantenga la reserva manual hecha por el usuario, el movimiento debe estar reservado, es decir, que tiene que haberse asignado manualmente la cantidad total que se indica en el movimiento porque, si la cantidad reservada no es igual al total de la cantidad indicada en el movimiento, el nuevo botón 'Comprobar disponibilidad de lo pendiente' detecta que el movimiento está en estado 'Esperando disponibilidad' ('confirmed') y llama a la función 'rereserve_quants' estándar que desreserva lo reservado y vuelve a reservar de forma automática, perdiendo la reserva manual que hizo el usuario.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
