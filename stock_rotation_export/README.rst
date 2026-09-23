.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock rotation export
=====================

Este módulo añade un nuevo asistente "Exportar rotación de stock" en el menú "Inventario/Informes" que genera un fichero excel con la rotación de stock entre dos fechas establecidas por el usuario.

El asistente pide al usuario los siguientes campos obligatorios:
   - Fecha desde.
   - Fecha hasta.
   - Opcionalmente se puede rellenar el campo "Proveedor", si lo hace, se filtrará la búsqueda y sólo se generará el informe con los productos que tengan dicho proveedor definido en el formulario de producto.

El fichero generado muestra las siguientes columnas:
   - Referencia interna producto: referencia interna del producto.
   - Nombre producto: nombre del producto.
   - Categoría: categoría a la que pertenece del producto.
   - Ubicación: nombre de la ubicación.
   - Ratio: se calcula con la siguiente fórmula en base al resto de columnas:
          ratio = (Comprado + Dev. de clientes + Stock en "Fecha desde") / (Vendido + Dev. a proveedores))
   - Stock en "Fecha desde": stock calculado en la "Fecha desde" indicada en el asistente.
   - Stock en "Fecha hasta": stock calculado en la "Fecha hasta" indicada en el asistente.
   - Comprado: cantidad de producto comprada.
   - Dev. de clientes: cantidad de producto devuelta por clientes.
   - Vendido: cantidad de producto vendida.
   - Dev. a proveedores: cantidad de producto devuelta por proveedores.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
