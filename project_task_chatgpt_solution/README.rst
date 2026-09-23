==============================
Project Task Chat GPT Solution
==============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo ofrece una solución para la gestión de tareas en Odoo,
integrando la API de Chat GPT de OpenAI.

**Tabla de contenidos**

.. contents::
   :local:

Características
===============

* Permite solicitar propuestas de solución automáticas para tareas de proyecto usando ChatGPT.
* Recopila el título, descripción e historial de conversación de la tarea y lo envía a ChatGPT.
* Añade la respuesta de ChatGPT como nota interna en el chatter de la tarea.
* Soporta múltiples modelos de ChatGPT configurables desde el módulo `chatgpt_api_connector`.
* Gestión de errores y mensajes claros en caso de problemas de comunicación con la API.

Configuración
=============

1. Instala este módulo y el módulo `chatgpt_api_connector`.
2. Configura tu clave API de OpenAI en los ajustes del sistema (ver documentación de `chatgpt_api_connector`).
3. (Opcional) Selecciona el modelo de ChatGPT a utilizar en la configuración.

Uso
===

1. Abre una tarea de proyecto en Odoo.
2. Haz clic en el botón "Obtener Solución de ChatGPT" (puede aparecer como acción o botón contextual).
3. El sistema recopilará la información relevante y enviará la consulta a ChatGPT.
4. La respuesta generada por la IA se añadirá automáticamente como nota interna en el chatter de la tarea.

Notas técnicas
==============

* El módulo utiliza el método `chat_completion` del conector para interactuar con la API de OpenAI.
* El historial de mensajes se limpia de HTML antes de enviarse a la IA.
* El prompt enviado a ChatGPT está optimizado para obtener respuestas prácticas y accionables.

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_

Colaboradores
~~~~~~~~~~~~~

* Equipo de Trey

Licencia
========

AGPL-3

Soporte
=======

Para soporte, contacta con el equipo de Trey en https://www.trey.es
