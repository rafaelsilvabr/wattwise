"""Local-only WattWise MVP. Run: python app.py"""

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
from urllib import error, request

from demo import number, reduction
from energy_skill import answer_history, experiment_for, load_skill, reply_schema, validate_reply

ROOT = Path(__file__).parent
SAMPLE = json.loads((ROOT / "examples" / "family-household.json").read_text(encoding="utf-8"))


def analyze(config):
    if not isinstance(config, dict):
        raise ValueError("Envie os dados da sua casa.")
    voltage = number(config.get("voltage"), "Tensão", positive=True)
    rate = number(config.get("rate"), "Preço por kWh")
    days = number(config.get("days"), "Dias", positive=True)
    if rate > 1000:
        raise ValueError("Informe um preço por kWh de até R$ 1.000.")
    if days > 366:
        raise ValueError("Escolha um período de até 366 dias.")
    devices = config.get("devices")
    if not isinstance(devices, list) or not 1 <= len(devices) <= 50:
        raise ValueError("Cadastre entre 1 e 50 aparelhos ou modos de uso.")
    rows, ids = [], set()
    for device in devices:
        if not isinstance(device, dict):
            raise ValueError("Aparelho inválido.")
        identity, name = device.get("id"), device.get("name")
        if not isinstance(identity, str) or not re.fullmatch(r"[\w-]{1,80}", identity) or identity in ids:
            raise ValueError("Cada aparelho precisa de um identificador único.")
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise ValueError("Informe um nome de até 100 caracteres.")
        ids.add(identity)
        watts, hours = number(device.get("watts"), "Potência"), number(device.get("hours"), "Horas por dia")
        planned_watts = number(device.get("plannedWatts"), "Potência proposta")
        planned_hours = number(device.get("plannedHours"), "Horas propostas")
        if max(watts, planned_watts) > 100000:
            raise ValueError("Informe uma potência de até 100.000 W por aparelho.")
        if max(hours, planned_hours) > 24:
            raise ValueError("As horas de uso devem estar entre 0 e 24 por dia.")
        protected = device.get("protected", False)
        if not isinstance(protected, bool):
            raise ValueError("O campo de uso essencial deve ser verdadeiro ou falso.")
        if protected and (watts != planned_watts or hours != planned_hours):
            raise ValueError(f"O uso de {name} está protegido. Mantenha os valores atuais na proposta.")
        before, after = watts * hours * days / 1000, planned_watts * planned_hours * days / 1000
        rows.append({"id": identity, "name": name.strip(), "watts": watts, "hours": hours,
                     "plannedWatts": planned_watts, "plannedHours": planned_hours, "protected": protected,
                     **reduction(before, after, rate), "baseline_cost_brl": round(before * rate, 2)})
    before, after = sum(r["baseline_kwh"] for r in rows), sum(r["proposed_kwh"] for r in rows)
    opportunities = []
    for row in sorted(rows, key=lambda r: r["energy_reduction_kwh"], reverse=True):
        if row["energy_reduction_kwh"] > 0 and not row["protected"]:
            opportunities.append({**row, "household_after_kwh": round(before - row["energy_reduction_kwh"], 6),
                                  "household_after_cost_brl": round((before - row["energy_reduction_kwh"]) * rate, 2)})
    context = config.get("context", "")
    if not isinstance(context, str) or len(context) > 2000:
        raise ValueError("Descreva sua rotina em até 2.000 caracteres.")
    return {"evidence": "manual_estimate", "voltage": voltage, "rate": rate, "days": days,
            "devices": rows, "opportunities": opportunities,
            "total": {**reduction(before, after, rate), "baseline_cost_brl": round(before * rate, 2)}}


def ollama_model():
    model = os.environ.get("OLLAMA_MODEL", "gemma4:e2b")
    if not re.fullmatch(r"gemma4(?::[a-zA-Z0-9_.-]+)?", model) or "cloud" in model:
        raise ValueError("Use um modelo Gemma 4 local em OLLAMA_MODEL, como gemma4:e2b.")
    return model


def ollama_status():
    model = ollama_model()
    try:
        with request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
            models = json.load(response).get("models", [])
        names = [m.get("name", "") for m in models]
        return {"available": model in names or (model == "gemma4" and "gemma4:latest" in names),
                "running": True, "model": model}
    except (OSError, ValueError):
        return {"available": False, "running": False, "model": model}


def advise(config):
    report = analyze(config)
    candidates = report["opportunities"][:8]
    answers = answer_history(config)
    skill = load_skill()
    model = ollama_model()
    clarification_only = not candidates or (not config.get("context", "").strip() and not answers)
    schema = reply_schema(candidates, clarification_only)
    system = skill["body"]
    payload = {"model": model, "stream": False, "think": False, "format": schema,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": json.dumps({
                                "task": "ask_one_question" if clarification_only else "choose_or_clarify",
                                "routine": config.get("context", ""), "answers": answers,
                                "evidence": "manual_estimate",
                                "highest_consumers": [{k: d[k] for k in ("name", "watts", "hours", "protected")}
                                    for d in sorted(report["devices"], key=lambda d: d["baseline_kwh"], reverse=True)[:4]],
                                "candidates": [{k: c[k] for k in (
                                    "id", "name", "watts", "hours", "plannedWatts", "plannedHours", "energy_reduction_kwh")}
                                    for c in candidates]}, ensure_ascii=False)}],
               "options": {"num_ctx": 4096, "num_predict": 400, "temperature": 0}}
    req = request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=90) as response:
            response_data = json.load(response)
    except error.HTTPError as exc:
        raise ValueError(f"Ollama retornou HTTP {exc.code}. Confira se o modelo local está instalado.") from None
    except (error.URLError, TimeoutError):
        raise ValueError("Gemma não respondeu. Inicie o Ollama e carregue o modelo; a simulação continua disponível.") from None
    content = response_data.get("message", {}).get("content", "")
    if response_data.get("done_reason") == "length":
        raise ValueError("Gemma atingiu o limite de resposta. Tente novamente com uma rotina mais curta.")
    try:
        answer = json.loads(content)
    except (ValueError, TypeError):
        raise ValueError("O modelo não retornou um plano válido. Tente novamente.") from None
    candidate = validate_reply(answer, candidates)
    # Missing routine must be clarified even if a model tries to recommend anyway.
    if not config.get("context", "").strip() and not answers and candidate is not None:
        raise ValueError("Conte um pouco sobre sua rotina antes de receber uma recomendação.")
    return {"provider": "ollama", "model": model, "evidence": "manual_estimate",
            "decision": answer["decision"], "experiment": experiment_for(candidate),
            "phase": "clarify" if clarification_only else "choose",
            "skill": {"name": skill["name"], "sha256": skill["sha256"]},
            "considered_candidate_ids": [c["id"] for c in candidates], "answers_considered": len(answers),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "candidate": candidate, "reason": answer["reason"],
            "next_step": answer["next_step"], "question": answer["question"]}


class Handler(BaseHTTPRequestHandler):
    server_version = "WattWise/0.1"

    def send(self, status, body, content_type="application/json; charset=utf-8"):
        data = json.dumps(body, ensure_ascii=False).encode() if content_type.startswith("application/json") else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def valid_host(self):
        return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, {"error": "Use o endereço local do aplicativo."})
        if self.path == "/api/sample":
            return self.send(200, SAMPLE)
        if self.path == "/api/status":
            return self.send(200, ollama_status())
        files = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                 "/styles.css": ("styles.css", "text/css; charset=utf-8")}
        if self.path not in files:
            return self.send(404, {"error": "Página não encontrada."})
        name, content_type = files[self.path]
        return self.send(200, (ROOT / "web" / name).read_bytes(), content_type)

    def do_POST(self):
        if not self.valid_host():
            return self.send(403, {"error": "Origem inválida."})
        origin = self.headers.get("Origin")
        if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}:
            return self.send(403, {"error": "Origem inválida."})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.send(415, {"error": "Envie application/json."})
        if self.path not in {"/api/analyze", "/api/advise"}:
            return self.send(404, {"error": "Operação não encontrada."})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 65536:
                return self.send(413, {"error": "Envie até 64 KB de dados."})
            data = json.loads(self.rfile.read(size))
            report = analyze(data)
        except (ValueError, TypeError, KeyError, AttributeError):
            return self.send(400, {"error": "Dados inválidos. Confira nomes, potências, horários e uso essencial."})
        if self.path == "/api/analyze":
            return self.send(200, report)
        try:
            return self.send(200, advise(data))
        except ValueError as exc:
            return self.send(502, {"error": str(exc)})
        except (TypeError, KeyError, AttributeError):
            return self.send(502, {"error": "Ollama retornou uma resposta inesperada. Tente novamente."})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"WattWise: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
