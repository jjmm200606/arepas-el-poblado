
#venv\Scripts\activate
#python -m uvicorn app.main:app --reload


from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os

# Instancia principal de la app FastAPI
app = FastAPI()


# Importar SQLAlchemy y modelos
from .database import SessionLocal
from .models import Usuario, Producto, Pedido, DetallePedido

BASE_DIR = Path(__file__).resolve().parent.parent

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "clave-secreta-arepas-2026")
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))




def obtener_usuario(request: Request):
    return request.session.get("usuario")


def requiere_admin(request: Request):
    usuario = request.session.get("usuario")
    return usuario and usuario.get("rol") == "admin"


@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    usuario = obtener_usuario(request)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "usuario": usuario
    })


@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request):
    usuario = obtener_usuario(request)
    db = SessionLocal()
    productos = db.query(Producto).all()
    db.close()
    return templates.TemplateResponse("catalogo.html", {
        "request": request,
        "usuario": usuario,
        "productos": productos
    })


@app.get("/carrito", response_class=HTMLResponse)
def carrito(request: Request):
    usuario = obtener_usuario(request)
    return templates.TemplateResponse("carrito.html", {
        "request": request,
        "usuario": usuario
    })


@app.get("/pedido", response_class=HTMLResponse)
def pedido(request: Request):
    usuario = obtener_usuario(request)
    return templates.TemplateResponse("pedido.html", {
        "request": request,
        "usuario": usuario
    })


@app.get("/contacto", response_class=HTMLResponse)
def contacto(request: Request):
    usuario = obtener_usuario(request)
    return templates.TemplateResponse("contacto.html", {
        "request": request,
        "usuario": usuario
    })


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "usuario": None,
        "error": None
    })


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    db.close()

    if not usuario or usuario.password != password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "usuario": None,
            "error": "Email o contraseña incorrectos"
        })

    request.session["usuario"] = {
        "email": usuario.email,
        "nombre": usuario.nombre,
        "rol": usuario.rol
    }

    if usuario.rol == "admin":
        return RedirectResponse(url="/admin", status_code=303)

    return RedirectResponse(url="/catalogo", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "error": None,
        "exito": False
    })


@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...)
):
    errores = []
    db = SessionLocal()
    # Validar que el email no exista
    if db.query(Usuario).filter(Usuario.email == email).first():
        errores.append("Este email ya está registrado")
    # Validar que las contraseñas coincidan
    if password != password_confirm:
        errores.append("Las contraseñas no coinciden")
    if len(password) < 6:
        errores.append("La contraseña debe tener al menos 6 caracteres")
    if not nombre or len(nombre.strip()) < 3:
        errores.append("El nombre debe tener al menos 3 caracteres")
    if "@" not in email or "." not in email:
        errores.append("El email no es válido")
    if errores:
        db.close()
        error_mensaje = " | ".join(errores)
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": error_mensaje,
            "exito": False
        })
    # Registrar el nuevo usuario en la base de datos
    nuevo_usuario = Usuario(
        nombre=nombre,
        email=email,
        password=password,
        rol="cliente",
        estado="activo"
    )
    db.add(nuevo_usuario)
    db.commit()
    db.close()
    return templates.TemplateResponse("register.html", {
        "request": request,
        "error": None,
        "exito": True
    })


@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "usuario": usuario
    })


# ===== GESTIÓN DE PRODUCTOS =====

@app.get("/admin/productos", response_class=HTMLResponse)
def admin_productos(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    db = SessionLocal()
    productos = db.query(Producto).all()
    db.close()
    return templates.TemplateResponse("admin_productos.html", {
        "request": request,
        "usuario": usuario,
        "productos": productos
    })



@app.post("/admin/productos/crear", response_class=HTMLResponse)
def crear_producto(
    request: Request,
    nombre: str = Form(...),
    precio: float = Form(...),
    stock: int = Form(...),
    descripcion: str = Form(...)
):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    nuevo_producto = Producto(
        nombre=nombre,
        precio=precio,
        stock=stock,
        descripcion=descripcion
    )
    db.add(nuevo_producto)
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/productos", status_code=303)



@app.post("/admin/productos/actualizar/{producto_id}", response_class=HTMLResponse)
def actualizar_producto(
    request: Request,
    producto_id: int,
    precio: float = Form(...),
    stock: int = Form(...)
):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        producto.precio = precio
        producto.stock = stock
        db.commit()
    db.close()
    return RedirectResponse(url="/admin/productos", status_code=303)



@app.get("/admin/productos/eliminar/{producto_id}", response_class=HTMLResponse)
def eliminar_producto(request: Request, producto_id: int):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        db.delete(producto)
        db.commit()
    db.close()
    return RedirectResponse(url="/admin/productos", status_code=303)


# ===== GESTIÓN DE PEDIDOS =====
@app.get("/admin/pedidos", response_class=HTMLResponse)
def admin_pedidos(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    db = SessionLocal()
    from .models import Pedido
    pedidos = db.query(Pedido).all()
    return templates.TemplateResponse("admin_pedidos.html", {
        "request": request,
        "usuario": usuario,
        "pedidos": pedidos
    })


@app.post("/admin/pedidos/actualizar/{pedido_id}")
def actualizar_estado_pedido(
    request: Request,
    pedido_id: int,
    estado: str = Form(...)
):
    if not requiere_admin(request):
        return JSONResponse({"error": "No autorizado"}, status_code=403)

    db = SessionLocal()
    from .models import Pedido
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido:
        pedido.estado = estado
        db.commit()
        db.close()
        return JSONResponse({"exito": True, "mensaje": "Estado actualizado"})
    db.close()
    return JSONResponse({"exito": False, "mensaje": "Pedido no encontrado"}, status_code=404)


@app.post("/api/crear-pedido")
async def crear_pedido(request: Request):
    """Crear un nuevo pedido desde el carrito y guardarlo en PostgreSQL."""
    try:
        data = await request.json()

        usuario = obtener_usuario(request)
        correo_usuario = usuario["email"] if usuario else "Cliente no registrado"

        productos = data.get("productos", [])
        if not productos:
            return JSONResponse({
                "exito": False,
                "mensaje": "No hay productos en el pedido"
            }, status_code=400)

        db = SessionLocal()
        try:
            usuario_db = None
            if usuario and usuario.get("email"):
                usuario_db = db.query(Usuario).filter(Usuario.email == usuario["email"]).first()

            total = float(data.get("total", 0) or 0)
            timestamp = datetime.now()

            nuevo_pedido = Pedido(
                usuario_id=usuario_db.id if usuario_db else None,
                cliente_nombre=data.get("nombre", "Sin nombre"),
                cliente_email=correo_usuario,
                cliente_telefono=data.get("telefono", ""),
                cliente_direccion=data.get("direccion", ""),
                total=total,
                estado="Pendiente",
                numero_pedido=f"PED-{timestamp.strftime('%Y%m%d%H%M%S')}",
                fecha_pedido=timestamp.strftime("%Y-%m-%d"),
                notas=(
                    f"Metodo de pago: {data.get('metodoPago', '')}"
                    f" | Observaciones: {data.get('observaciones', '')}"
                ),
                created_at=timestamp.isoformat(),
                updated_at=timestamp.isoformat(),
            )
            db.add(nuevo_pedido)
            db.flush()
            pedido_id = nuevo_pedido.id

            for item in productos:
                producto_id = item.get("id")
                cantidad = int(item.get("cantidad", 0) or 0)

                if not producto_id or cantidad <= 0:
                    continue

                producto_db = db.query(Producto).filter(Producto.id == producto_id).first()
                if not producto_db:
                    continue

                precio_unitario = float(item.get("precio", 0) or 0)
                if precio_unitario <= 0:
                    precio_unitario = float(producto_db.precio)

                subtotal = precio_unitario * cantidad

                detalle = DetallePedido(
                    pedido_id=nuevo_pedido.id,
                    producto_id=producto_id,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal,
                    nombre_producto=producto_db.nombre,
                    imagen_producto=producto_db.imagen_url or producto_db.imagen,
                    created_at=timestamp,
                )
                db.add(detalle)

            db.commit()

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        return JSONResponse({
            "exito": True,
            "id_pedido": pedido_id,
            "mensaje": "Pedido creado correctamente"
        })

    except Exception as e:
        return JSONResponse({
            "exito": False,
            "mensaje": f"Error al crear el pedido: {str(e)}"
        }, status_code=400)


# ===== GESTIÓN DE USUARIOS =====

# ===== GESTIÓN DE USUARIOS =====
@app.get("/admin/usuarios", response_class=HTMLResponse)
def admin_usuarios(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    db = SessionLocal()
    usuarios = db.query(Usuario).all()
    return templates.TemplateResponse("admin_usuarios.html", {
        "request": request,
        "usuario": usuario,
        "usuarios": usuarios
    })


# ===== RUTAS PARA CONTENIDO AJAX =====

@app.get("/admin/productos/content", response_class=HTMLResponse)
def admin_productos_content(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    db = SessionLocal()
    productos = db.query(Producto).all()
    db.close()
    return templates.TemplateResponse("admin_productos_content.html", {
        "request": request,
        "usuario": usuario,
        "productos": productos
    })



@app.get("/admin/pedidos/content", response_class=HTMLResponse)
def admin_pedidos_content(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    db = SessionLocal()
    from .models import Pedido
    pedidos = db.query(Pedido).all()
    return templates.TemplateResponse("admin_pedidos_content.html", {
        "request": request,
        "usuario": usuario,
        "pedidos": pedidos
    })



@app.get("/admin/usuarios/content", response_class=HTMLResponse)
def admin_usuarios_content(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    db = SessionLocal()
    usuarios = db.query(Usuario).all()
    return templates.TemplateResponse("admin_usuarios_content.html", {
        "request": request,
        "usuario": usuario,
        "usuarios": usuarios
    })


@app.post("/admin/usuarios/editar/{usuario_id}")
def editar_usuario_admin(
    request: Request,
    usuario_id: int,
    rol: str = Form(...),
    estado: str = Form(...)
):
    if not requiere_admin(request):
        return JSONResponse({"error": "No autorizado"}, status_code=403)

    if rol not in {"admin", "cliente"}:
        return JSONResponse({"exito": False, "mensaje": "Rol no valido"}, status_code=400)

    if estado not in {"activo", "inactivo"}:
        return JSONResponse({"exito": False, "mensaje": "Estado no valido"}, status_code=400)

    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        db.close()
        return JSONResponse({"exito": False, "mensaje": "Usuario no encontrado"}, status_code=404)

    usuario.rol = rol
    usuario.estado = estado
    db.commit()
    db.close()
    return JSONResponse({"exito": True, "mensaje": "Usuario actualizado"})


# ===== ELIMINAR PEDIDO DESDE ADMIN =====
@app.post("/admin/pedidos/eliminar/{pedido_id}")
def eliminar_pedido(request: Request, pedido_id: int):
    if not requiere_admin(request):
        return JSONResponse({"error": "No autorizado"}, status_code=403)

    db = SessionLocal()
    from .models import Pedido
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido:
        db.delete(pedido)
        db.commit()
        db.close()
        return JSONResponse({"exito": True, "mensaje": "Pedido eliminado"})
    db.close()
    return JSONResponse({"exito": False, "mensaje": "Pedido no encontrado"}, status_code=404)