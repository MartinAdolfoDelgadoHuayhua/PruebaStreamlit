import streamlit as st
import pandas as pd
import random
from io import BytesIO

st.set_page_config(page_title="Asignación de Marcas", layout="centered")

st.title("Asignacion de Prueba a Realizar - A/B Test Mibanco")
st.markdown("Sube tu archivo y se asignarán aleatoriamente las marcas **Adam Milo** y **Manpower** por grupo de agencia.")
st.markdown("Tener en cuenta que después del procesamiento unicamente tendremos las posiciones de **Asesor de Negocios I, II y III**.")
st.markdown("Una vez generado el archivo, compartirlo con el equipo de **People Analytics - Credicorp**.")

# Subida del archivo base
grupos_file = st.file_uploader("1. Sube el archivo base que contiene el grupo de agencia", type=["xlsx"])

# Subida del archivo de requerimientos
datos_file = st.file_uploader("2. Sube el archivo de requerimientos", type=["xlsx"])

# Subida del archivo histórico (opcional)
historico_file = st.file_uploader("3. (Opcional) Sube el archivo histórico de asignaciones anteriores", type=["xlsx"])

if grupos_file and datos_file:
    try:
        grupos_df = pd.read_excel(grupos_file)
        user_df = pd.read_excel(datos_file)
        user_df = user_df[['NUMERO CENTRO COSTO', 'CODIGO RQ', 'PUESTO REQUERIDO']]
        grupos_df = grupos_df[['NUMERO CENTRO COSTO', 'cluster']]

        # Filtrar puestos válidos para el experimento
        user_df = user_df[user_df['PUESTO REQUERIDO'].isin([
            'ASESOR DE NEGOCIOS 2',
            'ASESOR DE NEGOCIOS 1',
            'ASESOR DE NEGOCIOS 3',
            'ASESOR DE NEGOCIOS  3  ',
            'ASESOR DE NEGOCIOS  1  ',
            'ASESOR DE NEGOCIOS  2  '
        ])].reset_index(drop=True)

        # Validar columnas mínimas
        if 'NUMERO CENTRO COSTO' not in grupos_df.columns or 'NUMERO CENTRO COSTO' not in user_df.columns:
            st.error("El archivo de requerimiento no tiene la columna 'NUMERO CENTRO COSTO'.")
        else:
            # Merge de bases
            df = pd.merge(user_df, grupos_df, on="NUMERO CENTRO COSTO", how="left")

            # Inicializar conteos históricos
            total_adam = 0
            total_manpower = 0
            usar_historico = False

            if historico_file:
                historico_df = pd.read_excel(historico_file)
                if 'Prueba' in historico_df.columns:
                    total_adam = historico_df[historico_df['Prueba'] == 'Adam Milo'].shape[0]
                    total_manpower = historico_df[historico_df['Prueba'] == 'Manpower'].shape[0]
                    usar_historico = True
                    st.info(f"Histórico cargado: {total_adam} Adam Milo vs {total_manpower} Manpower asignados anteriormente.")
                else:
                    st.warning("El archivo histórico no tiene columna 'Prueba'. Se ignorará el histórico.")

            # Función de asignación
            def asignar_marcas(grupo):
                if usar_historico:
                    nonlocal total_adam, total_manpower
                    marcas = []
                    for _ in range(len(grupo)):
                        if total_adam < total_manpower:
                            marcas.append("Adam Milo")
                            total_adam += 1
                        elif total_manpower < total_adam:
                            marcas.append("Manpower")
                            total_manpower += 1
                        else:
                            marca = random.choice(["Adam Milo", "Manpower"])
                            marcas.append(marca)
                            if marca == "Adam Milo":
                                total_adam += 1
                            else:
                                total_manpower += 1
                    grupo["Prueba"] = marcas
                else:
                    # Si no hay histórico, simple 50/50 en cada cluster
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
