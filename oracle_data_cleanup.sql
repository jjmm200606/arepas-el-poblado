-- =========================================================
-- Limpieza de datos migrados a Oracle
-- Corrige caracteres especiales y restaura timestamps
-- =========================================================

-- ---------------------------------------------------------
-- CATEGORIAS
-- ---------------------------------------------------------
UPDATE categoria
SET nombre = 'Arepa de chócolo'
WHERE id = 3;

UPDATE categoria
SET nombre = 'Arepa pequeña'
WHERE id = 4;

-- ---------------------------------------------------------
-- USUARIOS
-- ---------------------------------------------------------
UPDATE usuarios
SET nombre = 'Juan Pérez',
    created_at = TO_TIMESTAMP('2026-03-24 23:14:46.208723', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-03-24 23:14:46.208723', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 3;

UPDATE usuarios
SET created_at = TO_TIMESTAMP('2026-04-23 00:11:59.782838', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-04-23 00:11:59.782838', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 5;

UPDATE usuarios
SET created_at = TO_TIMESTAMP('2026-03-24 23:14:46.208723', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-03-24 23:14:46.208723', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 2;

UPDATE usuarios
SET created_at = TO_TIMESTAMP('2026-03-24 23:14:46.208723', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-05-04 08:05:25.054978', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 1;

-- ---------------------------------------------------------
-- PRODUCTOS
-- ---------------------------------------------------------
UPDATE productos
SET descripcion = 'Arepa grande con múltiples rellenos',
    activo = 1,
    created_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 3;

UPDATE productos
SET descripcion = 'Arepa grande para compartir en familia',
    activo = 1,
    created_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 4;

UPDATE productos
SET descripcion = 'Arepa lista para rellenar al gusto',
    activo = 1,
    created_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 5;

UPDATE productos
SET descripcion = 'Arepa elaborada con chócolo fresco',
    activo = 1,
    created_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 6;

UPDATE productos
SET descripcion = 'Arepa pequeña rellena de queso',
    activo = 1,
    created_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 1;

UPDATE productos
SET descripcion = 'Arepa mediana con carne y queso',
    activo = 1,
    created_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-03-24 23:15:05.2012', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 2;

-- ---------------------------------------------------------
-- PEDIDOS
-- ---------------------------------------------------------
UPDATE pedidos
SET fecha_pedido = TO_TIMESTAMP('2026-03-24 23:15:24.363181', 'YYYY-MM-DD HH24:MI:SS.FF'),
    created_at = TO_TIMESTAMP('2026-03-24 23:15:24.363181', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-03-24 23:15:24.363181', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 2;

UPDATE pedidos
SET fecha_pedido = TO_TIMESTAMP('2026-03-24 23:15:24.363181', 'YYYY-MM-DD HH24:MI:SS.FF'),
    created_at = TO_TIMESTAMP('2026-03-24 23:15:24.363181', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-05-04 01:26:44.239749', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 1;

UPDATE pedidos
SET fecha_pedido = TO_TIMESTAMP('2026-05-04 20:01:20.521586', 'YYYY-MM-DD HH24:MI:SS.FF'),
    created_at = TO_TIMESTAMP('2026-05-04 20:01:20.521586', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-05-04 16:19:02.224224', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 14;

UPDATE pedidos
SET fecha_pedido = TO_TIMESTAMP('2026-05-04 16:22:13.77593', 'YYYY-MM-DD HH24:MI:SS.FF'),
    created_at = TO_TIMESTAMP('2026-05-04 16:22:13.77593', 'YYYY-MM-DD HH24:MI:SS.FF'),
    updated_at = TO_TIMESTAMP('2026-05-04 16:24:18.077532', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 15;

-- ---------------------------------------------------------
-- DETALLES DE PEDIDO
-- ---------------------------------------------------------
UPDATE detalles_pedido
SET created_at = TO_TIMESTAMP('2026-03-24 23:16:35.869413', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id IN (1, 2, 3, 4, 5);

UPDATE detalles_pedido
SET created_at = TO_TIMESTAMP('2026-05-04 20:01:20.521586', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 13;

UPDATE detalles_pedido
SET created_at = TO_TIMESTAMP('2026-05-04 16:22:13.77593', 'YYYY-MM-DD HH24:MI:SS.FF')
WHERE id = 14;

COMMIT;
