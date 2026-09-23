# Documentación de Endpoints para la integración entre WooCommerce y Odoo

Documentación de endpoints disponible para la integración WooCommerce Odoo

Una sugerencia de conexión es con PHP a través del paquete de composer automattic/woocommerce
`use Automattic\WooCommerce\Client;
$woocommerce = new Client(
    'http://TuSitioWoocommece.com',
    'ck_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    'cs_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    [
        'version' => 'wc/v3',
    ]
);
print_r($woocommerce->get('products'));`

Otra opción es en Python con
https://pypi.org/project/WooCommerce/

+información en
https://github.com/woocommerce/woocommerce/wiki/Getting-started-with-the-REST-API
https://woocommerce.github.io/woocommerce-rest-api-docs/?python#libraries-and-tools

Este plugin hace uso de las clases WC_REST_* para extenderlas y reescribir el comportamiento.

Las características del plugin es para hacer override de la rest API:
* parsear la ID en los casos de updates y deletes ponerles las ids correspondientes de WordPress,
* preparar los campos de descuentos que hacen uso de un plugin paralelo en los inserts updates
* borrar los campos de descuentos cuando se hace delete de un producto

Y para enviar información hacia Odoo como:
* En la creación de usuario, enviar la información y guardar la id de Odoo
* En la creación de pedidos, enviar la información y guardar la id de Odoo
* Hacer override de la página de my account para mostrar enlaces hacia el user de Odoo

Se pueden ver ejemplos de llamadas json en a carpeta /examples

# Products

### Products POST create
POST `/wp-json/woodoo/v1/products`
Endpoint con override para controlar que se pasan los parámetros meta_data['id_odoo'] y lang. Siempre la primera vez que se crea el producto debe ser en español.

https://woocommerce.github.io/woocommerce-rest-api-docs/#create-a-product

Se pueden hacer servir todos los elementos especificados en la documentación.
https://woocommerce.github.io/woocommerce-rest-api-docs/?php#product-properties

También se debe especificar el idioma pasando el parámetro 'lang' => 'code_lang'
https://wpml.org/documentation/related-projects/woocommerce-multilingual/using-wordpress-rest-api-woocommerce-multilingual/#create-products

Además de estos hay unos campos extras para añadir.

* (mandatory) id_odoo (string) Debe ser el id especificado en odoo
* (mandatory) lang (string) 'en','pt-pt','fr','it','es' el id con el que esté declarado en WooCommerce

* meta_data['wc_productdata_options'] (array) Propiedades relacionadas con el tema
  * _product_video (string)
* meta_data['_alg_wc_price_by_user_role_regular_price_distribuidor'] (float) precio para el distribuidor
* bulk_prices (array) se le pasa el array tal y como lo espera el plugin, el índice es el rol de usuario al que se le aplica y everyone significa a todos los usuarios incluso no identificados.
`
"prices": [{
		"distribuidor" : [
			{
				"min_quantity" : "5",
				"max_quantity" : "10",
				"type_discount" : "fixed-price",
				"discount_amount" : "4.50"
			},
			{
				"min_quantity" : "11",
				"max_quantity" : "20",
				"type_discount" : "fixed-price",
				"discount_amount" : "4.20"
			}
		],
		"everyone" : [
			{
				"min_quantity" : "5",
				"max_quantity" : "10",
				"type_discount" : "fixed-price",
				"discount_amount" : "4.50"
			},
			{
				"min_quantity" : "11",
				"max_quantity" : "20",
				"type_discount" : "fixed-price",
				"discount_amount" : "4.20"
			}
		]
	}]
`
* fecha_restock (date)

### Products DELETE
DELETE `/wp-json/woodoo/v1/products/{id_odoo}`

Para provocar el delete del producto se debe pasar el parámetro id_odoo que sea igual al elemento en la url.

* (mandatory) id_odoo (string) Debe ser el id especificado en odoo
* (mandatory) lang (string) 'en','pt-pt','fr','it','es' el id con el que esté declarado en WooCommerce

## Attributes
### Products Attributes POST create
POST `/wp-json/woodoo/v1/products/attributes`
https://woocommerce.github.io/woocommerce-rest-api-docs/?javascript#create-a-product-attribute

* (mandatory) name (string) En inglés para dar de alta
* (mandatory) slug (string) Alerta que este será el que se utiliza para sincronizar con Odoo y para añadir términos a los productos

### Products Attributes DELETE delete
DELETE `/wp-json/woodoo/v1/products/attributes/{slug}`

* (mandatory) slug (string) Alerta que este será el que se utiliza para sincronizar con Odoo y para añadir términos a los productos

## Variations
### Products Variations POST create
POST `https://local.enuc/wp-json/woodoo/v1/products/<id_odoo>/variations`
https://woocommerce.github.io/woocommerce-rest-api-docs/#product-variations

* id_odoo (string) Si se especifica se hará update del producto
* (mandatory) id_odoo_parent (string) Debe ser el id del producto padre especificado en odoo
* (mandatory) lang (string) 'en','pt-pt','fr','it','es' el id con el que esté declarado en WooCommerce
* (mandatory) attributes (array)
  * slug (string) Debe ser el slug con el que se creó el attributo
  * option (string) El valor del atributo

# Categories
### Categories POST create
POST `/wp-json/woodoo/v1/products/categories`
https://woocommerce.github.io/woocommerce-rest-api-docs/#create-a-product-category

* (mandatory) id_odoo (string) Debe ser el id especificado en odoo
* (mandatory) lang (string) 'en','pt-pt','fr','it','es' el id con el que esté declarado en
*	cat_header (string) contenido para la plantilla flatsome
*	cat_footer (string) contenido para la plantilla flatsome

### Categories POST updating id_odoo
POST `/wp-json/woodoo/v1/products/categories/{id_odoo}`

* (mandatory) id_odoo (string) Debe ser el id especificado en odoo
* (mandatory) lang (string) 'en','pt-pt','fr','it','es' el id con el que esté declarado en WooCommerce

### Categories DELETE getting id_odoo
DELETE `/wp-json/woodoo/v1/product/categories/{id_odoo}`

* (mandatory) id_odoo (string) Debe ser el id especificado en odoo
* (mandatory) lang (string) 'en','pt-pt','fr','it','es' el id con el que esté declarado en WooCommerce

# Comerciales
### Comercial POST create
POST `/wp-json/woodoo/v1/comerciales`
* (mandatory) id_odoo (string) Debe ser el id especificado en odoo
* (mandatory) title (string)
* telefono (string)
* extension (string)
* email (string)

### Comercial POST updatting id_odoo
POST `/wp-json/woodoo/v1/comerciales/{id_odoo}`
* (mandatory) id_odoo (string) Debe ser el id especificado en odoo

### Comercial POST getting id_odoo
DELETE `/wp-json/woodoo/v1/comerciales/{id_odoo}`
* (mandatory) id_odoo (string) Debe ser el id especificado en odoo

# Users
### Customer POST create
POST `/wp-json/woodoo/v1/users`
* (mandatory) id_odoo (string) Debe ser el id especificado en odoo
*	idodoo_comercial (string) la id de odoo del comercial asignado
* roles (array) los id de Odoo que sean
* (mandatory) email (string)
* first_name (string)
* last_name (string)
* (mandatory) username (string)
*	(mandatory) password (string)
* billing y shipping revisar el archivo de ejemplo
* logo_partner (url de fichero)
* telefono_partner (string)
* email_partner (string)
* porcentaje_beneficios_partner (string)

### Customer POST updating id_odoo
POST `/wp-json/woodoo/v1/users/{id_odoo}`
* (mandatory) id_odoo (string) Debe ser el id especificado en odoo

### Customer DELETE getting id_odoo
DELETE `/wp-json/woodoo/v1/users/{id_odoo}`
* (mandatory) id_odoo (string) Debe ser el id especificado en odoo

