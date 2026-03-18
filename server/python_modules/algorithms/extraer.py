import cv2
import numpy as np
import os
from pathlib import Path

def extraer_patron_simple(imagen_path, salida_path, 
                         r_min=0, r_max=255,
                         g_min=0, g_max=255, 
                         b_min=0, b_max=255):
    """
    Extrae patrones basado en intervalos RGB específicos
    - Negro (0): píxeles que coinciden con los rangos especificados (PATRÓN)
    - Blanco (255): píxeles que NO coinciden (FONDO)
    """
    
    # Leer imagen directamente en RGB
    img = cv2.imread(imagen_path)
    if img is None:
        print(f"Error: No se pudo cargar {imagen_path}")
        return None
    
    # Convertir BGR a RGB (OpenCV lee en BGR por defecto)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Separar canales
    r = img_rgb[:,:,0]
    g = img_rgb[:,:,1]
    b = img_rgb[:,:,2]
    
    # Crear máscara binaria
    # Inicialmente todo blanco (fondo)
    mascara = np.ones(r.shape, dtype=np.uint8) * 255
    
    # Aplicar condiciones - donde coincida con los rangos, poner NEGRO (patrón)
    condicion = (
        (r >= r_min) & (r <= r_max) &
        (g >= g_min) & (g <= g_max) &
        (b >= b_min) & (b <= b_max)
    )
    
    mascara[condicion] = 0  # Negro donde está el patrón
    
    # Guardar imagen resultante
    cv2.imwrite(salida_path, mascara)
    
    # Estadísticas simples
    total_pixeles = mascara.size
    pixeles_patron = np.sum(mascara == 0)
    porcentaje = (pixeles_patron / total_pixeles) * 100
    
    print(f"Procesado: {os.path.basename(imagen_path)}")
    print(f"  - Píxeles del patrón: {pixeles_patron}/{total_pixeles} ({porcentaje:.2f}%)")
    print(f"  - Rangos usados: R({r_min}-{r_max}), G({g_min}-{g_max}), B({b_min}-{b_max})")
    
    return mascara

# ---------------------------------------------------------------------
# CONFIGURACIÓN - ¡MODIFICA ESTOS VALORES!
# ---------------------------------------------------------------------

# Rangos RGB para extraer el patrón (MODIFICA AQUÍ)
CONFIGURACION = {
    'r_min': 0,    # Mínimo valor Rojo (0-255)
    'r_max': 255,  # Máximo valor Rojo (0-255)
    'g_min': 0,    # Mínimo valor Verde (0-255)
    'g_max': 255,  # Máximo valor Verde (0-255)  
    'b_min': 0,    # Mínimo valor Azul (0-255)
    'b_max': 255   # Máximo valor Azul (0-255)
}

def main():
    # Configuración de carpetas
    carpeta_entrada = 'img'
    carpeta_salida = 'patrones_bn'
    
    # Crear carpeta de salida
    Path(carpeta_salida).mkdir(exist_ok=True)
    
    # Lista de imágenes
    archivos = [
        'alpha-wireless-1.png', 'alpha-wireless-2.png', 'alpha-wireless-3.png',
        'molex-1.png', 'molex-2.png', 'molex-3.png',
        'quectel-1.png', 'quectel-2.png', 'quectel-3.png', 'quectel-4.png',
        'rf-elements-1.png', 'rf-elements-2.png',
        'taoglas-1.png', 'taoglas-2.png', 'taoglas-3.png', 'taoglas-4.png'
    ]
    
    print("=== EXTRACCIÓN DE PATRONES B/N ===")
    print(f"Rangos configurados: R({CONFIGURACION['r_min']}-{CONFIGURACION['r_max']}), "
          f"G({CONFIGURACION['g_min']}-{CONFIGURACION['g_max']}), "
          f"B({CONFIGURACION['b_min']}-{CONFIGURACION['b_max']})")
    print()
    
    for archivo in archivos:
        entrada = os.path.join(carpeta_entrada, archivo)
        salida = os.path.join(carpeta_salida, f"patron_{archivo}")
        
        if os.path.exists(entrada):
            extraer_patron_simple(entrada, salida, **CONFIGURACION)
        else:
            print(f"Archivo no encontrado: {entrada}")
    
    print(f"\n¡Proceso completado! Imágenes guardadas en: {carpeta_salida}")

# ---------------------------------------------------------------------
# FUNCIÓN PARA PROBAR CON UNA IMAGEN
# ---------------------------------------------------------------------

def probar_una_imagen():
    """
    Para probar rápidamente con una sola imagen
    """
    imagen_prueba = '../datasheets/taoglas-1.png'  
    # imagen_prueba = '../datasheets/rf-elements-1.png'  
    # imagen_prueba = '../datasheets/molex-1.png'  
    # imagen_prueba = '../datasheets/alpha-wireless-1.png'  
    # imagen_prueba = '../datasheets/quectel-1.png'  
    salida_prueba = 'taoglas-1.png'
    # salida_prueba = 'prueba_patron_rf_elements.png'
    # salida_prueba = 'prueba_patron_molex_1.png'
    # salida_prueba = 'prueba_patron_alpha-wireless_1.png'
    # salida_prueba = 'prueba_patron_quectel_1.png'
    
    # Configuración de prueba (taoglas)
    config_prueba = {
        'r_min': 25, 'r_max': 35,
        'g_min': 0, 'g_max': 255, 
        'b_min': 0, 'b_max': 255
    }
    # rf-elements:
    # config_prueba = {
    #     'r_min': 237, 'r_max': 237,
    #     'g_min': 0, 'g_max': 255, 
    #     'b_min': 0, 'b_max': 255
    #     }
    # molex-1.png 
    # config_prueba = {
    #     'r_min': 74, 'r_max': 74,
    #     'g_min': 0, 'g_max': 255, 
    #     'b_min': 187, 'b_max': 187
    #     }
    # #   molex-1.png 
    # config_prueba = {
    #     'r_min': 180, 'r_max': 210,
    #     'g_min': 180, 'g_max': 210, 
    #     'b_min': 180, 'b_max': 210
    #     }
    # Aplha wireless:
    # config_prueba = {
    #     'r_min': 3, 'r_max': 38,
    #     'g_min': 3, 'g_max': 38, 
    #     'b_min': 3, 'b_max': 38
    #     }
    # Quectel-1:
    # config_prueba = {
    #     'r_min': 0, 'r_max': 90,
    #     'g_min': 130, 'g_max': 150, 
    #     'b_min': 0, 'b_max': 255
    # }


    
    if os.path.exists(imagen_prueba):
        resultado = extraer_patron_simple(imagen_prueba, salida_prueba, **config_prueba)
        print(f"Imagen de prueba guardada como: {salida_prueba}")
    else:
        print(f"Imagen no encontrada: {imagen_prueba}")

if __name__ == "__main__":
    # Ejecutar procesamiento de todas las imágenes
    # main()
    
    # Para probar con una sola imagen, descomenta:
    probar_una_imagen()