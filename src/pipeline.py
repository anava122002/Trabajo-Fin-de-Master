from bronze.todostuslibros_info import control_flujo
from silver.silver_ttl import crear_df, crear_silver_ttl
from silver.silver_spi import merge_spi, crear_silver_spi
from gold.gold_metadata import crear_gold

# =================================================================================
# PIPELINE PARA LA CREACIÓN DE LAS CAPAS DE DATOS
# =================================================================================

def pipeline(bronze:bool=False):
    print("INICIO DEL PIPELINE\n")

    # --- BRONZE
    if bronze:
        control_flujo()

    # --- SILVER
    data_ttl = crear_df()
    silver_ttl = crear_silver_ttl(data_ttl)

    data_spi = merge_spi()
    silver_spi = crear_silver_spi(data_spi)

    # --- GOLD
    gold_metadata = crear_gold()

    print("FIN DEL PIPELINE")


