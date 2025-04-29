import streamlit as st
import pandas as pd
import random
from io import BytesIO

st.set_page_config(page_title="Asignación de Marcas", layout="centered")

st.title("Asignacion de Prueba a Realizar - A/B Test Mibanco")
st.markdown("Sube tu archivo y se asignarán aleatoriamente las marcas **Adam Milo** y **Manpower** por grupo de agencia.")
st.markdown("Tener en cuenta que después del procesamiento unicamente tendremos las posiciones de **Asesor de Negocios I, II y III**.")
st.markdown("Una vez generado el archivo, compartirlo con el equipo de **People Analytics - Credicorp**.")
st.markdown("Si no es el primer requerimento del mes - colocar en un excel los requerimentos previos con las marcas asignadas para que se tome como un historico en la asignacion")

# Subida del archivo base
grupos_file = st.file_uploader("1. Sube el archivo base que contiene el grupo de agencia", type=["xlsx"])

# Subida del archivo de requerimientos
datos_file = st.file_uploader("2. Sube el archivo de requerimientos", type=["xlsx"])

# Subida del archivo histórico (opcional)
historico_file = st.file_uploader("3. (Opcional) Sube el archivo histórico de asignaciones anteriores del mes", type=["xlsx"])

# Activar pesos manuales (opcional)
usar_pesos = st.checkbox("¿Deseas definir manualmente los porcentajes de asignación? (Opcional)")

if usar_pesos:
    porcentaje_adam = st.slider("Porcentaje de Adam Milo", min_value=0, max_value=100, value=50)
    porcentaje_manpower = 100 - porcentaje_adam
    st.write(f"Porcentaje de Manpower: {porcentaje_manpower}%")

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
                
                random.seed(2025)
                n = len(grupo)
            
                if usar_pesos:
                    # Asignación usando pesos definidos manualmente
                    cantidad_adam = round(n * porcentaje_adam / 100)
                    cantidad_manpower = n - cantidad_adam
                    marcas = ["Adam Milo"] * cantidad_adam + ["Manpower"] * cantidad_manpower
                    random.shuffle(marcas)
                    grupo["Prueba"] = marcas
            
                elif usar_historico:
                    # Conteos locales, sin usar nonlocal
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
                    marcas = ["Manpower"] * mitad + ["Adam Milo"] * (n - mitad)
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
