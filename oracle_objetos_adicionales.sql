-- =========================================================
-- Objetos adicionales Oracle para Arepas El Poblado
-- Vistas, funciones, procedimientos, tipos y triggers
-- =========================================================

-- =========================================================
-- VISTAS
-- =========================================================

CREATE OR REPLACE VIEW vw_usuarios_detalle AS
SELECT
    u.id,
    u.nombre,
    u.email,
    u.telefono,
    r.nombre_rol,
    eu.nombre_estado_usuario,
    u.created_at,
    u.updated_at
FROM usuarios u
JOIN rol r ON r.id = u.rol_id
JOIN estado_usuario eu ON eu.id = u.estado_usuario_id;
/

CREATE OR REPLACE VIEW vw_productos_catalogo AS
SELECT
    p.id,
    DBMS_LOB.SUBSTR(p.descripcion, 4000, 1) AS descripcion,
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
    p.id,
    p.numero_pedido,
    u.nombre AS cliente,
    u.email,
    u.telefono,
    p.total,
    ep.nombre_estado_pedido,
    p.fecha_pedido,
    p.fecha_entrega,
    p.created_at,
    p.updated_at
FROM pedidos p
JOIN usuarios u ON u.id = p.usuario_id
JOIN estado_pedido ep ON ep.id = p.estado_pedido_id;
/

CREATE OR REPLACE VIEW vw_detalles_pedido_resumen AS
SELECT
    dp.id,
    dp.pedido_id,
    p.numero_pedido,
    dp.producto_id,
    DBMS_LOB.SUBSTR(pr.descripcion, 4000, 1) AS producto,
    dp.cantidad,
    dp.precio_unitario,
    dp.subtotal,
    dp.created_at
FROM detalles_pedido dp
JOIN pedidos p ON p.id = dp.pedido_id
JOIN productos pr ON pr.id = dp.producto_id;
/

CREATE OR REPLACE VIEW vw_carrito_resumen AS
SELECT
    c.id AS carrito_id,
    u.nombre AS cliente,
    u.email,
    ci.id AS item_id,
    DBMS_LOB.SUBSTR(p.descripcion, 4000, 1) AS producto,
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
    NVL(SUM(dp.subtotal), 0) AS total_recaudado
FROM categoria c
LEFT JOIN productos p ON p.categoria_id = c.id
LEFT JOIN detalles_pedido dp ON dp.producto_id = p.id
GROUP BY c.id, c.nombre;
/

CREATE OR REPLACE VIEW vw_pedidos_por_usuario AS
SELECT
    u.id AS usuario_id,
    u.nombre,
    u.email,
    COUNT(p.id) AS total_pedidos,
    NVL(SUM(p.total), 0) AS total_gastado
FROM usuarios u
LEFT JOIN pedidos p ON p.usuario_id = u.id
GROUP BY u.id, u.nombre, u.email;
/

CREATE OR REPLACE VIEW vw_productos_stock_bajo AS
SELECT
    p.id,
    DBMS_LOB.SUBSTR(p.descripcion, 4000, 1) AS descripcion,
    p.stock,
    c.nombre AS categoria
FROM productos p
JOIN categoria c ON c.id = p.categoria_id
WHERE NVL(p.stock, 0) <= 10;
/

CREATE OR REPLACE VIEW vw_pedidos_pendientes AS
SELECT
    p.id,
    p.numero_pedido,
    u.nombre AS cliente,
    p.total,
    ep.nombre_estado_pedido,
    p.fecha_pedido
FROM pedidos p
JOIN usuarios u ON u.id = p.usuario_id
JOIN estado_pedido ep ON ep.id = p.estado_pedido_id
WHERE LOWER(ep.nombre_estado_pedido) IN ('pendiente', 'en proceso');
/

CREATE OR REPLACE VIEW vw_top_productos_vendidos AS
SELECT
    pr.id AS producto_id,
    DBMS_LOB.SUBSTR(pr.descripcion, 4000, 1) AS descripcion,
    NVL(SUM(dp.cantidad), 0) AS total_unidades_vendidas,
    NVL(SUM(dp.subtotal), 0) AS total_recaudado
FROM productos pr
LEFT JOIN detalles_pedido dp ON dp.producto_id = pr.id
GROUP BY pr.id, DBMS_LOB.SUBSTR(pr.descripcion, 4000, 1);
/

CREATE OR REPLACE VIEW vw_usuarios_activos AS
SELECT
    u.id,
    u.nombre,
    u.email,
    u.telefono,
    eu.nombre_estado_usuario
FROM usuarios u
JOIN estado_usuario eu ON eu.id = u.estado_usuario_id
WHERE LOWER(eu.nombre_estado_usuario) = 'activo';
/

CREATE OR REPLACE VIEW vw_ventas_por_dia AS
SELECT
    TRUNC(fecha_pedido) AS fecha_venta,
    COUNT(id) AS total_pedidos,
    NVL(SUM(total), 0) AS total_vendido
FROM pedidos
WHERE fecha_pedido IS NOT NULL
GROUP BY TRUNC(fecha_pedido);
/

-- =========================================================
-- FUNCIONES
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

CREATE OR REPLACE FUNCTION fn_total_carrito_usuario(p_usuario_id NUMBER)
RETURN NUMBER
IS
    v_total NUMBER;
BEGIN
    SELECT NVL(SUM(ci.cantidad * p.precio), 0)
    INTO v_total
    FROM carritos c
    JOIN carrito_items ci ON ci.carrito_id = c.id
    JOIN productos p ON p.id = ci.producto_id
    WHERE c.usuario_id = p_usuario_id;

    RETURN v_total;
END;
/

CREATE OR REPLACE FUNCTION fn_total_pedidos_usuario(p_usuario_id NUMBER)
RETURN NUMBER
IS
    v_total NUMBER;
BEGIN
    SELECT COUNT(*)
    INTO v_total
    FROM pedidos
    WHERE usuario_id = p_usuario_id;

    RETURN v_total;
END;
/

CREATE OR REPLACE FUNCTION fn_stock_suficiente(p_producto_id NUMBER, p_cantidad NUMBER)
RETURN NUMBER
IS
    v_stock NUMBER;
BEGIN
    SELECT NVL(stock, 0)
    INTO v_stock
    FROM productos
    WHERE id = p_producto_id;

    IF v_stock >= NVL(p_cantidad, 0) THEN
        RETURN 1;
    END IF;

    RETURN 0;
END;
/

CREATE OR REPLACE FUNCTION fn_nombre_categoria_producto(p_producto_id NUMBER)
RETURN VARCHAR2
IS
    v_categoria VARCHAR2(100);
BEGIN
    SELECT c.nombre
    INTO v_categoria
    FROM productos p
    JOIN categoria c ON c.id = p.categoria_id
    WHERE p.id = p_producto_id;

    RETURN v_categoria;
END;
/

CREATE OR REPLACE FUNCTION fn_total_vendido_producto(p_producto_id NUMBER)
RETURN NUMBER
IS
    v_total NUMBER;
BEGIN
    SELECT NVL(SUM(subtotal), 0)
    INTO v_total
    FROM detalles_pedido
    WHERE producto_id = p_producto_id;

    RETURN v_total;
END;
/

CREATE OR REPLACE FUNCTION fn_ultimo_pedido_usuario(p_usuario_id NUMBER)
RETURN VARCHAR2
IS
    v_numero VARCHAR2(50);
BEGIN
    SELECT numero_pedido
    INTO v_numero
    FROM (
        SELECT numero_pedido
        FROM pedidos
        WHERE usuario_id = p_usuario_id
        ORDER BY NVL(fecha_pedido, created_at) DESC, id DESC
    )
    WHERE ROWNUM = 1;

    RETURN v_numero;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN NULL;
END;
/

-- =========================================================
-- PROCEDIMIENTOS
-- =========================================================

CREATE OR REPLACE PROCEDURE sp_actualizar_stock_producto(
    p_producto_id IN NUMBER,
    p_cantidad IN NUMBER,
    p_operacion IN VARCHAR2 DEFAULT 'RESTAR'
)
AS
BEGIN
    IF UPPER(p_operacion) = 'SUMAR' THEN
        UPDATE productos
        SET stock = NVL(stock, 0) + NVL(p_cantidad, 0),
            updated_at = SYSTIMESTAMP
        WHERE id = p_producto_id;
    ELSE
        UPDATE productos
        SET stock = GREATEST(NVL(stock, 0) - NVL(p_cantidad, 0), 0),
            updated_at = SYSTIMESTAMP
        WHERE id = p_producto_id;
    END IF;
END;
/

CREATE OR REPLACE PROCEDURE sp_cambiar_estado_pedido(
    p_pedido_id IN NUMBER,
    p_estado_pedido_id IN NUMBER
)
AS
BEGIN
    UPDATE pedidos
    SET estado_pedido_id = p_estado_pedido_id,
        updated_at = SYSTIMESTAMP
    WHERE id = p_pedido_id;
END;
/

CREATE OR REPLACE PROCEDURE sp_actualizar_estado_usuario(
    p_usuario_id IN NUMBER,
    p_estado_usuario_id IN NUMBER
)
AS
BEGIN
    UPDATE usuarios
    SET estado_usuario_id = p_estado_usuario_id,
        updated_at = SYSTIMESTAMP
    WHERE id = p_usuario_id;
END;
/

CREATE OR REPLACE PROCEDURE sp_registrar_telefono_usuario(
    p_usuario_id IN NUMBER,
    p_telefono IN VARCHAR2
)
AS
BEGIN
    UPDATE usuarios
    SET telefono = p_telefono,
        updated_at = SYSTIMESTAMP
    WHERE id = p_usuario_id;
END;
/

CREATE OR REPLACE PROCEDURE sp_recalcular_total_pedido(
    p_pedido_id IN NUMBER
)
AS
BEGIN
    UPDATE pedidos p
    SET total = (
        SELECT NVL(SUM(dp.subtotal), 0)
        FROM detalles_pedido dp
        WHERE dp.pedido_id = p_pedido_id
    ),
    updated_at = SYSTIMESTAMP
    WHERE p.id = p_pedido_id;
END;
/

CREATE OR REPLACE PROCEDURE sp_limpiar_carrito_usuario(
    p_usuario_id IN NUMBER
)
AS
BEGIN
    DELETE FROM carrito_items
    WHERE carrito_id IN (
        SELECT id
        FROM carritos
        WHERE usuario_id = p_usuario_id
    );

    UPDATE carritos
    SET updated_at = SYSTIMESTAMP
    WHERE usuario_id = p_usuario_id;
END;
/

CREATE OR REPLACE PROCEDURE sp_cancelar_pedido(
    p_pedido_id IN NUMBER
)
AS
    v_estado_cancelado NUMBER;
BEGIN
    SELECT id
    INTO v_estado_cancelado
    FROM estado_pedido
    WHERE LOWER(nombre_estado_pedido) = 'cancelado'
      AND ROWNUM = 1;

    UPDATE pedidos
    SET estado_pedido_id = v_estado_cancelado,
        updated_at = SYSTIMESTAMP
    WHERE id = p_pedido_id;
END;
/

CREATE OR REPLACE PROCEDURE sp_marcar_pedido_completado(
    p_pedido_id IN NUMBER
)
AS
    v_estado_completado NUMBER;
BEGIN
    SELECT id
    INTO v_estado_completado
    FROM estado_pedido
    WHERE LOWER(nombre_estado_pedido) = 'completado'
      AND ROWNUM = 1;

    UPDATE pedidos
    SET estado_pedido_id = v_estado_completado,
        updated_at = SYSTIMESTAMP
    WHERE id = p_pedido_id;
END;
/

CREATE OR REPLACE PROCEDURE sp_reactivar_usuario(
    p_usuario_id IN NUMBER
)
AS
    v_estado_activo NUMBER;
BEGIN
    SELECT id
    INTO v_estado_activo
    FROM estado_usuario
    WHERE LOWER(nombre_estado_usuario) = 'activo'
      AND ROWNUM = 1;

    UPDATE usuarios
    SET estado_usuario_id = v_estado_activo,
        updated_at = SYSTIMESTAMP
    WHERE id = p_usuario_id;
END;
/

CREATE OR REPLACE PROCEDURE sp_desactivar_producto_sin_stock(
    p_producto_id IN NUMBER
)
AS
BEGIN
    UPDATE productos
    SET activo = CASE WHEN NVL(stock, 0) <= 0 THEN 0 ELSE activo END,
        updated_at = SYSTIMESTAMP
    WHERE id = p_producto_id;
END;
/

-- =========================================================
-- TIPOS
-- =========================================================

CREATE OR REPLACE TYPE t_lista_emails AS TABLE OF VARCHAR2(120);
/

CREATE OR REPLACE TYPE t_lista_telefonos AS TABLE OF VARCHAR2(20);
/

CREATE OR REPLACE TYPE t_lista_categorias AS TABLE OF VARCHAR2(100);
/

CREATE OR REPLACE TYPE t_lista_numeros_pedido AS TABLE OF VARCHAR2(50);
/

CREATE OR REPLACE TYPE t_lista_ids_producto AS TABLE OF NUMBER;
/

CREATE OR REPLACE TYPE t_etiquetas_cortas AS VARRAY(20) OF VARCHAR2(100);
/

CREATE OR REPLACE TYPE t_lista_direcciones AS TABLE OF VARCHAR2(200);
/

CREATE OR REPLACE TYPE t_lista_estados_cortos AS VARRAY(10) OF VARCHAR2(50);
/

-- =========================================================
-- TRIGGERS
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

CREATE OR REPLACE TRIGGER trg_pedidos_bu_updated_at_extra
BEFORE UPDATE ON pedidos
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER trg_carritos_bu_updated_at
BEFORE UPDATE ON carritos
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/
