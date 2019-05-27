.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
Website User Inactive
=====================

Controla el tiempo que lleva un usuario externo (de compartición) sin acceder
al sistema permitiendo parametrizar dicho tiempo en días.

Usando este parámetro mediante una acción planificada se bloquean los usuarios
que cumplan con alguno de los siguientes criterios:

- El número de días desde el último inicio de sesion del usuario supera el
tiempo de parametrización del módulo.

Parametrización
===============
En la configuración del sitio web. Hay un apartado para indicar el número de
días de inactividad para el bloqueo.

En acciones planificadas tenemos una acción para bloquear los usuarios. Por
defecto se ejecuta una vez al día.
