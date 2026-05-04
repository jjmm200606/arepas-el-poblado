from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Rol(Base):
    __tablename__ = "rol"

    id = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String(50), nullable=False, unique=True)
    usuarios = relationship("Usuario", back_populates="rol_rel")


class EstadoUsuario(Base):
    __tablename__ = "estado_usuario"

    id = Column(Integer, primary_key=True, index=True)
    nombre_estado_usuario = Column(String(50), nullable=False, unique=True)
    usuarios = relationship("Usuario", back_populates="estado_usuario_rel")


class EstadoPedido(Base):
    __tablename__ = "estado_pedido"

    id = Column(Integer, primary_key=True, index=True)
    nombre_estado_pedido = Column(String(50), nullable=False, unique=True)
    pedidos = relationship("Pedido", back_populates="estado_pedido_rel")


class Categoria(Base):
    __tablename__ = "categoria"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    productos = relationship("Producto", back_populates="categoria_rel")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    telefono = Column(String(20))
    rol_id = Column(Integer, ForeignKey("rol.id"), nullable=False)
    estado_usuario_id = Column(Integer, ForeignKey("estado_usuario.id"), nullable=False)

    rol_rel = relationship("Rol", back_populates="usuarios")
    estado_usuario_rel = relationship("EstadoUsuario", back_populates="usuarios")
    pedidos = relationship("Pedido", back_populates="usuario")
    carrito = relationship("Carrito", back_populates="usuario", uselist=False)

    @property
    def rol(self):
        return self.rol_rel.nombre_rol if self.rol_rel else None

    @property
    def estado(self):
        return (
            self.estado_usuario_rel.nombre_estado_usuario
            if self.estado_usuario_rel
            else None
        )


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(Text)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=True, default=0)
    imagen = Column(String(255))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    imagen_url = Column(Text)
    categoria_id = Column(Integer, ForeignKey("categoria.id"), nullable=False)

    categoria_rel = relationship("Categoria", back_populates="productos")
    detalles = relationship("DetallePedido", back_populates="producto")
    carrito_items = relationship("CarritoItem", back_populates="producto")

    @property
    def nombre(self):
        return self.categoria_rel.nombre if self.categoria_rel else "Producto"


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cliente_direccion = Column(Text)
    total = Column(Numeric(10, 2), nullable=False, default=0)
    numero_pedido = Column(String(50))
    fecha_pedido = Column(DateTime)
    fecha_entrega = Column(DateTime)
    notas = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    estado_pedido_id = Column(Integer, ForeignKey("estado_pedido.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="pedidos")
    estado_pedido_rel = relationship("EstadoPedido", back_populates="pedidos")
    detalles = relationship(
        "DetallePedido",
        back_populates="pedido",
        cascade="all, delete-orphan",
    )

    @property
    def estado(self):
        return (
            self.estado_pedido_rel.nombre_estado_pedido
            if self.estado_pedido_rel
            else None
        )

    @property
    def cliente_nombre(self):
        return self.usuario.nombre if self.usuario else ""

    @property
    def cliente_email(self):
        return self.usuario.email if self.usuario else ""

    @property
    def cliente_telefono(self):
        return self.usuario.telefono if self.usuario else ""


class DetallePedido(Base):
    __tablename__ = "detalles_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime)

    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles")


class Carrito(Base):
    __tablename__ = "carritos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    usuario = relationship("Usuario", back_populates="carrito")
    items = relationship("CarritoItem", back_populates="carrito", cascade="all, delete-orphan")


class CarritoItem(Base):
    __tablename__ = "carrito_items"

    id = Column(Integer, primary_key=True, index=True)
    carrito_id = Column(Integer, ForeignKey("carritos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    carrito = relationship("Carrito", back_populates="items")
    producto = relationship("Producto", back_populates="carrito_items")
