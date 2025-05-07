import streamlit as st
import pandas as pd
import random
from io import BytesIO
import openpyxl

st.set_page_config(page_title="Asignación de Marcas", layout="centered")

st.title("Asignacion de Prueba a Realizar - A/B Test Mibanco")
st.markdown("Sube tu archivo y se asignarán aleatoriamente las marcas **Adam Milo** y **Manpower** por grupo de agencia.")
st.markdown("Tener en cuenta que despues del procesamiento unicamente tendremos las posiciones de **Asesor de Negocios I, II y III**")
st.markdown("Una vez generado el archivo compartirlo con el equipo de **People Analytics - Credicorp**")

# Archivos a subir
grupos_file = st.file_uploader("1. Sube el archivo base que contiene el grupo de agencias **(Compartido por PA Credicorp)** ", type=["xlsx"])
datos_file = st.file_uploader("2. Sube el archivo de requerimientos", type=["xlsx"])
historico_file = st.file_uploader("3. (Opcional) Sube el archivo histórico de asignaciones anteriores del mes", type=["xlsx"])

# Opcional: pesos manuales
usar_pesos = st.checkbox("¿Deseas usar pesos personalizados?")
if usar_pesos:
    porcentaje_adam = st.slider("Porcentaje de asignación para Adam Milo", min_value=0, max_value=100, value=50)
    st.write(f"Se asignará {porcentaje_adam}% a Adam Milo y {100 - porcentaje_adam}% a Manpower")

if grupos_file and datos_file:
    try:
        grupos_df = pd.read_excel(grupos_file)
        user_df = pd.read_excel(datos_file)

        user_df = user_df[['NUMERO CENTRO COSTO', 'CODIGO RQ', 'PUESTO REQUERIDO', 'FUERZA COMERCIAL']]
        grupos_df = grupos_df[['NUMERO CENTRO COSTO', 'cluster']]

        # Normalización de valores con espacios extra
        reemplazos = {'ASESOR DE NEGOCIOS  1  ': 'ASESOR DE NEGOCIOS 1','ASESOR DE NEGOCIOS  2  ': 'ASESOR DE NEGOCIOS 2','ASESOR DE NEGOCIOS  3  ': 'ASESOR DE NEGOCIOS 3'}
        user_df['PUESTO REQUERIDO'] = user_df['PUESTO REQUERIDO'].replace(reemplazos)

        # Filtrar solo puestos válidos
        puestos_validos = [
            'ASESOR DE NEGOCIOS 1',
            'ASESOR DE NEGOCIOS 2',
            'ASESOR DE NEGOCIOS 3'
        ]
        user_df = user_df[user_df['PUESTO REQUERIDO'].isin(puestos_validos)].reset_index(drop=True)

        if 'NUMERO CENTRO COSTO' not in grupos_df.columns or 'NUMERO CENTRO COSTO' not in user_df.columns:
            st.error("El archivo de requerimiento no tiene la columna 'NUMERO CENTRO COSTO'.")
        else:
            # Merge con grupos
            df = pd.merge(user_df, grupos_df, on="NUMERO CENTRO COSTO", how="left")

            # Leer histórico si se subió
            usar_historico = False
            historico_counts = {}

            if historico_file:
                historico_df = pd.read_excel(historico_file)
                if all(col in historico_df.columns for col in ["FUERZA COMERCIAL", "PUESTO REQUERIDO", "cluster", "Prueba"]):
                    reemplazos = {'ASESOR DE NEGOCIOS  1  ': 'ASESOR DE NEGOCIOS 1','ASESOR DE NEGOCIOS  2  ': 'ASESOR DE NEGOCIOS 2','ASESOR DE NEGOCIOS  3  ': 'ASESOR DE NEGOCIOS 3'}
                    historico_df['PUESTO REQUERIDO'] = historico_df['PUESTO REQUERIDO'].replace(reemplazos)
                    historico_counts = historico_df.groupby(
                        ["FUERZA COMERCIAL", "PUESTO REQUERIDO", "cluster", "Prueba"]
                    ).size().unstack(fill_value=0).to_dict(orient="index")
                    usar_historico = not usar_pesos
                else:
                    st.warning("El histórico no tiene las columnas necesarias ('FUERZA COMERCIAL', 'PUESTO REQUERIDO', 'cluster', 'Prueba'). No se usará para balancear.")

            # Asignar marcas
            def asignar_marcas(grupo):
                random.seed(2025)
                n = len(grupo)

                if usar_pesos:
                    cantidad_adam = round(n * porcentaje_adam / 100)
                    cantidad_manpower = n - cantidad_adam
                    marcas = ["Adam Milo"] * cantidad_adam + ["Manpower"] * cantidad_manpower
                    random.shuffle(marcas)
                    grupo["Prueba"] = marcas

                elif usar_historico:
                    key = (grupo["FUERZA COMERCIAL"].iloc[0], grupo["PUESTO REQUERIDO"].iloc[0], grupo["cluster"].iloc[0])
                    adam_count = historico_counts.get(key, {}).get("Adam Milo", 0)
                    manpower_count = historico_counts.get(key, {}).get("Manpower", 0)

                    marcas = []
                    for _ in range(n):
                        if adam_count < manpower_count:
                            marcas.append("Adam Milo")
                            adam_count += 1
                        elif manpower_count < adam_count:
                            marcas.append("Manpower")
                            manpower_count += 1
                        else:
                            marca = random.choice(["Adam Milo", "Manpower"])
                            marcas.append(marca)
                            if marca == "Adam Milo":
                                adam_count += 1
                            else:
                                manpower_count += 1

                    grupo["Prueba"] = marcas

                else:
                    mitad = n // 2
                    marcas = ["Adam Milo"] * mitad + ["Manpower"] * (n - mitad)
                    random.shuffle(marcas)
                    grupo["Prueba"] = marcas

                return grupo

            resultado_df = df.groupby(["FUERZA COMERCIAL", "PUESTO REQUERIDO", "cluster"], group_keys=False).apply(asignar_marcas)

            st.success("¡Asignación completada!")
            st.dataframe(resultado_df)

            output = BytesIO()
            resultado_df.to_excel(output, index=False)
            st.download_button(
                label="Descargar Excel con marcas asignadas",
                data=output.getvalue(),
                file_name="resultado_marcas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Error al procesar los archivos: {e}")
