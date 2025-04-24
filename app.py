import streamlit as st
import pandas as pd
import random
from io import BytesIO
 
st.set_page_config(page_title="Asignación de Marcas", layout="centered")
 
st.title("Asignacion de Prueba a Realizar - A/B Test Mibanco")
st.markdown("Sube tu archivo y se asignarán aleatoriamente las marcas **Adam Milo** y **Manpower** por grupo de agencia.")
st.markdown("Tener en cuenta que despues del procesamiento unicamente tendremos las posiciones de **Asesor de Negocios I, II y III**")
st.markdown("Una vez generado el archivo compartirlo con el equipo de **People Analytics - Credicorp**. Gracias :)")
 
# Subida del archivo base
grupos_file = st.file_uploader("1. Sube el archivo base que contiene el grupo de agencia", type=["xlsx"])
 
# Subida del archivo del usuario
datos_file = st.file_uploader("2. Sube el archivo de requerimientos", type=["xlsx"])
 
if grupos_file and datos_file:
    try:
        grupos_df = pd.read_excel(grupos_file)
        user_df = pd.read_excel(datos_file)
        user_df = user_df[['NOMBRE CENTRO COSTO','CODIGO RQ','PUESTO REQUERIDO']]
        grupos_df = grupos_df[['NOMBRE CENTRO COSTO','cluster']]

        user_df = user_df[user_df['PUESTO REQUERIDO'].isin([])
 
        # Validar columnas mínimas
        if 'NOMBRE CENTRO COSTO' not in grupos_df.columns or 'NOMBRE CENTRO COSTO' not in user_df.columns:
            st.error("Ambos archivos deben tener la columna 'NOMBRE CENTRO COSTO'.")
        else:
            # Hacer merge por agencia
            df = pd.merge(user_df, grupos_df, on="NOMBRE CENTRO COSTO", how="left")
 
            if 'NOMBRE CENTRO COSTO' not in df.columns:
                st.error("El archivo base debe contener la columna 'NOMBRE CENTRO COSTO'.")
            else:
                def asignar_marcas(grupo):
                    n = len(grupo)
                    mitad = n // 2
                    marcas = ["Adam Milo"] * mitad + ["Manpower"] * (n - mitad)
                    random.seed(2025)
                    random.shuffle(marcas)
                    grupo["Prueba"] = marcas
                    return grupo
 
                resultado_df = df.groupby("cluster", group_keys=False).apply(asignar_marcas)
 
                st.success("¡Asignación completada!")
 
                st.dataframe(resultado_df)
 
                # Preparar para descarga
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
