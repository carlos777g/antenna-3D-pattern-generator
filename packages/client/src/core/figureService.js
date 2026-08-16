/**
 * figureService
 * Responsabilidad única: obtener datos de figuras desde cualquier fuente.
 *
 * Hoy lee un JSON local (simulación).
 * Mañana llamará al backend real — solo cambia este archivo.
 *
 * El resto de la app (hook, componentes) no sabe de dónde vienen los datos.
 */

// En Vite los assets en /public se sirven desde la raíz
const JSON_URL = "./figures.json";

/**
 * Carga todas las figuras disponibles.
 * @returns {Promise<Array>}
 */
export async function fetchFigures() {
  const res = await fetch(JSON_URL);
  if (!res.ok) throw new Error(`No se pudo cargar figures.json: ${res.status}`);
  return res.json();
}

/**
 * Carga una figura por nombre.
 * @param {string} name
 * @returns {Promise<object>}
 */
export async function fetchFigureByName(name) {
  const figures = await fetchFigures();
  const fig = figures.find(f => f.name === name);
  if (!fig) throw new Error(`Figura "${name}" no encontrada`);
  return fig;
}

// ----------------------------------------------------------------
// PRÓXIMO PASO — reemplazar fetch local por llamada al backend:
//
// export async function fetchFigureFromBackend(payload) {
//   const res = await fetch("/api/analyze", {
//     method: "POST",
//     body: JSON.stringify(payload),
//   });
//   return res.json(); // devuelve { vertices, faces }
// }
// ----------------------------------------------------------------