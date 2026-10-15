import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


class LLMProviderError(RuntimeError):
    pass


def _load_dotenv():
    path = Path(__file__).resolve().parent / ".env"
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip("\"'")
        if name and name not in os.environ:
            os.environ[name] = value


def provider_config():
    _load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
    if provider not in {"openrouter", "gemini"}:
        raise LLMProviderError("LLM_PROVIDER must be openrouter or gemini")
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/").rstrip("/")
        model = os.getenv("LLM_MODEL", "gemini-2.5-flash").strip()
    else:
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
        model = os.getenv("LLM_MODEL", "google/gemini-2.5-flash").strip()
    return {"provider": provider, "api_key": api_key, "base_url": base_url, "model": model}


def _schema_prompt():
    return """You extract procurement attributes from a user request for an industrial material catalogue.
Return only one valid JSON object. Do not invent MESC codes. Use null when an attribute is absent or uncertain.
Normalize Persian and English synonyms. Keep manufacturer names as provided unless an obvious translation exists.
Schema:
{
  \"item_type\": \"pipe|valve|fitting|flange|pump|gasket|cable|instrument|fastener|null\",
  \"item_subtype\": \"string|null\",
  \"size_inch\": \"number|null\",
  \"material\": \"string|null\",
  \"material_family\": \"plastic|carbon steel|stainless steel|metal|composite|null\",
  \"manufacturer\": \"string|null\",
  \"pressure_class\": \"number|null\",
  \"connection\": \"Threaded|Flanged|Butt Weld|Socket|null\",
  \"standard\": \"string|null\",
  \"service\": \"string|null\",
  \"missing_information\": [\"string\"]
}"""


def _json_content(response):
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("LLM response did not contain assistant content") from exc
    if not isinstance(content, str):
        raise LLMProviderError("LLM content was not text")
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMProviderError("LLM returned invalid JSON") from exc


def _normalize(data):
    allowed = {"item_type", "item_subtype", "size_inch", "material", "material_family", "manufacturer", "pressure_class", "connection", "standard", "service", "missing_information"}
    output = {key: data.get(key) for key in allowed}
    if output["item_type"] in {"tube", "لوله"}:
        output["item_type"] = "pipe"
    if output["material_family"] in {"plastic", "پلاستیک", "پلاستیکی"}:
        output["material_family"] = "plastic"
    if output["manufacturer"] in {"داچ", "داتچ"}:
        output["manufacturer"] = "Dutch"
    if output["size_inch"] is not None:
        output["size_inch"] = float(output["size_inch"])
    if output["pressure_class"] is not None:
        output["pressure_class"] = int(output["pressure_class"])
    output["missing_information"] = output["missing_information"] if isinstance(output["missing_information"], list) else []
    return output


def extract_query(query):
    config = provider_config()
    if not config["api_key"]:
        raise LLMProviderError(f"Missing API key for {config['provider']}")
    payload = {
        "model": config["model"],
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _schema_prompt()},
            {"role": "user", "content": query},
        ],
    }
    headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
    if config["provider"] == "openrouter":
        headers["HTTP-Referer"] = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost")
        headers["X-OpenRouter-Title"] = os.getenv("OPENROUTER_TITLE", "MESC Copilot")
    request = urllib.request.Request(f"{config['base_url']}/chat/completions", data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise LLMProviderError(f"LLM request failed: HTTP {exc.code} {exc.reason}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LLMProviderError(f"LLM request failed: {exc}") from exc
    return _normalize(_json_content(body))
