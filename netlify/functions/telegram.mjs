// Función de Netlify: el gemelo habla con Telegram a través de acá, así el token del bot
// queda guardado una sola vez en Netlify (variable secreta) y sirve en cualquier dispositivo.
// El token nunca llega al navegador.
//
// Variables de entorno en Netlify (Site configuration → Environment variables):
//   TELEGRAM_TOKEN    el código que da @BotFather
//   TELEGRAM_CHAT_ID  el chat que recibe los avisos (el del celular del técnico o un grupo)
//
// GET  → { configurado, chat }   (el chat no es secreto: el gemelo lo usa para filtrar respuestas)
// POST { metodo, params } → la respuesta de Telegram. Solo deja usar los métodos del gemelo
//      y siempre manda al chat configurado, para que nadie la use para escribirle a otro.

const PERMITIDOS = new Set(["getMe", "getUpdates", "sendMessage", "answerCallbackQuery", "getChat"]);
const JSON_HDR = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const responder = (cuerpo, status = 200) => new Response(JSON.stringify(cuerpo), { status, headers: JSON_HDR });

export default async function handler(req) {
  const token = (process.env.TELEGRAM_TOKEN || "").trim();
  const chat = (process.env.TELEGRAM_CHAT_ID || "").trim();
  if (req.method === "GET") return responder({ configurado: Boolean(token && chat), chat: chat || null });
  if (req.method !== "POST") return responder({ ok: false, description: "Método no permitido" }, 405);
  if (!token || !chat) return responder({ ok: false, description: "Falta configurar TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en Netlify" }, 503);

  let pedido;
  try { pedido = await req.json(); } catch { return responder({ ok: false, description: "Pedido inválido" }, 400); }
  const metodo = String(pedido?.metodo || "");
  if (!PERMITIDOS.has(metodo)) return responder({ ok: false, description: "Método de Telegram no permitido" }, 400);

  const params = {};
  for (const [k, v] of Object.entries(pedido?.params || {})) params[k] = typeof v === "string" ? v : JSON.stringify(v);
  if (metodo === "sendMessage" || metodo === "getChat") params.chat_id = chat;      // siempre al chat configurado
  if (metodo === "sendMessage" && (params.text || "").length > 4000) params.text = params.text.slice(0, 4000);

  try {
    const r = await fetch(`https://api.telegram.org/bot${token}/${metodo}`, { method: "POST", body: new URLSearchParams(params) });
    return responder(await r.json(), 200);
  } catch {
    return responder({ ok: false, description: "Netlify no pudo conectar con Telegram" }, 502);
  }
}
