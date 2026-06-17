'''
Optional AI assistant for WriteHat.

Talks to any OpenAI-compatible Chat Completions endpoint (e.g. a self-hosted
Open WebUI instance, Ollama, vLLM, LM Studio, or the OpenAI API). Uses only the
Python standard library, so it adds no dependencies.

Configuration lives in settings.AI_* (see settings.py / config/writehat.conf).
The feature is disabled unless AI_ENABLED is true and a base URL + model are set.
'''

import ssl
import json
import hashlib
import logging
import urllib.error
import urllib.request

from django.conf import settings

from writehat.lib.errors import WriteHatError

log = logging.getLogger(__name__)


class AIError(WriteHatError):
    '''Raised when an AI generation request fails.'''
    pass


class AIDisabledError(AIError):
    '''Raised when the assistant is invoked while disabled or misconfigured.'''
    pass


# Mirrors Report.defaultLanguageChoices in writehat.lib.report
LANGUAGE_NAMES = {
    'en': 'English',
    'it': 'Italian',
    'fr': 'French',
    'de': 'German',
    'es': 'Spanish',
}


def language_name(code):
    '''Human-readable language name for a report language code.'''
    return LANGUAGE_NAMES.get((code or 'en').lower(), 'English')


def is_enabled():
    '''True only if the assistant is switched on and minimally configured.'''
    return bool(
        getattr(settings, 'AI_ENABLED', False)
        and getattr(settings, 'AI_BASE_URL', '')
        and getattr(settings, 'AI_MODEL', '')
    )


def _endpoint():
    '''Resolve the full chat-completions URL from the configured base URL.'''
    base = (getattr(settings, 'AI_BASE_URL', '') or '').rstrip('/')
    if not base:
        raise AIDisabledError('AI_BASE_URL is not configured.')
    if base.endswith('/chat/completions'):
        return base
    return base + '/chat/completions'


def _ssl_context():
    if getattr(settings, 'AI_VERIFY_SSL', True):
        return None
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def chat(messages, temperature=None, max_tokens=None, timeout=None):
    '''
    Low-level call to the OpenAI-compatible /chat/completions endpoint.

    messages: list of {"role": ..., "content": ...} dicts.
    Returns the assistant's reply text. Raises AIError on any failure.
    '''
    if not is_enabled():
        raise AIDisabledError('The AI assistant is disabled or not fully configured.')

    payload = {
        'model': settings.AI_MODEL,
        'messages': messages,
        'temperature': settings.AI_TEMPERATURE if temperature is None else temperature,
        'max_tokens': settings.AI_MAX_TOKENS if max_tokens is None else max_tokens,
        'stream': False,
    }
    data = json.dumps(payload).encode('utf-8')

    headers = {'Content-Type': 'application/json'}
    if getattr(settings, 'AI_API_KEY', ''):
        headers['Authorization'] = f'Bearer {settings.AI_API_KEY}'

    request = urllib.request.Request(_endpoint(), data=data, headers=headers, method='POST')
    timeout = settings.AI_TIMEOUT if timeout is None else timeout

    log.debug(f'ai.chat() -> {_endpoint()} (model={settings.AI_MODEL})')

    try:
        with urllib.request.urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            body = response.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        detail = ''
        try:
            detail = e.read().decode('utf-8', errors='replace')[:500]
        except Exception:
            pass
        log.error(f'AI endpoint returned HTTP {e.code}: {detail}')
        raise AIError(f'AI endpoint returned HTTP {e.code}. {detail}'.strip())
    except urllib.error.URLError as e:
        log.error(f'AI endpoint unreachable: {e.reason}')
        raise AIError(f'Could not reach the AI endpoint: {e.reason}')
    except (TimeoutError, OSError) as e:
        log.error(f'AI request failed: {e}')
        raise AIError(f'AI request failed: {e}')

    return _extract_text(body)


def _extract_text(body):
    '''Pull the assistant text out of an OpenAI-compatible JSON response.'''
    try:
        parsed = json.loads(body)
    except (ValueError, TypeError):
        raise AIError('AI endpoint returned a non-JSON response.')

    try:
        choice = parsed['choices'][0]
    except (KeyError, IndexError, TypeError):
        raise AIError('AI endpoint returned an unexpected response shape.')

    message = choice.get('message') or {}
    content = message.get('content')
    if content is None:
        # Some servers (completion-style) use "text" instead of message.content
        content = choice.get('text', '')

    # Some servers return content as a list of parts
    if isinstance(content, list):
        content = ''.join(
            part.get('text', '') if isinstance(part, dict) else str(part)
            for part in content
        )

    return (content or '').strip()


def build_messages(field_label, system_prompt, context_items, language='en', existing_text=''):
    '''
    Assemble chat messages for drafting a single report field.

      field_label   : human label of the field being written (e.g. "Description")
      system_prompt : the effective per-field / per-component instruction (may be blank)
      context_items : iterable of (label, value) fact pairs to write from
      language      : target language code for the output
      existing_text : current field content, if any
    '''
    system = (getattr(settings, 'AI_DEFAULT_SYSTEM_PROMPT', '') or '').strip()
    if system_prompt and system_prompt.strip():
        system = (system + '\n\n' + system_prompt.strip()).strip()
    system += f'\n\nWrite the output in {language_name(language)}.'

    lines = []
    for label, value in context_items:
        value = ('' if value is None else str(value)).strip()
        if value:
            lines.append(f'## {label}\n{value}')
    context_block = '\n\n'.join(lines) if lines else '(no additional context provided)'

    user = (
        f'Write the "{field_label}" section of this penetration-test finding, '
        f'using only the information below.\n\n'
        f'# Context\n{context_block}'
    )
    if existing_text and existing_text.strip():
        user += f'\n\n# Current draft (improve or replace this)\n{existing_text.strip()}'

    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def generate_field(field_label, system_prompt, context_items, language='en', existing_text=''):
    '''High-level helper: assemble messages and return the generated text.'''
    messages = build_messages(
        field_label,
        system_prompt,
        context_items,
        language=language,
        existing_text=existing_text,
    )
    return chat(messages)


# ---------------------------------------------------------------------------
# Export-time translation
# ---------------------------------------------------------------------------

# Small process-local cache so repeated exports of unchanged content within a
# worker don't re-pay translation cost. Keyed by hash(source|target|html).
_TRANSLATION_CACHE = {}
_TRANSLATION_CACHE_MAX = 512


def _translate_system_prompt(source_name, target_name):
    return (
        'You are a professional translator localizing a penetration-test report. '
        f'Translate the visible human-readable text of the given HTML fragment from '
        f'{source_name} into {target_name}. Preserve ALL HTML tags, attributes, '
        'structure and whitespace exactly as they are. Do NOT translate or modify: '
        'text inside <code> or <pre> elements, URLs, email addresses, file system '
        'paths, hostnames, code identifiers, CVE IDs, CVSS or DREAD vector strings, '
        'or any curly-brace placeholder markers. Output only the translated HTML '
        'fragment, with no explanation and no code fences.'
    )


def _strip_code_fences(text):
    '''Remove an accidental ```...``` wrapper some models add around output.'''
    t = (text or '').strip()
    if t.startswith('```'):
        newline = t.find('\n')
        if newline != -1:
            t = t[newline + 1:]
        if t.rstrip().endswith('```'):
            t = t.rstrip()[:-3]
    return t.strip()


def _cache_translation(key, value):
    if len(_TRANSLATION_CACHE) >= _TRANSLATION_CACHE_MAX:
        try:
            _TRANSLATION_CACHE.pop(next(iter(_TRANSLATION_CACHE)))
        except StopIteration:
            pass
    _TRANSLATION_CACHE[key] = value


def translate_html(html, target_language, source_language='en'):
    '''
    Translate the visible text of an HTML fragment, preserving markup.

    Fail-open: if the assistant is disabled or the call fails, the original HTML
    is returned so report export is never broken. Same-language or text-free
    fragments are returned unchanged.
    '''
    if not html or not html.strip():
        return html

    target = (target_language or '').lower()
    source = (source_language or 'en').lower()
    if not target or target == source:
        return html
    if not is_enabled():
        return html
    # nothing translatable (e.g. pure markup / numbers)
    if not any(c.isalpha() for c in html):
        return html

    key = hashlib.sha256(f'{source}|{target}|{html}'.encode('utf-8')).hexdigest()
    cached = _TRANSLATION_CACHE.get(key)
    if cached is not None:
        return cached

    messages = [
        {'role': 'system', 'content': _translate_system_prompt(language_name(source), language_name(target))},
        {'role': 'user', 'content': html},
    ]
    try:
        translated = chat(
            messages,
            temperature=0.1,
            max_tokens=max(int(getattr(settings, 'AI_MAX_TOKENS', 1200)), 4096),
        )
    except AIError as e:
        log.warning(f'translate_html failed ({source}->{target}); returning source text: {e}')
        return html

    if not translated or not translated.strip():
        return html

    translated = _strip_code_fences(translated)
    _cache_translation(key, translated)
    return translated
