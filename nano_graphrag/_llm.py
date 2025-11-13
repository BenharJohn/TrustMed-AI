import numpy as np
import os
import google.generativeai as genai

from ._utils import compute_args_hash, wrap_embedding_func_with_attrs
from .base import BaseKVStorage

# Configure Gemini API - will use environment variable
def _ensure_configured():
    """Ensure Gemini is configured with API key from environment"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)


async def openai_complete_if_cache(
    model, prompt, system_prompt=None, history_messages=[], **kwargs
) -> str:
    """
    Renamed but uses Gemini for compatibility with existing code.
    Maps model names: gpt-4o -> gemini-1.5-pro, gpt-4o-mini -> gemini-1.5-flash
    """
    hashing_kv: BaseKVStorage = kwargs.pop("hashing_kv", None)

    # Map OpenAI model names to Gemini models
    model_mapping = {
        "gpt-4o": "models/gemini-pro-latest",
        "gpt-4o-mini": "models/gemini-flash-latest",
        "gpt-4-1106-preview": "models/gemini-pro-latest"
    }
    gemini_model_name = model_mapping.get(model, "models/gemini-pro-latest")

    # Build combined prompt for Gemini
    full_prompt = ""
    if system_prompt:
        full_prompt += f"{system_prompt}\n\n"
    for msg in history_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        full_prompt += f"{role.capitalize()}: {content}\n"
    full_prompt += f"User: {prompt}"

    # Check cache
    if hashing_kv is not None:
        messages_for_hash = []
        if system_prompt:
            messages_for_hash.append({"role": "system", "content": system_prompt})
        messages_for_hash.extend(history_messages)
        messages_for_hash.append({"role": "user", "content": prompt})
        args_hash = compute_args_hash(model, messages_for_hash)
        if_cache_return = await hashing_kv.get_by_id(args_hash)
        if if_cache_return is not None:
            return if_cache_return["return"]

    # Ensure Gemini is configured
    _ensure_configured()

    # Call Gemini API (synchronously, wrapped in async)
    gemini_model = genai.GenerativeModel(gemini_model_name)

    # Extract generation config from kwargs
    generation_config = {}
    if 'temperature' in kwargs:
        generation_config['temperature'] = kwargs['temperature']
    if 'max_tokens' in kwargs:
        generation_config['max_output_tokens'] = kwargs['max_tokens']

    response = gemini_model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(**generation_config) if generation_config else None
    )

    response_text = response.text

    # Cache result
    if hashing_kv is not None:
        await hashing_kv.upsert(
            {args_hash: {"return": response_text, "model": model}}
        )
    return response_text


async def gpt_4o_complete(
    prompt, system_prompt=None, history_messages=[], **kwargs
) -> str:
    """Uses gemini-1.5-pro"""
    return await openai_complete_if_cache(
        "gpt-4o",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        **kwargs,
    )


async def gpt_4o_mini_complete(
    prompt, system_prompt=None, history_messages=[], **kwargs
) -> str:
    """Uses gemini-1.5-flash"""
    return await openai_complete_if_cache(
        "gpt-4o-mini",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        **kwargs,
    )


@wrap_embedding_func_with_attrs(embedding_dim=768, max_token_size=2048)
async def openai_embedding(texts: list[str]) -> np.ndarray:
    """
    Renamed but uses Gemini embeddings for compatibility.
    Note: Gemini embedding-001 has dimension 768, not 1536
    """
    _ensure_configured()
    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        embeddings.append(result['embedding'])
    return np.array(embeddings)
