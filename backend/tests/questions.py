import argparse
import pandas as pd
from datetime import datetime
from src.engine.llm_service import LLMService

TEST_QUESTIONS = [
    # --- CATEGORÍA: CORPORATIVO (Corp) ---
    {"cat": "Corp", "q": "¿Cuál es la misión de Dollarcity?"},
    {"cat": "Corp", "q": "¿Desde qué año opera la empresa y cuál es su visión de crecimiento?"},
    
    # --- CATEGORÍA: PRODUCTOS Y PRECIOS (Prod) ---
    {"cat": "Prod", "q": "¿Puedo comprar productos a través de la página web o pedir domicilio?"},
    {"cat": "Prod", "q": "¿Cómo puedo conocer el precio de un artículo antes de ir a la tienda?"},
    {"cat": "Prod", "q": "¿Tienen un sistema para consultar la disponibilidad de inventario en una sucursal específica?"},
    
    # --- CATEGORÍA: UBICACIONES Y HORARIOS (Loc) ---
    {"cat": "Loc", "q": "¿Dónde puedo encontrar las direcciones y los horarios de atención de las tiendas?"},
    {"cat": "Loc", "q": "¿Cómo puedo enterarme de las próximas aperturas de Dollarcity en Colombia?"},
    
    # --- CATEGORÍA: SERVICIOS Y PAGOS (Serv) ---
    {"cat": "Serv", "q": "¿Cuál es el proceso para obtener la factura electrónica de mi compra?"},
    {"cat": "Serv", "q": "¿Aceptan pagos con Nequi y se puede usar código QR?"},
    {"cat": "Serv", "q": "¿Qué pasa si pierdo mi tarjeta de regalo o si se agota el saldo?"},
    {"cat": "Serv", "q": "¿Las tarjetas de regalo tienen fecha de vencimiento?"},
    
    # --- CATEGORÍA: POLÍTICAS Y TRÁMITES (Policy) ---
    {"cat": "Policy", "q": "¿Cuáles son las condiciones y el plazo máximo para solicitar un cambio de producto?"},
    {"cat": "Policy", "q": "¿Está permitido el ingreso de mascotas a las tiendas de Dollarcity?"},
    {"cat": "Policy", "q": "¿Dollarcity ofrece el modelo de negocio por franquicias?"},
    
    # --- CATEGORÍA: TALENTO HUMANO Y PROVEEDORES (HR/Prov) ---
    {"cat": "HR", "q": "¿Cómo puedo aplicar a una vacante para trabajar con ustedes?"},
    {"cat": "HR", "q": "¿Es cierto que Dollarcity solicita pagos para exámenes médicos en los procesos de selección?"},
    {"cat": "Prov", "q": "Soy dueño de un inmueble y quiero ofrecérselo a Dollarcity, ¿qué debo hacer?"},
    
    # --- CATEGORÍA: GUARDRAILS / NEGATIVAS (Guard) ---
    {"cat": "Guard", "q": "¿Tienen servicio de guardería para niños dentro de las tiendas?"},
    {"cat": "Guard", "q": "¿Venden medicamentos de venta libre o bajo fórmula médica?"},
    {"cat": "Guard", "q": "¿Cuáles son las promociones actuales en las tiendas de la competencia como Tiendas D1 o Ara?"}
]

def run_evaluation(limit: int = None):
    print(f"\n[EVALUACIÓN] Iniciando batería de pruebas...")
    service = LLMService()
    results = []
    output_path = "data/evaluation_results.csv"
    
    # Limitar preguntas si se solicita
    questions_to_run = TEST_QUESTIONS[:limit] if limit else TEST_QUESTIONS

    for i, item in enumerate(questions_to_run):
        print(f"[{i+1}/{len(questions_to_run)}] Pregunta ({item['cat']}): {item['q']}")
        
        start_time = datetime.now()
        try:
            response = service.get_chat_response(item['q'])
            status = "SUCCESS"
        except Exception as e:
            response = f"Error: {str(e)}"
            status = "ERROR"
            
        latency = (datetime.now() - start_time).total_seconds()

        # Registro del resultado
        res_data = {
            "ID": i + 1,
            "Categoria": item['cat'],
            "Pregunta": item['q'],
            "Respuesta_LLM": response,
            "Latencia_Seg": round(latency, 2),
            "Status": status
        }
        results.append(res_data)

        # GUARDADO INCREMENTAL: Actualizar el CSV en cada iteración
        pd.DataFrame(results).to_csv(output_path, index=False, encoding='utf-8')

    print(f"\n[INFO] Pruebas terminadas. Resultados guardados en: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Número de preguntas a probar")
    args = parser.parse_args()
    
    run_evaluation(limit=args.limit)