.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

base_manage_exception
=====================

Módulo base para gestionar excepciones.


Configuración
-------------

Desde el menú Ajustes/Manejar excepciones hay que crear un manejador de
excepciones y agreguar una línea para cada función sobre la que desee recibir
comentarios cuando haya una excepción.

Para cada una de las líneas, cuando la función se ejecuta con sus parámetros,
si se lanza una excepción, el sistema creará una acción del tipo definido.

Estos son los campos que hay que rellenar:

    - Nombre: nombre descriptivo de la acción que se va a realizar.

    - Compañía: compañía para la que se va a ejecutar la función.

    - Usuarios: usuarios responsables que serán informados de las excepciones.

    - Modelo: modelo donde se declara la función a ejecutar.

    - Nombre de la función: nombre de la función a ejecutar y de la que se
    gestionarán sus excepciones.

    - Parámetros de función: parámetros de la función cuyos valores se
    expresan como diccionario. Por ejemplo:
        {'param1': valor1, 'param2': valor2}.
    Si la función no tiene parámetros, deje solo {}.

    - Acción a ejecutar: acción a ejecutar cuando se detecta un error de
    excepción en la función seleccionada.

    - Notificar excepción: si esta opción está desactivada, no se tendrán en
    cuenta las excepciones de la función y no se lanzará la acción asociada.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
