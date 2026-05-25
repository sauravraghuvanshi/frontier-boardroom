"""Azure Speech TTS with viseme events (§6.7).

Yields (audio_base64, viseme_frames). Uses azure-cognitiveservices-speech
with AAD-token auth via DefaultAzureCredential (subscription-key access is
blocked by tenant policy on the corp sub — see corp_sub_tenant_policy memo).
Falls back to silent placeholder with heuristic viseme timing only as a last
resort (rule 7 of §16 — heuristics disallowed for prod).
"""

from __future__ import annotations

import asyncio
import base64
import time
from typing import List, Tuple

from ..config import get_settings
from ..telemetry import get_logger
from .visemes import heuristic_visemes

log = get_logger("tts")

try:
    import azure.cognitiveservices.speech as speechsdk  # type: ignore

    _SDK_OK = True
except Exception:  # noqa: BLE001
    _SDK_OK = False

try:
    from azure.identity import DefaultAzureCredential  # type: ignore

    _cred = DefaultAzureCredential()
except Exception:  # noqa: BLE001
    _cred = None  # type: ignore[assignment]

_SCOPE = "https://cognitiveservices.azure.com/.default"
_token_cache: dict = {"token": None, "expires_on": 0}


def _get_auth_token(resource_id: str) -> str | None:
    if _cred is None:
        return None
    now = time.time()
    if _token_cache["token"] is None or _token_cache["expires_on"] - now < 300:
        t = _cred.get_token(_SCOPE)
        _token_cache.update(token=t.token, expires_on=t.expires_on)
    return f"aad#{resource_id}#{_token_cache['token']}"


async def synthesize_with_visemes(*, text: str, voice: str) -> Tuple[str, List[dict]]:
    settings = get_settings()
    if not _SDK_OK or not settings.azure_speech_resource_id or _cred is None:
        return "", heuristic_visemes(text)

    def _run() -> Tuple[str, List[dict]]:
        auth_token = _get_auth_token(settings.azure_speech_resource_id)
        if auth_token is None:
            return "", heuristic_visemes(text)
        cfg = speechsdk.SpeechConfig(  # type: ignore[attr-defined]
            auth_token=auth_token, region=settings.azure_speech_region
        )
        cfg.speech_synthesis_voice_name = voice
        cfg.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3  # type: ignore[attr-defined]
        )
        synth = speechsdk.SpeechSynthesizer(speech_config=cfg, audio_config=None)  # type: ignore[arg-type]
        frames: List[dict] = []

        def _viseme_cb(evt) -> None:  # noqa: ANN001
            frames.append(
                {"visemeId": int(evt.viseme_id), "offset_ms": int(evt.audio_offset / 10000)}
            )

        synth.viseme_received.connect(_viseme_cb)
        result = synth.speak_text_async(text).get()
        if (
            result.reason
            != speechsdk.ResultReason.SynthesizingAudioCompleted  # type: ignore[attr-defined]
        ):
            return "", frames or heuristic_visemes(text)
        audio_b64 = base64.b64encode(result.audio_data).decode("ascii")
        return audio_b64, frames

    try:
        return await asyncio.to_thread(_run)
    except Exception as e:  # noqa: BLE001
        log.warning("speech_failed", error=str(e))
        return "", heuristic_visemes(text)
