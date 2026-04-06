import streamlit as st
import pandas as pd

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Sistema de Inventario", layout="wide")

# ------------------ FUNCION CLAVE ------------------
def recalcular_inventario():
    inv = pd.DataFrame(columns=["Producto", "Cantidad", "Unidad"])

    for _, row in st.session_state["movimientos"].iterrows():
        producto = row["Producto"]
        cantidad = row["Cantidad"]
        unidad = row["Unidad"]

        if producto not in inv["Producto"].values:
            nuevo = pd.DataFrame([[producto, 0, unidad]],
                                 columns=["Producto", "Cantidad", "Unidad"])
            inv = pd.concat([inv, nuevo], ignore_index=True)

        if row["Tipo"] == "Entrada":
            inv.loc[inv["Producto"] == producto, "Cantidad"] += cantidad
        else:
            inv.loc[inv["Producto"] == producto, "Cantidad"] -= cantidad

    inv = inv.reset_index(drop=True)
    st.session_state["inventario"] = inv

# ------------------ HEADER ------------------
st.title("📦 Sistema de Inventario")

# ------------------ USUARIOS ------------------
usuarios = {
    "admin": {"password": "1234", "rol": "admin"},
    "empleado": {"password": "1234", "rol": "empleado"}
}

# ------------------ LOGIN ------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.subheader("Login")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        if user in usuarios and usuarios[user]["password"] == password:
            st.session_state["login"] = True
            st.session_state["usuario"] = user
            st.session_state["rol"] = usuarios[user]["rol"]
            st.rerun()
        else:
            st.error("Datos incorrectos")

    st.stop()

# ------------------ SIDEBAR ------------------
st.sidebar.write(f"👤 Usuario: {st.session_state['usuario']}")

# 🔓 Cerrar sesión (sin borrar datos)
if st.sidebar.button("🔓 Cerrar sesión"):
    st.session_state["login"] = False
    st.session_state.pop("usuario", None)
    st.session_state.pop("rol", None)
    st.rerun()

# ------------------ DATOS ------------------
if "inventario" not in st.session_state:
    st.session_state["inventario"] = pd.DataFrame(columns=["Producto", "Cantidad", "Unidad"])

if "movimientos" not in st.session_state:
    st.session_state["movimientos"] = pd.DataFrame(columns=[
        "Producto", "Cantidad", "Unidad", "Tipo", "Usuario",
        "Proveedor", "Destino", "Sucursal"
    ])

# ------------------ MENU ------------------
menu = st.sidebar.selectbox("Menú", ["Dashboard", "Entradas", "Salidas", "Reportes"])

# ------------------ LISTAS ------------------
proveedores = [
    "Murgati","Gema","Harina","Pealpan","Alim. Cargo","Cajas","La güera",
    "Sigma","Manolo","El Ingrato","3B","Abastos","Jam’s","Gas",
    "La Costeña","Queso y Jamón","Chorizo"
]

franquicias = {
    "Lukarios Pizza": ["Salk", "Topacio", "Cactus", "Los Pinos"],
    "Blue Pizzas": ["Pozos", "Santa María del Río", "Centro", "Paseo"],
    "El Gran Jardín": ["Central"]
}

# ------------------ DASHBOARD ------------------
if menu == "Dashboard":
    st.subheader("📊 Inventario actual")

    recalcular_inventario()
    df = st.session_state["inventario"]

    if df.empty:
        st.info("No hay inventario registrado")
    else:
        st.dataframe(df, use_container_width=True)

    # ALERTAS
    st.subheader("⚠️ Alertas de escasez")
    bajos = df[df["Cantidad"] < 10]

    if not bajos.empty:
        st.warning("Productos bajos:")
        st.dataframe(bajos)
    else:
        st.success("Inventario en buen estado")

    # GRAFICA
    st.subheader("📊 Stock real por producto")
    if not df.empty:
        df_ordenado = df.sort_values(by="Cantidad", ascending=False)
        st.bar_chart(df_ordenado.set_index("Producto")["Cantidad"])

# ------------------ ENTRADAS ------------------
elif menu == "Entradas":
    st.subheader("📥 Registrar Entrada")

    producto = st.text_input("Producto")
    cantidad = st.number_input("Cantidad", min_value=0.0)
    unidad = st.selectbox("Unidad", ["kg", "L", "mg", "paquete", "pieza"])
    proveedor = st.selectbox("Proveedor", proveedores)

    if st.button("Agregar Entrada"):
        if producto and cantidad > 0:
            nuevo = pd.DataFrame([[producto, cantidad, unidad, "Entrada",
                                   st.session_state["usuario"], proveedor, None, None]],
                                 columns=st.session_state["movimientos"].columns)

            st.session_state["movimientos"] = pd.concat(
                [st.session_state["movimientos"], nuevo], ignore_index=True
            )

            recalcular_inventario()
            st.success("Entrada registrada")
            st.rerun()

    st.subheader("Historial de Entradas")
    df = st.session_state["movimientos"]
    st.dataframe(df[df["Tipo"] == "Entrada"].fillna("N/A"), use_container_width=True)

# ------------------ SALIDAS ------------------
elif menu == "Salidas":
    st.subheader("📤 Registrar Salida")

    recalcular_inventario()

    if st.session_state["inventario"].empty:
        st.warning("⚠️ No hay inventario disponible. Registra una entrada primero.")
    else:
        producto = st.selectbox("Producto", st.session_state["inventario"]["Producto"])
        cantidad = st.number_input("Cantidad", min_value=0.0)
        unidad = st.selectbox("Unidad", ["kg", "L", "mg", "paquete", "pieza"])

        franquicia = st.selectbox("Franquicia", list(franquicias.keys()))
        sucursal = st.selectbox("Sucursal", franquicias[franquicia])

        if st.button("Registrar Salida"):
            actual = st.session_state["inventario"].loc[
                st.session_state["inventario"]["Producto"] == producto, "Cantidad"
            ].values[0]

            if actual >= cantidad:
                nuevo = pd.DataFrame([[producto, cantidad, unidad, "Salida",
                                       st.session_state["usuario"], None,
                                       franquicia, sucursal]],
                                     columns=st.session_state["movimientos"].columns)

                st.session_state["movimientos"] = pd.concat(
                    [st.session_state["movimientos"], nuevo], ignore_index=True
                )

                recalcular_inventario()
                st.success("Salida registrada")
                st.rerun()
            else:
                st.error("No hay suficiente inventario")

    st.subheader("Historial de Salidas")
    df = st.session_state["movimientos"]
    st.dataframe(df[df["Tipo"] == "Salida"].fillna("N/A"), use_container_width=True)

# ------------------ REPORTES ------------------
elif menu == "Reportes":
    st.subheader("📑 Movimientos")

    df = st.session_state["movimientos"].fillna("N/A")
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        st.subheader("📊 Entradas vs Salidas")
        st.bar_chart(df["Tipo"].value_counts())

        st.subheader("📈 Productos más movidos")
        st.bar_chart(df["Producto"].value_counts())

    if st.session_state["rol"] == "admin":
        st.subheader("🗑️ Eliminar registro")

        index = st.number_input("Índice", min_value=0, step=1)

        if st.button("Eliminar"):
            if index < len(st.session_state["movimientos"]):
                st.session_state["movimientos"] = (
                    st.session_state["movimientos"]
                    .drop(index)
                    .reset_index(drop=True)
                )

                recalcular_inventario()
                st.success("Eliminado correctamente")
                st.rerun()
            else:
                st.error("Índice inválido")

        if st.button("⚠️ Reiniciar sistema"):
            st.session_state["movimientos"] = pd.DataFrame(columns=st.session_state["movimientos"].columns)
            st.session_state["inventario"] = pd.DataFrame(columns=st.session_state["inventario"].columns)
            st.success("Sistema limpio")
            st.rerun()