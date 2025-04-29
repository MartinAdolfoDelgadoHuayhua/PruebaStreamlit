import streamlit as st
import pandas as pd
import random
from io import BytesIO

st.set_page_config(page_title="Asignación de Marcas", layout="centered")

st.title("Asignación de Prueba a Realizar - A/B Test Mibanco")
st.markdown("Sube tus archivos y se asignarán aleatoriamente las marcas **Adam Milo** y **Manpower** por grupo de agencia, fuerza comercial y puesto requerido.")
st.markdown("**Nota:** Después del procesamiento solo se incluirán las posiciones **Asesor de Negocios I, II y III**.")
st.markdown("Una vez generado el archivo, compartirlo con el equipo de **People Analytics - Credicorp**.")

# Subida del archivo base
grupos_file = st.file_uploader("1. Sube el archivo base que contiene el grupo de agencia", type=["xlsx"])

# Subida del archivo de requerimientos
datos_file = st.file_uploader("2. Sube el archivo de requerimientos", type=["xlsx"])

# Subida del histórico (opcional)
historico_file = st.file_uploader("3. (Opcional) Sube el archivo histórico de asignaciones anteriores", type=["xlsx"])

usar_pesos = st.checkbox("¿Deseas asignar usando porcentajes personalizados?", value=False)

if usar_pesos:
    porcentaje_adam = st.slider("Porcentaje para Adam Milo", min_value=0, max_value=100, value=50)
    porcentaje_manpower = 100 - porcentaje_adam
    st.write(f"Adam Milo: {porcentaje_adam}% | Manpower: {porcentaje_manpower}%")

if grupos_file and datos_file:
    try:
        grupos_df = pd.read_excel(grupos_file)
        user_df = pd.read_excel(datos_file)

        # Validar columnas necesarias
        user_df = user_df[['NUMERO CENTRO COSTO', 'CODIGO RQ', 'PUESTO REQUERIDO', 'FUERZA COMERCIAL']]
        grupos_df = grupos_df[['NUMERO CENTRO COSTO', 'cluster']]

        # Filtro de puestos válidos
        puestos_validos = [
            'ASESOR DE NEGOCIOS 2',
            'ASESOR DE NEGOCIOS 1',
            'ASESOR DE NEGOCIOS 3',
            'ASESOR DE NEGOCIOS  3  ',
            'ASESOR DE NEGOCIOS  1  ',
            'ASESOR DE NEGOCIOS  2  '
        ]
        user_df = user_df[user_df['PUESTO REQUERIDO'].isin(puestos_validos)].reset_index(drop=True)
        reemplazos = {'ASESOR DE NEGOCIOS  1  ': 'ASESOR DE NEGOCIOS 1','ASESOR DE NEGOCIOS  2  ': 'ASESOR DE NEGOCIOS 2','ASESOR DE NEGOCIOS  3  ': 'ASESOR DE NEGOCIOS 3'}
        user_df['PUESTO REQUERIDO'] = user_df['PUESTO REQUERIDO'].replace(reemplazos)

        if 'NUMERO CENTRO COSTO' not in grupos_df.columns or 'NUMERO CENTRO COSTO' not in user_df.columns:
            st.error("El archivo no contiene la columna 'NUMERO CENTRO COSTO'.")
        else:
            # Merge
            df = pd.merge(user_df, grupos_df, on="NUMERO CENTRO COSTO", how="left")

            # Procesar histórico si se subió
            usar_historico = False
            total_adam = 0
            total_manpower = 0

            if historico_file:
                historico_df = pd.read_excel(historico_file)
                if "Prueba" in historico_df.columns:
                    total_adam = (historico_df["Prueba"] == "Adam Milo").sum()
                    total_manpower = (historico_df["Prueba"] == "Manpower").sum()
                    usar_historico = True
                else:
                    st.warning("El histórico no contiene la columna 'Prueba'. No se usará para balancear.")

            # Función de asignación
            def asignar_marcas(grupo):
                random.seed(2025)
                n = len(grupo)

                if usar_pesos:
                    # Asignación usando porcentajes definidos
                    cantidad_adam = round(n * porcentaje_adam / 100)
                    cantidad_manpower = n - cantidad_adam
                    marcas = ["Adam Milo"] * cantidad_adam + ["Manpower"] * cantidad_manpower
                    random.shuffle(marcas)
                    grupo["Prueba"] = marcas

                elif usar_historico:
                    # Asignación basada en histórico
                    marcas = []
                    count_adam = total_adam
                    count_manpower = total_manpower
                    for _ in range(len(grupo)):
                        if count_adam < count_manpower:
                            marcas.append("Adam Milo")
                            count_adam += 1
                        elif count_manpower < count_adam:
                            marcas.append("Manpower")
                            count_manpower += 1
                        else:
                            marca = random.choice(["Adam Milo", "Manpower"])
                            marcas.append(marca)
                            if marca == "Adam Milo":
                                count_adam += 1
                            else:
                                count_manpower += 1
                    grupo["Prueba"] = marcas

                else:
                    # Asignación simple 50/50
                    mitad = n // 2
                    marcas = ["Adam Milo"] * mitad + ["Manpower"] * (n - mitad)
                    random.shuffle(marcas)
                    grupo["Prueba"] = marcas

                return grupo

            # Agrupar por fuerza comercial, puesto requerido y cluster
            resultado_df = df.groupby(["FUERZA COMERCIAL", "PUESTO REQUERIDO", "cluster"], group_keys=False).apply(asignar_marcas)

            st.success("¡Asignación completada!")

            st.dataframe(resultado_df)

            # Exportar
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
