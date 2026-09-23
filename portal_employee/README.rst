.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============
Portal Employee
===============

Portal de empleados.

Incluye acceso a documentación de conocimiento y firma de documentos PDF
adjuntos desde el portal de empleado.

Configuración
=============

* Desde el menú "Ajustes / Opciones Generales / Sitio web / Solicitudes de
  ausencia" seleccionar el tipo de ausencia para vacaciones.
* Desde el menú "Ajustes / Usuarios y compañías / Usuarios" marcar en la
  pestaña "Preferencias" para cada uno de ellos si deseamos "Bloquear el
  acceso al backoffice".
* Podemos definir las categorías de conocimiento a las que tendrá acceso el
  usuario a través del campo 'Categorías de conocimiento' de su perfil.
* En páginas de conocimiento (`document.page`) se puede activar "Permitir
  firma de PDF" para permitir la firma portal de un único adjunto PDF.

Acceso a conocimiento
=====================

El portal de empleado muestra categorías y documentos de conocimiento en
función de las categorías asignadas en el campo 'Categorías de conocimiento'
del usuario.

Un usuario podrá consultar:

* Las categorías asignadas directamente en su perfil.
* Las subcategorías directas de esas categorías.
* Los documentos contenidos en cualquiera de esas categorías permitidas.

No es necesario conceder al usuario los grupos internos de conocimiento de
Odoo para usar el portal de empleado. La asignación funcional se realiza desde
el perfil del usuario, seleccionando las categorías que debe consultar. En
instalaciones multi compañía también se comprueba la compañía de la categoría
o documento.

Compañías en categorías y documentos
====================================

En instalaciones multi compañía, la compañía de las categorías y documentos
debe configurarse según el alcance real del contenido:

* Si el contenido debe ser común para cualquier empresa, crear la categoría y
  sus documentos sin compañía (`company_id` vacío).
* Si el contenido pertenece a una empresa concreta, crear la categoría y sus
  documentos con esa compañía asignada.
* Si el contenido debe ser común para una estructura de empresas, se puede
  crear en una compañía padre. Los empleados de compañías hijas podrán
  consultarlo siempre que tengan asignada la categoría correspondiente.
* Si varias empresas necesitan contenido propio, crear categorías y documentos
  específicos para cada compañía y asignar a cada usuario las categorías de su
  empresa.

El portal considera accesibles las categorías y documentos sin compañía, los
de la compañía del empleado y los de cualquier compañía padre de la compañía
del empleado. Para contenido transversal a todas las empresas sigue siendo más
claro dejar la compañía vacía; para contenido particular, usar documentos
específicos por compañía.

Créditos
========

Autor
~~~~~

* `Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

Mantenedores
~~~~~~~~~~~~

Este módulo es mantenido por Trey Kilobytes de Soluciones SL.

.. image:: https://trey.es/logo.png
   :alt: Trey Kilobytes de Soluciones SL
   :target: https://www.trey.es
