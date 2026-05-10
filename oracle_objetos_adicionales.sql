-- =========================================================
-- Objetos adicionales para Oracle
-- Arepas El Poblado
-- Incluye:
-- 1. 6 apuntadores (claves foraneas de referencia)
-- 2. 6 vistas
-- 3. 6 funciones
-- 4. 6 triggers
-- =========================================================

-- =========================================================
-- 1. APUNTADORES / REFERENCIAS (YA EXISTEN EN EL MODELO)
-- =========================================================
-- 1) usuarios.rol_id -> rol.id
-- 2) usuarios.estado_usuario_id -> estado_usuario.id
-- 3) productos.categoria_id -> categoria.id
-- 4) pedidos.usuario_id -> usuarios.id
-- 5) pedidos.estado_pedido_id -> estado_pedido.id
-- 6) detalles_pedido.producto_id -> productos.id


-- =========================================================
-- 2. VISTAS
-- =========================================================

CREATE OR REPLACE VIEW vw_usuarios_detalle AS
SELECT
    u.id,
    u.nombre,
    u.email,
    u.telefono,
    r.nombre_rol AS rol,
    eu.nombre_estado_usuario AS estado_usuario,
    u.created_at,
    u.updated_at
FROM usuarios u
JOIN rol r ON r.id = u.rol_id
JOIN estado_usuario eu ON eu.id = u.estado_usuario_id;
/

CREATE OR REPLACE VIEW vw_productos_catalogo AS
SELECT
    p.id,
    p.descripcion,
    p.precio,
    p.stock,
    p.imagen,
    p.activo,
    c.nombre AS categoria,
    p.created_at,
    p.updated_at
FROM productos p
JOIN categoria c ON c.id = p.categoria_id;
/

CREATE OR REPLACE VIEW vw_pedidos_resumen AS
SELECT
    pe.id,
    pe.numero_pedido,
    u.nombre AS cliente,
    u.email,
    pe.total,
    ep.nombre_estado_pedido AS estado,
    pe.fecha_pedido,
    pe.fecha_entrega
FROM pedidos pe
JOIN usuarios u ON u.id = pe.usuario_id
JOIN estado_pedido ep ON ep.id = pe.estado_pedido_id;
/

CREATE OR REPLACE VIEW vw_detalles_pedido_resumen AS
SELECT
    dp.id,
    dp.pedido_id,
    pe.numero_pedido,
    dp.producto_id,
    pr.descripcion AS producto,
    dp.cantidad,
    dp.precio_unitario,
    dp.subtotal
FROM detalles_pedido dp
JOIN pedidos pe ON pe.id = dp.pedido_id
JOIN productos pr ON pr.id = dp.producto_id;
/

CREATE OR REPLACE VIEW vw_carrito_resumen AS
SELECT
    c.id AS carrito_id,
    u.nombre AS cliente,
    u.email,
    ci.id AS carrito_item_id,
    p.descripcion AS producto,
    ci.cantidad,
    p.precio,
    (ci.cantidad * p.precio) AS subtotal
FROM carritos c
JOIN usuarios u ON u.id = c.usuario_id
JOIN carrito_items ci ON ci.carrito_id = c.id
JOIN productos p ON p.id = ci.producto_id;
/

CREATE OR REPLACE VIEW vw_ventas_por_categoria AS
SELECT
    c.id AS categoria_id,
    c.nombre AS categoria,
    NVL(SUM(dp.cantidad), 0) AS total_unidades_vendidas,
    NVL(SUM(dp.subtotal), 0) AS total_vendido
FROM categoria c
LEFT JOIN productos p ON p.categoria_id = c.id
LEFT JOIN detalles_pedido dp ON dp.producto_id = p.id
GROUP BY c.id, c.nombre;
/


-- =========================================================
-- 3. FUNCIONES
-- =========================================================

CREATE OR REPLACE FUNCTION fn_total_items_pedido(p_pedido_id NUMBER)
RETURN NUMBER
IS
    v_total NUMBER;
BEGIN
    SELECT NVL(SUM(cantidad), 0)
    INTO v_total
    FROM detalles_pedido
    WHERE pedido_id = p_pedido_id;

    RETURN v_total;
END;
/

CREATE OR REPLACE FUNCTION fn_total_items_carrito(p_carrito_id NUMBER)
RETURN NUMBER
IS
    v_total NUMBER;
BEGIN
    SELECT NVL(SUM(cantidad), 0)
    INTO v_total
    FROM carrito_items
    WHERE carrito_id = p_carrito_id;

    RETURN v_total;
END;
/

CREATE OR REPLACE FUNCTION fn_stock_disponible(p_producto_id NUMBER)
RETURN NUMBER
IS
    v_stock NUMBER;
BEGIN
    SELECT NVL(stock, 0)
    INTO v_stock
    FROM productos
    WHERE id = p_producto_id;

    RETURN v_stock;
END;
/

CREATE OR REPLACE FUNCTION fn_nombre_rol_usuario(p_usuario_id NUMBER)
RETURN VARCHAR2
IS
    v_rol VARCHAR2(50);
BEGIN
    SELECT r.nombre_rol
    INTO v_rol
    FROM usuarios u
    JOIN rol r ON r.id = u.rol_id
    WHERE u.id = p_usuario_id;

    RETURN v_rol;
END;
/

CREATE OR REPLACE FUNCTION fn_estado_texto_pedido(p_pedido_id NUMBER)
RETURN VARCHAR2
IS
    v_estado VARCHAR2(50);
BEGIN
    SELECT ep.nombre_estado_pedido
    INTO v_estado
    FROM pedidos p
    JOIN estado_pedido ep ON ep.id = p.estado_pedido_id
    WHERE p.id = p_pedido_id;

    RETURN v_estado;
END;
/

CREATE OR REPLACE FUNCTION fn_total_gastado_usuario(p_usuario_id NUMBER)
RETURN NUMBER
IS
    v_total NUMBER;
BEGIN
    SELECT NVL(SUM(total), 0)
    INTO v_total
    FROM pedidos
    WHERE usuario_id = p_usuario_id;

    RETURN v_total;
END;
/


-- =========================================================
-- 4. TRIGGERS
-- =========================================================

CREATE OR REPLACE TRIGGER trg_usuarios_bi_timestamps
BEFORE INSERT ON usuarios
FOR EACH ROW
BEGIN
    IF :NEW.created_at IS NULL THEN
        :NEW.created_at := SYSTIMESTAMP;
    END IF;

    IF :NEW.updated_at IS NULL THEN
        :NEW.updated_at := :NEW.created_at;
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_usuarios_bu_updated_at
BEFORE UPDATE ON usuarios
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER trg_productos_bi_defaults
BEFORE INSERT ON productos
FOR EACH ROW
BEGIN
    IF :NEW.stock IS NULL THEN
        :NEW.stock := 0;
    END IF;

    IF :NEW.activo IS NULL THEN
        :NEW.activo := 1;
    END IF;

    IF :NEW.created_at IS NULL THEN
        :NEW.created_at := SYSTIMESTAMP;
    END IF;

    IF :NEW.updated_at IS NULL THEN
        :NEW.updated_at := :NEW.created_at;
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_productos_bu_updated_at
BEFORE UPDATE ON productos
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER trg_pedidos_bi_defaults
BEFORE INSERT ON pedidos
FOR EACH ROW
BEGIN
    IF :NEW.fecha_pedido IS NULL THEN
        :NEW.fecha_pedido := SYSTIMESTAMP;
    END IF;

    IF :NEW.created_at IS NULL THEN
        :NEW.created_at := :NEW.fecha_pedido;
    END IF;

    IF :NEW.updated_at IS NULL THEN
        :NEW.updated_at := :NEW.fecha_pedido;
    END IF;

    IF :NEW.total IS NULL THEN
        :NEW.total := 0;
    END IF;

    IF :NEW.numero_pedido IS NULL THEN
        :NEW.numero_pedido := 'PED-' || TO_CHAR(SYSTIMESTAMP, 'YYYYMMDDHH24MISSFF3');
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_detalles_pedido_biu_subtotal
BEFORE INSERT OR UPDATE ON detalles_pedido
FOR EACH ROW
BEGIN
    :NEW.subtotal := NVL(:NEW.cantidad, 0) * NVL(:NEW.precio_unitario, 0);

    IF INSERTING AND :NEW.created_at IS NULL THEN
        :NEW.created_at := SYSTIMESTAMP;
    END IF;
END;
/

COMMIT;
