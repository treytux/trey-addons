
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Product pricelist item by conditions
====================================
Añade una nueva opción al campo "Calcula el precio" del elemento de tarifa llamada "Por condiciones" para que el usuario seleccione el precio basado para el cálculo con el campo "Basado en" y añada las franjas de precios donde aplicar el porcentaje de los incrementos o decrementos de precio en el campo "Incrementos por rangos (%)".

Cada condición consta de tres caampos:

    - "Precio desde": indica el precio desde el cual se aplicará el porcentaje de incremento/decremento. Es un campo calculado; para la primera franja es 0 y para las siguientes un céntimo más que el valor del campo "Precio hasta" de la franja anterior.

    - "Precio hasta": indica el precio hasta el cual se aplicará el porcentaje de incremento/decremento.

    - "Porcentaje incremento/decremento": indica el porcentaje al que se incrementará o decrementará el precio. Su valor debe ser siempre positivo.
    La fórmula usada para calcular el precio es:
        Precio * Porcentaje incremento/decremento / 100
    Si el valor es mayor que 100, se incrementará el precio en ese porcentaje.
    Si por el contrario el valor es menor que 100, se decrementará el precio en ese porcentaje.

    Ejemplo:
        Pongamos que tenemos un producto cuyo precio es 10.
        Si 'Porcentaje incremento/decremento' = 200, el precio final será: 10 * 200 / 100 = 20, es decir, el precio se a incrementado a un 200%.
        Si por el contrario 'Porcentaje incremento/decremento' = 50, el precio final será: 10 * 50 / 100 = 5, es decir, el precio se a decrementado a un 50%.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
