-- ================================================================
-- DATOS INICIALES / RECONSTRUCCION DE PRODUCTOS
-- Ejecutar despues de oracle_schema.sql
-- Si ya existen datos, revisar antes de ejecutar para evitar duplicados
-- ================================================================

-- ----------------------------------------------------------------
-- CATEGORIAS
-- ----------------------------------------------------------------
MERGE INTO categoria c
USING (SELECT 1 AS id, 'Arepa de rellenar' AS nombre FROM dual) s
ON (c.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, nombre)
    VALUES (s.id, s.nombre);

MERGE INTO categoria c
USING (SELECT 2 AS id, 'Arepa mediana' AS nombre FROM dual) s
ON (c.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, nombre)
    VALUES (s.id, s.nombre);

MERGE INTO categoria c
USING (SELECT 3 AS id, 'Arepa de chócolo' AS nombre FROM dual) s
ON (c.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, nombre)
    VALUES (s.id, s.nombre);

MERGE INTO categoria c
USING (SELECT 4 AS id, 'Arepa pequeña' AS nombre FROM dual) s
ON (c.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, nombre)
    VALUES (s.id, s.nombre);

MERGE INTO categoria c
USING (SELECT 5 AS id, 'Arepa familiar' AS nombre FROM dual) s
ON (c.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, nombre)
    VALUES (s.id, s.nombre);

MERGE INTO categoria c
USING (SELECT 6 AS id, 'Arepa grande' AS nombre FROM dual) s
ON (c.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, nombre)
    VALUES (s.id, s.nombre);

-- ----------------------------------------------------------------
-- PRODUCTOS
-- ----------------------------------------------------------------
MERGE INTO productos p
USING (
    SELECT
        1 AS id,
        'Arepa pequeña rellena de queso' AS descripcion,
        1500 AS precio,
        30 AS stock,
        '/static/img/productos/arepa-pequena.png' AS imagen,
        1 AS activo,
        '/static/img/productos/arepa-pequena.png' AS imagen_url,
        4 AS categoria_id
    FROM dual
) s
ON (p.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, descripcion, precio, stock, imagen, activo, created_at, updated_at, imagen_url, categoria_id)
    VALUES (s.id, s.descripcion, s.precio, s.stock, s.imagen, s.activo, SYSTIMESTAMP, SYSTIMESTAMP, s.imagen_url, s.categoria_id);

MERGE INTO productos p
USING (
    SELECT
        2 AS id,
        'Arepa mediana con carne y queso' AS descripcion,
        1500 AS precio,
        40 AS stock,
        '/static/img/productos/arepa-mediana.png' AS imagen,
        1 AS activo,
        '/static/img/productos/arepa-mediana.png' AS imagen_url,
        2 AS categoria_id
    FROM dual
) s
ON (p.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, descripcion, precio, stock, imagen, activo, created_at, updated_at, imagen_url, categoria_id)
    VALUES (s.id, s.descripcion, s.precio, s.stock, s.imagen, s.activo, SYSTIMESTAMP, SYSTIMESTAMP, s.imagen_url, s.categoria_id);

MERGE INTO productos p
USING (
    SELECT
        3 AS id,
        'Arepa grande con multiples rellenos' AS descripcion,
        2200 AS precio,
        30 AS stock,
        '/static/img/productos/arepa-grande.png' AS imagen,
        1 AS activo,
        '/static/img/productos/arepa-grande.png' AS imagen_url,
        6 AS categoria_id
    FROM dual
) s
ON (p.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, descripcion, precio, stock, imagen, activo, created_at, updated_at, imagen_url, categoria_id)
    VALUES (s.id, s.descripcion, s.precio, s.stock, s.imagen, s.activo, SYSTIMESTAMP, SYSTIMESTAMP, s.imagen_url, s.categoria_id);

MERGE INTO productos p
USING (
    SELECT
        4 AS id,
        'Arepa grande para compartir en familia' AS descripcion,
        2500 AS precio,
        40 AS stock,
        '/static/img/productos/arepa-familiar.png' AS imagen,
        1 AS activo,
        '/static/img/productos/arepa-familiar.png' AS imagen_url,
        5 AS categoria_id
    FROM dual
) s
ON (p.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, descripcion, precio, stock, imagen, activo, created_at, updated_at, imagen_url, categoria_id)
    VALUES (s.id, s.descripcion, s.precio, s.stock, s.imagen, s.activo, SYSTIMESTAMP, SYSTIMESTAMP, s.imagen_url, s.categoria_id);

MERGE INTO productos p
USING (
    SELECT
        5 AS id,
        'Arepa lista para rellenar al gusto' AS descripcion,
        4000 AS precio,
        36 AS stock,
        '/static/img/productos/arepa-pequena.png' AS imagen,
        1 AS activo,
        '/static/img/productos/arepa-pequena.png' AS imagen_url,
        1 AS categoria_id
    FROM dual
) s
ON (p.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, descripcion, precio, stock, imagen, activo, created_at, updated_at, imagen_url, categoria_id)
    VALUES (s.id, s.descripcion, s.precio, s.stock, s.imagen, s.activo, SYSTIMESTAMP, SYSTIMESTAMP, s.imagen_url, s.categoria_id);

MERGE INTO productos p
USING (
    SELECT
        6 AS id,
        'Arepa elaborada con chócolo fresco' AS descripcion,
        3200 AS precio,
        26 AS stock,
        '/static/img/productos/arepa-chocolo.png' AS imagen,
        1 AS activo,
        '/static/img/productos/arepa-chocolo.png' AS imagen_url,
        3 AS categoria_id
    FROM dual
) s
ON (p.id = s.id)
WHEN NOT MATCHED THEN
    INSERT (id, descripcion, precio, stock, imagen, activo, created_at, updated_at, imagen_url, categoria_id)
    VALUES (s.id, s.descripcion, s.precio, s.stock, s.imagen, s.activo, SYSTIMESTAMP, SYSTIMESTAMP, s.imagen_url, s.categoria_id);

COMMIT;

-- ----------------------------------------------------------------
-- AJUSTE DE IDENTITY DESPUES DE INSERTS MANUALES
-- ----------------------------------------------------------------
ALTER TABLE categoria MODIFY id GENERATED BY DEFAULT AS IDENTITY (START WITH LIMIT VALUE);
ALTER TABLE productos MODIFY id GENERATED BY DEFAULT AS IDENTITY (START WITH LIMIT VALUE);
