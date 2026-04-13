from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from .database import Base

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default='cliente')
    estado = Column(String(20), nullable=False, default='activo')
    pedidos = relationship('Pedido', back_populates='usuario')

class Producto(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=True, default=0)
    imagen = Column(String(255))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    imagen_url = Column(Text)
    detalles = relationship('DetallePedido', back_populates='producto')
    carrito_items = relationship('CarritoItem', back_populates='producto')

class Pedido(Base):
    __tablename__ = 'pedidos'
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    cliente_nombre = Column(String(150))
    cliente_email = Column(String(120))
    cliente_telefono = Column(String(20))
    cliente_direccion = Column(Text)
    total = Column(Float, nullable=False, default=0)
    estado = Column(String(30), nullable=False, default='Pendiente')
    numero_pedido = Column(String(50))
    fecha_pedido = Column(String)
    fecha_entrega = Column(String)
    notas = Column(Text)
    created_at = Column(String)
    updated_at = Column(String)
    usuario = relationship('Usuario', back_populates='pedidos')
    detalles = relationship('DetallePedido', back_populates='pedido', cascade='all, delete-orphan')

class DetallePedido(Base):
    __tablename__ = 'detalles_pedido'
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    nombre_producto = Column(String(150))
    imagen_producto = Column(String(255))
    created_at = Column(DateTime)
    pedido = relationship('Pedido', back_populates='detalles')
    producto = relationship('Producto', back_populates='detalles')


class Carrito(Base):
    __tablename__ = 'carritos'
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    items = relationship('CarritoItem', back_populates='carrito', cascade='all, delete-orphan')


class CarritoItem(Base):
    __tablename__ = 'carrito_items'
    id = Column(Integer, primary_key=True, index=True)
    carrito_id = Column(Integer, ForeignKey('carritos.id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    carrito = relationship('Carrito', back_populates='items')
    producto = relationship('Producto', back_populates='carrito_items')
