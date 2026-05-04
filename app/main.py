
#venv\Scripts\activate
#python -m uvicorn app.main:app --reload


from pathlib import Path
from datetime import datetime, timedelta
from email.message import EmailMessage
import hashlib
import hmac
import json
import random
import smtplib
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode

from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import joinedload
from starlette.middleware.sessions import SessionMiddleware
import os

# Instancia principal de la app FastAPI
app = FastAPI()


# Importar SQLAlchemy y modelos
from .database import SessionLocal
from .models import (
    Categoria,
    DetallePedido,
    EstadoPedido,
    EstadoUsuario,
    Pedido,
    Producto,
    Rol,
    Usuario,
)

BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_STORE_PATH = Path(
    os.getenv(
        "AUTH_STORE_PATH",
        "/tmp/auth_state.json" if os.getenv("VERCEL") else str(BASE_DIR / "data" / "auth_state.json"),
    )
)

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


def generar_codigo():
    return f"{random.randint(100000, 999999)}"


def asegurar_auth_store():
    AUTH_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not AUTH_STORE_PATH.exists():
        AUTH_STORE_PATH.write_text(
            json.dumps(
                {
                    "pending_verification_emails": [],
                    "verification_codes": {},
                    "reset_codes": {},
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )


def cargar_auth_store():
    asegurar_auth_store()
    with AUTH_STORE_PATH.open("r", encoding="utf-8") as archivo:
        datos = json.load(archivo)
    datos.setdefault("pending_verification_emails", [])
    datos.setdefault("verification_codes", {})
    datos.setdefault("reset_codes", {})
    return datos


def guardar_auth_store(datos):
    asegurar_auth_store()
    with AUTH_STORE_PATH.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=True, indent=2)


def email_verificado_externamente(email):
    datos = cargar_auth_store()
    pendientes = {correo.lower() for correo in datos["pending_verification_emails"]}
    return email.lower() not in pendientes


def marcar_email_pendiente(email):
    datos = cargar_auth_store()
    pendientes = {correo.lower() for correo in datos["pending_verification_emails"]}
    pendientes.add(email.lower())
    datos["pending_verification_emails"] = sorted(pendientes)
    guardar_auth_store(datos)


def marcar_email_verificado(email):
    datos = cargar_auth_store()
    pendientes = {correo.lower() for correo in datos["pending_verification_emails"]}
    pendientes.discard(email.lower())
    datos["pending_verification_emails"] = sorted(pendientes)
    datos["verification_codes"].pop(email.lower(), None)
    guardar_auth_store(datos)


def preparar_codigo_externo(email, tipo):
    datos = cargar_auth_store()
    codigo = generar_codigo()
    registro = {
        "code": codigo,
        "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat(),
    }
    datos[tipo][email.lower()] = registro
    guardar_auth_store(datos)
    return codigo


def validar_codigo_externo(email, codigo, tipo):
    datos = cargar_auth_store()
    registro = datos[tipo].get(email.lower())
    if not registro:
        return False

    expiracion = registro.get("expires_at")
    try:
        expira = datetime.fromisoformat(expiracion)
    except (TypeError, ValueError):
        return False

    return registro.get("code") == codigo.strip() and expira >= datetime.now()


def limpiar_codigo_externo(email, tipo):
    datos = cargar_auth_store()
    datos[tipo].pop(email.lower(), None)
    guardar_auth_store(datos)


def obtener_rol_por_nombre(db, nombre):
    return db.query(Rol).filter(Rol.nombre_rol == nombre).first()


def obtener_estado_usuario_por_nombre(db, nombre):
    return (
        db.query(EstadoUsuario)
        .filter(EstadoUsuario.nombre_estado_usuario == nombre)
        .first()
    )


def obtener_estado_pedido_por_nombre(db, nombre):
    return (
        db.query(EstadoPedido)
        .filter(EstadoPedido.nombre_estado_pedido == nombre)
        .first()
    )


def obtener_o_crear_categoria(db, nombre):
    nombre_limpio = (nombre or "").strip()
    if not nombre_limpio:
        nombre_limpio = "Producto"

    categoria = db.query(Categoria).filter(Categoria.nombre == nombre_limpio).first()
    if not categoria:
        categoria = Categoria(nombre=nombre_limpio)
        db.add(categoria)
        db.flush()
    return categoria


def validar_password_seguro(password):
    errores = []
    especiales = "!@#$%^&*()_+-=[]{}|;:,.<>?/"

    if len(password) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres")
    if not any(caracter.islower() for caracter in password):
        errores.append("La contraseña debe incluir una letra minúscula")
    if not any(caracter.isupper() for caracter in password):
        errores.append("La contraseña debe incluir una letra mayúscula")
    if not any(caracter.isdigit() for caracter in password):
        errores.append("La contraseña debe incluir un número")
    if not any(caracter in especiales for caracter in password):
        errores.append("La contraseña debe incluir un carácter especial")

    return errores


def construir_correo_html(titulo, saludo, mensaje_principal, codigo, nota):
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f4f8f6;font-family:Arial,sans-serif;color:#17322a;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f8f6;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #dcefe3;">
          <tr>
            <td style="background:linear-gradient(135deg,#0f9d58,#12b76a);padding:26px 32px;color:#ffffff;">
              <div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;opacity:0.92;">Arepas El Poblado</div>
              <h1 style="margin:10px 0 0;font-size:30px;line-height:1.2;">{titulo}</h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 16px;font-size:18px;line-height:1.6;">{saludo}</p>
              <p style="margin:0 0 24px;font-size:16px;line-height:1.7;color:#35584c;">{mensaje_principal}</p>

              <div style="margin:0 0 24px;padding:22px 18px;background:#f6fffa;border:1px solid #b8ead0;border-radius:14px;text-align:center;">
                <div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:#0f9d58;margin-bottom:10px;">Código</div>
                <div style="font-size:34px;font-weight:700;letter-spacing:0.18em;color:#0d6f43;">{codigo}</div>
              </div>

              <p style="margin:0 0 12px;font-size:15px;line-height:1.7;color:#4d6a60;">{nota}</p>
              <p style="margin:24px 0 0;font-size:15px;line-height:1.7;color:#35584c;">Si no solicitaste este proceso, puedes ignorar este mensaje.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px;background:#f9fcfa;border-top:1px solid #e6f2eb;font-size:13px;line-height:1.6;color:#638274;">
              Arepas El Poblado<br>
              Villavicencio, Meta, Colombia
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def construir_correo_verificacion_html(nombre, codigo):
    return construir_correo_html(
        "Confirma tu correo",
        f"Hola {nombre},",
        "Usa el siguiente código para confirmar tu correo y activar tu acceso.",
        codigo,
        "Este código vence en 15 minutos.",
    )


def construir_correo_reset_html(nombre, codigo):
    return construir_correo_html(
        "Recupera tu contraseña",
        f"Hola {nombre},",
        "Usa este código para continuar con el cambio de tu contraseña.",
        codigo,
        "Este código vence en 15 minutos.",
    )


def enviar_correo(destinatario, asunto, mensaje, html=None):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = (os.getenv("SMTP_PASSWORD") or "").replace(" ", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "no-reply@arepaselpoblado.com")

    smtp_incompleto = (
        not smtp_host
        or not smtp_user
        or not smtp_password
        or smtp_user.startswith("tu_")
        or smtp_password.startswith("tu_")
    )

    if smtp_incompleto:
        print(f"[CORREO NO CONFIGURADO] Para: {destinatario} | {asunto} | {mensaje}")
        return False

    email = EmailMessage()
    email["From"] = smtp_from
    email["To"] = destinatario
    email["Subject"] = asunto
    email.set_content(mensaje)
    if html:
        email.add_alternative(html, subtype="html")

    with smtplib.SMTP(smtp_host, smtp_port) as servidor:
        servidor.starttls()
        servidor.login(smtp_user, smtp_password)
        servidor.send_message(email)

    return True


def preparar_codigo_verificacion(usuario):
    return preparar_codigo_externo(usuario.email, "verification_codes")


def preparar_codigo_reset(usuario):
    return preparar_codigo_externo(usuario.email, "reset_codes")


def enviar_codigo_verificacion(usuario):
    codigo = preparar_codigo_verificacion(usuario)
    mensaje_texto = (
        f"Hola {usuario.nombre},\n\n"
        f"Tu codigo de confirmacion es: {codigo}\n"
        "Este codigo vence en 15 minutos.\n\n"
        "Arepas El Poblado"
    )
    mensaje_html = construir_correo_verificacion_html(usuario.nombre, codigo)
    enviar_correo(
        usuario.email,
        "Confirma tu correo - Arepas El Poblado",
        mensaje_texto,
        mensaje_html,
    )


def enviar_codigo_reset(usuario):
    codigo = preparar_codigo_reset(usuario)
    mensaje_texto = (
        f"Hola {usuario.nombre},\n\n"
        f"Tu codigo para recuperar la contraseña es: {codigo}\n"
        "Este codigo vence en 15 minutos.\n\n"
        "Arepas El Poblado"
    )
    mensaje_html = construir_correo_reset_html(usuario.nombre, codigo)
    enviar_correo(
        usuario.email,
        "Recupera tu contraseña - Arepas El Poblado",
        mensaje_texto,
        mensaje_html,
    )


@app.get("/preview/correo/{tipo}", response_class=HTMLResponse)
def preview_correo(tipo: str, nombre: str = "Juan Jose Martinez", codigo: str = "216602"):
    if tipo == "verificacion":
        return HTMLResponse(construir_correo_verificacion_html(nombre, codigo))
    if tipo == "reset":
        return HTMLResponse(construir_correo_reset_html(nombre, codigo))
    return HTMLResponse("<h1>Tipo de correo no valido</h1>", status_code=404)


def obtener_base_url(request: Request):
    return str(request.base_url).rstrip("/")


def pesos_a_centavos(valor):
    return int((Decimal(str(valor)) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def generar_firma_integridad_wompi(referencia, monto_centavos, moneda="COP"):
    secreto_integridad = os.getenv("WOMPI_INTEGRITY_SECRET")
    if not secreto_integridad:
        raise ValueError("Falta configurar WOMPI_INTEGRITY_SECRET")

    cadena = f"{referencia}{monto_centavos}{moneda}{secreto_integridad}"
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()


def crear_url_checkout_wompi(request: Request, pedido):
    llave_publica = os.getenv("WOMPI_PUBLIC_KEY")
    if not llave_publica:
        raise ValueError("Falta configurar WOMPI_PUBLIC_KEY")

    monto_centavos = pesos_a_centavos(pedido.total)
    referencia = pedido.numero_pedido
    moneda = "COP"
    firma = generar_firma_integridad_wompi(referencia, monto_centavos, moneda)
    base_url = obtener_base_url(request)

    parametros = {
        "public-key": llave_publica,
        "currency": moneda,
        "amount-in-cents": monto_centavos,
        "reference": referencia,
        "signature:integrity": firma,
        "redirect-url": f"{base_url}/pago/wompi/resultado",
    }

    if pedido.cliente_email and "@" in pedido.cliente_email:
        parametros["customer-data:email"] = pedido.cliente_email
    if pedido.cliente_nombre:
        parametros["customer-data:full-name"] = pedido.cliente_nombre
    if pedido.cliente_telefono:
        parametros["customer-data:phone-number"] = pedido.cliente_telefono
        parametros["customer-data:phone-number-prefix"] = "+57"
    if pedido.cliente_direccion:
        parametros["shipping-address:address-line-1"] = pedido.cliente_direccion
        parametros["shipping-address:country"] = "CO"
        parametros["shipping-address:city"] = os.getenv("WOMPI_SHIPPING_CITY", "Medellin")
        parametros["shipping-address:region"] = os.getenv("WOMPI_SHIPPING_REGION", "Antioquia")
        parametros["shipping-address:name"] = pedido.cliente_nombre or "Cliente"
        parametros["shipping-address:phone-number"] = pedido.cliente_telefono or ""

    return "https://checkout.wompi.co/p/?" + urlencode(parametros)


def obtener_valor_por_ruta(datos, ruta):
    valor = datos
    for parte in ruta.split("."):
        if not isinstance(valor, dict) or parte not in valor:
            return None
        valor = valor[parte]
    return valor


def validar_evento_wompi(payload, checksum_header):
    secreto_eventos = os.getenv("WOMPI_EVENTS_SECRET")
    if not secreto_eventos:
        return False

    firma = payload.get("signature") or {}
    propiedades = firma.get("properties") or []
    checksum = checksum_header or firma.get("checksum")
    timestamp = payload.get("timestamp")

    if not checksum or timestamp is None:
        return False

    datos = payload.get("data") or {}
    partes = []
    for propiedad in propiedades:
        valor = obtener_valor_por_ruta(datos, propiedad)
        if valor is None:
            return False
        partes.append(str(valor))

    cadena = "".join(partes) + str(timestamp) + secreto_eventos
    calculado = hashlib.sha256(cadena.encode("utf-8")).hexdigest()
    return hmac.compare_digest(calculado.lower(), str(checksum).lower())


def mapear_estado_wompi(estado):
    estados = {
        "APPROVED": "pagado",
        "DECLINED": "cancelado",
        "VOIDED": "cancelado",
        "ERROR": "cancelado",
        "PENDING": "pendiente",
    }
    return estados.get(estado, "pendiente")


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
    productos = db.query(Producto).options(joinedload(Producto.categoria_rel)).all()
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
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("pedido.html", {
        "request": request,
        "usuario": usuario
    })


@app.get("/mis-pedidos", response_class=HTMLResponse)
def mis_pedidos(request: Request):
    usuario = obtener_usuario(request)
    if not usuario or not usuario.get("email"):
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    usuario_db = db.query(Usuario).filter(Usuario.email == usuario["email"]).first()
    if not usuario_db:
        db.close()
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    pedidos = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.estado_pedido_rel),
            joinedload(Pedido.detalles)
            .joinedload(DetallePedido.producto)
            .joinedload(Producto.categoria_rel),
        )
        .filter(Pedido.usuario_id == usuario_db.id)
        .order_by(Pedido.fecha_pedido.desc(), Pedido.id.desc())
        .all()
    )
    db.close()

    return templates.TemplateResponse(
        "mis_pedidos.html",
        {
            "request": request,
            "usuario": usuario,
            "pedidos": pedidos,
        },
    )


@app.get("/pago/wompi/resultado", response_class=HTMLResponse)
def resultado_pago_wompi(request: Request):
    usuario = obtener_usuario(request)
    transaction_id = request.query_params.get("id")
    return templates.TemplateResponse("pago_wompi_resultado.html", {
        "request": request,
        "usuario": usuario,
        "transaction_id": transaction_id
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

    if not usuario or usuario.password != password:
        db.close()
        return templates.TemplateResponse("login.html", {
            "request": request,
            "usuario": None,
            "error": "Email o contraseña incorrectos"
        })

    if not email_verificado_externamente(usuario.email):
        enviar_codigo_verificacion(usuario)
        db.close()
        return templates.TemplateResponse("verificar_email.html", {
            "request": request,
            "usuario": None,
            "email": email,
            "error": "Debes confirmar tu correo antes de iniciar sesión.",
            "mensaje": "Te enviamos un nuevo código de confirmación."
        })

    request.session["usuario"] = {
        "id": usuario.id,
        "email": usuario.email,
        "nombre": usuario.nombre,
        "rol": usuario.rol
    }
    rol = usuario.rol
    db.close()

    if rol == "admin":
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
    errores.extend(validar_password_seguro(password))
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
        telefono=None,
        rol_id=obtener_rol_por_nombre(db, "cliente").id,
        estado_usuario_id=obtener_estado_usuario_por_nombre(db, "activo").id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(nuevo_usuario)
    db.flush()
    marcar_email_pendiente(email)
    enviar_codigo_verificacion(nuevo_usuario)
    db.commit()
    db.close()
    return templates.TemplateResponse("verificar_email.html", {
        "request": request,
        "usuario": None,
        "email": email,
        "error": None,
        "mensaje": "Cuenta creada. Te enviamos un código para confirmar tu correo."
    })


@app.get("/verificar-email", response_class=HTMLResponse)
def verificar_email_form(request: Request, email: str = ""):
    return templates.TemplateResponse("verificar_email.html", {
        "request": request,
        "usuario": None,
        "email": email,
        "error": None,
        "mensaje": None
    })


@app.post("/verificar-email", response_class=HTMLResponse)
def verificar_email(
    request: Request,
    email: str = Form(...),
    codigo: str = Form(...)
):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        db.close()
        return templates.TemplateResponse("verificar_email.html", {
            "request": request,
            "usuario": None,
            "email": email,
            "error": "No encontramos una cuenta con ese correo.",
            "mensaje": None
        })

    codigo_valido = validar_codigo_externo(email, codigo, "verification_codes")

    if not codigo_valido:
        db.close()
        return templates.TemplateResponse("verificar_email.html", {
            "request": request,
            "usuario": None,
            "email": email,
            "error": "El código no es válido o ya venció.",
            "mensaje": None
        })

    marcar_email_verificado(email)
    db.close()
    return templates.TemplateResponse("login.html", {
        "request": request,
        "usuario": None,
        "error": None,
        "mensaje": "Correo confirmado. Ya puedes iniciar sesión."
    })


@app.post("/reenviar-verificacion", response_class=HTMLResponse)
def reenviar_verificacion(request: Request, email: str = Form(...)):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario:
        enviar_codigo_verificacion(usuario)
    db.close()
    return templates.TemplateResponse("verificar_email.html", {
        "request": request,
        "usuario": None,
        "email": email,
        "error": None,
        "mensaje": "Si el correo existe, enviamos un nuevo código."
    })


@app.get("/recuperar-password", response_class=HTMLResponse)
def recuperar_password_form(request: Request):
    return templates.TemplateResponse("recuperar_password.html", {
        "request": request,
        "usuario": None,
        "error": None,
        "mensaje": None
    })


@app.post("/recuperar-password", response_class=HTMLResponse)
def recuperar_password(request: Request, email: str = Form(...)):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario:
        enviar_codigo_reset(usuario)
    db.close()
    return templates.TemplateResponse("reset_password.html", {
        "request": request,
        "usuario": None,
        "email": email,
        "error": None,
        "mensaje": "Si el correo existe, enviamos un código para recuperar la contraseña."
    })


@app.get("/reset-password", response_class=HTMLResponse)
def reset_password_form(request: Request, email: str = ""):
    return templates.TemplateResponse("reset_password.html", {
        "request": request,
        "usuario": None,
        "email": email,
        "error": None,
        "mensaje": None
    })


@app.post("/reset-password", response_class=HTMLResponse)
def reset_password(
    request: Request,
    email: str = Form(...),
    codigo: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...)
):
    if password != password_confirm:
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "usuario": None,
            "email": email,
            "error": "Las contraseñas no coinciden.",
            "mensaje": None
        })

    errores_password = validar_password_seguro(password)
    if errores_password:
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "usuario": None,
            "email": email,
            "error": " | ".join(errores_password),
            "mensaje": None
        })

    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    codigo_valido = (
        usuario
        and validar_codigo_externo(email, codigo, "reset_codes")
    )

    if not codigo_valido:
        db.close()
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "usuario": None,
            "email": email,
            "error": "El código no es válido o ya venció.",
            "mensaje": None
        })

    usuario.password = password
    db.commit()
    limpiar_codigo_externo(email, "reset_codes")
    db.close()
    return templates.TemplateResponse("login.html", {
        "request": request,
        "usuario": None,
        "error": None,
        "mensaje": "Contraseña actualizada. Ya puedes iniciar sesión."
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
    productos = db.query(Producto).options(joinedload(Producto.categoria_rel)).all()
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
    categoria = obtener_o_crear_categoria(db, nombre)
    nuevo_producto = Producto(
        categoria_id=categoria.id,
        precio=precio,
        stock=stock,
        descripcion=descripcion,
        created_at=datetime.now(),
        updated_at=datetime.now(),
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
    pedidos = db.query(Pedido).options(
        joinedload(Pedido.usuario),
        joinedload(Pedido.estado_pedido_rel),
    ).all()
    response = templates.TemplateResponse("admin_pedidos.html", {
        "request": request,
        "usuario": usuario,
        "pedidos": pedidos
    })
    db.close()
    return response


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
        estado_db = obtener_estado_pedido_por_nombre(db, estado)
        if not estado_db:
            db.close()
            return JSONResponse({"exito": False, "mensaje": "Estado no valido"}, status_code=400)
        pedido.estado_pedido_id = estado_db.id
        pedido.updated_at = datetime.now()
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
        if not usuario or not usuario.get("email"):
            return JSONResponse({
                "exito": False,
                "mensaje": "Debes iniciar sesion para realizar un pedido"
            }, status_code=401)

        productos = data.get("productos", [])
        if not productos:
            return JSONResponse({
                "exito": False,
                "mensaje": "No hay productos en el pedido"
            }, status_code=400)

        db = SessionLocal()
        try:
            usuario_db = db.query(Usuario).filter(Usuario.email == usuario["email"]).first()
            if not usuario_db:
                return JSONResponse({
                    "exito": False,
                    "mensaje": "Usuario no encontrado"
                }, status_code=404)

            total = float(data.get("total", 0) or 0)
            timestamp = datetime.now()

            metodo_pago = data.get("metodoPago", "")
            estado_inicial = "pendiente"
            estado_pedido = obtener_estado_pedido_por_nombre(db, estado_inicial)

            nuevo_pedido = Pedido(
                usuario_id=usuario_db.id,
                cliente_direccion=data.get("direccion", ""),
                total=total,
                estado_pedido_id=estado_pedido.id,
                numero_pedido=f"PED-{timestamp.strftime('%Y%m%d%H%M%S%f')}",
                fecha_pedido=timestamp,
                notas=(
                    f"Metodo de pago: {metodo_pago}"
                    f" | Observaciones: {data.get('observaciones', '')}"
                ),
                created_at=timestamp,
                updated_at=timestamp,
            )
            db.add(nuevo_pedido)
            db.flush()
            pedido_id = nuevo_pedido.id

            telefono_form = (data.get("telefono") or "").strip()
            if telefono_form and telefono_form != (usuario_db.telefono or ""):
                usuario_db.telefono = telefono_form
                usuario_db.updated_at = timestamp

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
                    created_at=timestamp,
                )
                db.add(detalle)

            checkout_wompi = None
            if metodo_pago == "Wompi":
                checkout_wompi = {
                    "url": crear_url_checkout_wompi(request, nuevo_pedido),
                    "referencia": nuevo_pedido.numero_pedido
                }

            db.commit()

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        return JSONResponse({
            "exito": True,
            "id_pedido": pedido_id,
            "wompi": checkout_wompi,
            "mensaje": "Pedido creado correctamente"
        })

    except Exception as e:
        return JSONResponse({
            "exito": False,
            "mensaje": f"Error al crear el pedido: {str(e)}"
        }, status_code=400)


@app.post("/api/wompi/webhook")
async def webhook_wompi(request: Request):
    payload = await request.json()
    checksum_header = request.headers.get("X-Event-Checksum")

    if not validar_evento_wompi(payload, checksum_header):
        return JSONResponse({"error": "Firma de evento invalida"}, status_code=401)

    if payload.get("event") != "transaction.updated":
        return JSONResponse({"exito": True, "mensaje": "Evento ignorado"})

    transaccion = (payload.get("data") or {}).get("transaction") or {}
    referencia = transaccion.get("reference")
    estado_wompi = transaccion.get("status")
    transaction_id = transaccion.get("id")

    if not referencia:
        return JSONResponse({"error": "Evento sin referencia"}, status_code=400)

    db = SessionLocal()
    try:
        pedido = db.query(Pedido).filter(Pedido.numero_pedido == referencia).first()
        if not pedido:
            return JSONResponse({"error": "Pedido no encontrado"}, status_code=404)

        estado_db = obtener_estado_pedido_por_nombre(db, mapear_estado_wompi(estado_wompi))
        if estado_db:
            pedido.estado_pedido_id = estado_db.id
        pedido.updated_at = datetime.now()

        detalle_wompi = f"Wompi transaction_id: {transaction_id} | estado: {estado_wompi}"
        if pedido.notas:
            if "Wompi transaction_id:" not in pedido.notas:
                pedido.notas = f"{pedido.notas} | {detalle_wompi}"
        else:
            pedido.notas = detalle_wompi

        db.commit()
        return JSONResponse({"exito": True, "mensaje": "Pedido actualizado"})
    finally:
        db.close()


# ===== GESTIÓN DE USUARIOS =====

# ===== GESTIÓN DE USUARIOS =====
@app.get("/admin/usuarios", response_class=HTMLResponse)
def admin_usuarios(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    db = SessionLocal()
    usuarios = db.query(Usuario).options(
        joinedload(Usuario.rol_rel),
        joinedload(Usuario.estado_usuario_rel),
    ).all()
    response = templates.TemplateResponse("admin_usuarios.html", {
        "request": request,
        "usuario": usuario,
        "usuarios": usuarios
    })
    db.close()
    return response


# ===== RUTAS PARA CONTENIDO AJAX =====

@app.get("/admin/productos/content", response_class=HTMLResponse)
def admin_productos_content(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    db = SessionLocal()
    productos = db.query(Producto).options(joinedload(Producto.categoria_rel)).all()
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
    pedidos = db.query(Pedido).options(
        joinedload(Pedido.usuario),
        joinedload(Pedido.estado_pedido_rel),
    ).all()
    response = templates.TemplateResponse("admin_pedidos_content.html", {
        "request": request,
        "usuario": usuario,
        "pedidos": pedidos
    })
    db.close()
    return response



@app.get("/admin/usuarios/content", response_class=HTMLResponse)
def admin_usuarios_content(request: Request):
    if not requiere_admin(request):
        return RedirectResponse(url="/login", status_code=303)

    usuario = obtener_usuario(request)
    db = SessionLocal()
    usuarios = db.query(Usuario).options(
        joinedload(Usuario.rol_rel),
        joinedload(Usuario.estado_usuario_rel),
    ).all()
    response = templates.TemplateResponse("admin_usuarios_content.html", {
        "request": request,
        "usuario": usuario,
        "usuarios": usuarios
    })
    db.close()
    return response


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

    if estado not in {"activo", "inactivo", "bloqueado"}:
        return JSONResponse({"exito": False, "mensaje": "Estado no valido"}, status_code=400)

    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        db.close()
        return JSONResponse({"exito": False, "mensaje": "Usuario no encontrado"}, status_code=404)

    rol_db = obtener_rol_por_nombre(db, rol)
    estado_db = obtener_estado_usuario_por_nombre(db, estado)
    if not rol_db or not estado_db:
        db.close()
        return JSONResponse({"exito": False, "mensaje": "Datos no validos"}, status_code=400)

    usuario.rol_id = rol_db.id
    usuario.estado_usuario_id = estado_db.id
    usuario.updated_at = datetime.now()
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
