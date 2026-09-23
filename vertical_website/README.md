Información
===========

Este módulo instala dependencias útiles para el sitio web.

Repositorios necesarios
-----------------------

- git@git.trey.es:odoo/odoo_modules.git
- git@git.trey.es:odoo/trey-addons.git
- git@github.com:odoo/odoo.git
- git@github.com:OCA/website.git

Módulos recomendados
--------------------

- git@git.trey.es:odoo/themes.git (original en git@github.com:odoo/design-themes.git)
    - website_animate
- git@git.trey.es:odoo/trey-addons.git
    - website_cookiebot
    - website_language_selector
- git@github.com:odoo/odoo.git
    - website_twitter
- git@github.com:OCA/website.git
    - website_breadcrumb
    - website_cookie_notice
    - website_crm_quick_answer
    - website_crm_recaptcha
    - website_logo

Configuración
-------------
Una vez instalada la vertical será necesario instalar algún módulo que muestre
el aviso legal sobre las cookies:

- website_cookie_notice
- website_cookiebot (gratuito para sitios web con menos de 100 páginas)

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


