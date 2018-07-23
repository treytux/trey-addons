**Información**

Este módulo implementa las funcionalidades necesarias para cargar las imágenes
de productos en el sitio web a partir de ficheros en disco en lugar del
habitual almacenamiento en base de datos.

No implementa cambios significativos en el sitio web, ya que es la base para
otros módulos que si incluirán galerías de imágenes o efectos tipo zoom.

**Configuración y uso**

- La carpeta por defecto para almacenar los ficheros es "[addons_path]/website_sale_multi_image_disk/static/images"
- Inicialmente habrá que crear la carpeta o bien un enlace simbólico con el nombre "images" a otra que contenga las imágenes.
- Si se prefiere, también puede indicarse la ruta de la carpeta mediante el parámetro del sistema "website_sale_multi_image_disk.static_dir"
- El idioma para los nombres de imágenes se toma del idioma por defecto del sitio web.
- Puede indicarse que se traduzcan los nombres de las imágenes por cada idioma asignando "True" al parámetro del sistema "website_sale_multi_image_disk.translate" para mejorar el SEO, pero obliga a mantener todas las imágenes por cada uno de ellos.
- Las ficheros en disco para las imágenes se nombran con el slug del producto y el sufijo "-n", siendo n un número, y a continuación la extensión correspondiente.
- Los ficheros de plantillas de producto (para los listados) o productos sin variantes (para la ficha) se nombran a partir del slug del nombre. Ej: "ipad-con-pantalla-retina-1.jpg", "ipad-con-pantalla-retina-2.jpg", etc...
- Si únicamente se va a mostrar una imagen en el producto o plantilla puede omitirse el sufijo. Ej: "ipad-con-pantalla-retina.jpg" sería lo mismo que "ipad-con-pantalla-retina-1.jpg".
- Los ficheros de variantes de producto se nombran a partir del slug del nombre de la plantilla, el nombre del attributo y el nombre del valor del atributo. Ej: "ipad-con-pantalla-retina-color-blanco-1.jpg", "ipad-con-pantalla-retina-color-blanco-2.jpg", etc...
- Debido a que los nombres de fichero se toman a partir del nombre del producto, cada vez que se modifique, es probable que se tengan que renombrar.
- La calidad de las miniaturas generadas se indica en el parámetro del sistema "website_sale_multi_image_disk.image_quality". El valor porcentual por defecto es 85.

**Mejoras**

- Generar miniaturas transparentes para los formatos .png y .gif
- Ordenación de atributos de producto para controlar como se generan los slugs para las variantes
- Mostrar información de las imágenes no encontradas en modo edición (para administradores), quizás como una opción personalizable por si se quiere ocultar en algún momento
