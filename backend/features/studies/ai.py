"""Propuesta de ocupación asistida por IA (OpenAI gpt-4o-mini vía emergentintegrations).

Mapea cada estancia al uso previsto y densidad de la Tabla 2.1 del CTE DB-SI,
eligiendo siempre de la lista de usos permitidos que recibe.
"""
import json
import os
import uuid

from emergentintegrations.llm.chat import LlmChat, UserMessage

SYSTEM = (
    "Eres un técnico especialista en protección contra incendios y en el CTE DB-SI (España). "
    "Para cada estancia asignas el uso previsto y su densidad de ocupación según la Tabla 2.1 del DB-SI. "
    "Debes elegir SIEMPRE un 'uso' EXACTAMENTE de la lista de usos permitidos indicada, con su densidad. "
    "Responde ÚNICAMENTE con JSON válido, sin explicaciones ni texto fuera del JSON."
)


def _clean_json(txt: str) -> str:
    t = txt.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    return t[i:j + 1] if i != -1 and j != -1 else t


async def propose_ocupacion(estancias: list, usos: list) -> list:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Falta la clave OPENAI_API_KEY en el backend.")

    catalogo = "\n".join(
        f"- {u.get('uso')}: {u.get('densidad') if u.get('densidad') is not None else 'sin ocupación (densidad nula)'}"
        for u in usos
    )
    lista = "\n".join(
        f"{i + 1}. id={e.get('id')} · «{e.get('nombre', '') or 's/n'}»"
        + (f" · {e.get('superficie')} m²" if e.get("superficie") else "")
        for i, e in enumerate(estancias)
    )
    prompt = (
        f"Usos permitidos (uso: densidad en m²/persona):\n{catalogo}\n\n"
        f"Estancias a clasificar:\n{lista}\n\n"
        "Devuelve un JSON con esta forma EXACTA:\n"
        '{"propuestas":[{"id":"<id de la estancia>","uso":"<uso EXACTO de la lista>",'
        '"densidad":<número o null>,"motivo":"<justificación breve>"}]}\n'
        "Usa densidad null solo cuando el uso permitido indique sin ocupación. "
        "Incluye TODAS las estancias, respetando sus id."
    )

    chat = LlmChat(
        api_key=key,
        session_id=f"ocup-{uuid.uuid4().hex[:10]}",
        system_message=SYSTEM,
    ).with_model("openai", "gpt-4o-mini")

    resp = await chat.send_message(UserMessage(text=prompt))
    data = json.loads(_clean_json(resp))

    usos_map = {u.get("uso"): u.get("densidad") for u in usos}
    out = []
    for p in data.get("propuestas", []):
        uso = p.get("uso")
        dens = usos_map.get(uso, p.get("densidad"))
        out.append({
            "id": p.get("id"),
            "uso": uso,
            "densidad": dens,
            "motivo": (p.get("motivo") or "").strip(),
        })
    return out
