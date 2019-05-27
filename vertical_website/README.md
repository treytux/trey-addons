Información
===========

Este módulo instala dependencias útiles para el sitio web.

Repositorios necesarios
-----------------------

- git@git.trey.es:odoo/odoo_modules.git
- git@git.trey.es:odoo/trey-addons.git
- git@github.com:odoo/odoo.git
- git@github.com:OCA/website.git

Módulos pendientes de revisar
-----------------------------

- website_attributes: para migrar desde trey-addons
- website_crm_recaptcha: este puede ser interesante
- website_files: no existe en la 11.0
- website_hide_info: para migrar desde trey-addons
- website_less: no es necesario
- website_legal_page: no es necesario si se instala website_crm_privacy_policy
- website_seo: revisar en trey-addons
- website_seo_url: pendiente de migrar en OCA website_seo_redirection
- website_signup_legal_page_required: puede que no sea necesario
- website_social_share: migrar de trey-addons
- website_styles_fix: revisar si es necesario
- website_no_crawler: puede ser interesante para bloquear web crawlers en el robots.txt
- website_odoo_debranding: puede ser interesante, oculta "Crea un sitio web gratis con Odoo" del pie
- website_snippet_anchor: probar para ver si interesa
- website_snippet_preset: probar para ver si interesa


Módulos recomendados
--------------------

- git@git.trey.es:odoo/themes.git (original en git@github.com:odoo/design-themes.git)
    - website_animate
- git@git.trey.es:odoo/trey-addons.git
    - website_language_selector
- git@github.com:odoo/odoo.git
    - website_twitter
- git@github.com:OCA/website.git
    - website_breadcrumb
    - website_crm_quick_answer
    - website_crm_recaptcha
    - website_logo

Configuración
-------------
El módulo `website_animate` requiere del siguiente código para activar las opciones avanzadas.

En el fichero `__openerp__.py`:
```
'data': [
    'templates/website.xml',
],
```

En el fichero `templates/website.xml`:
```
<record id="website_animate.o_animate_options_options" model="ir.ui.view">
    <field name="active">True</field>
</record>
```


