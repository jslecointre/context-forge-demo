import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from langchain.chat_models import init_chat_model

security = HTTPBasic()


def get_current_dir() -> Path:
    """Get the current directory of the module.
    Returns:
        Path object representing the current directory
    """
    try:
        return Path(__file__).resolve().parent
    except NameError:  # __file__ is not defined
        return Path.cwd()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Validate backend credentials credentials."""
    if credentials.username != os.getenv(
        "BACKEND_USER"
    ) or credentials.password != os.getenv("BACKEND_PASSWORD"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def create_model(
    model_name: str,
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
    **kwargs,
):
    """Create a model instance based on the model name with appropriate configuration.

    Args:
        model_name: The model identifier
        temperature: Temperature for model generation (default: 0.0)
        max_tokens: Maximum tokens to generate (optional)
        **kwargs: Additional parameters to pass to init_chat_model

    Returns:
        Initialized chat model instance

    Raises:
        ValueError: If the model type is not supported
    """
    if model_name.startswith("ollama:"):
        # Ollama models - special handling with num_predict
        model_kwargs = {
            "temperature": temperature,
            "seed": 122,
            "num_predict": max_tokens or 1000,
        }
        model_kwargs.update(kwargs)

    elif model_name.startswith("ibm:"):
        from ibm_watsonx_ai.foundation_models.schema import TextChatParameters

        params = TextChatParameters(
            max_tokens=max_tokens or 500, temperature=temperature, seed=122
        )

        wx_credentials = {
            "url": os.getenv("WATSONX_URL"),
            "apikey": os.getenv("WATSONX_APIKEY"),
            "project_id": os.getenv("WATSONX_PROJECT_ID"),
        }

        return init_chat_model(
            model=model_name, params=params, **wx_credentials, **kwargs
        )
    elif model_name.startswith(("openai:")):
        model_kwargs = {"temperature": temperature}
        if max_tokens:
            model_kwargs["max_tokens"] = max_tokens
        model_kwargs.update(kwargs)

        return init_chat_model(model=model_name, **model_kwargs)

    else:
        raise ValueError(
            f"Unknown model type: {model_name}. Supported types: 'ibm:', 'ollama:'"
        )


def messages_to_markdown(messages):
    """
    Convert a list of Human/AI messages (dict or LC objects) to markdown
    with '### User' and '### Assistant' headings.
    """
    md_blocks = []
    for msg in messages:
        # Detect role & content whether it's a dict or LC BaseMessage
        if hasattr(msg, "content"):
            content = msg.content
            role = getattr(msg, "role", None) or msg.__class__.__name__.lower()
        else:
            content = msg.get("content", "")
            role = msg.get("role", "")

        if "human" in role or role == "user":
            title = "### User"
        elif "ai" in role or role == "assistant":
            title = "### Assistant"
        else:
            title = f"### {role.title() or 'Message'}"

        md_blocks.append(f"{title}\n\n{content}")

    return "\n\n---\n\n".join(md_blocks)


def to_bool(val):
    """
    Convert "boolean" strings (for example, from environment variables) to real
    booleans.

    Values mapping to `True`:

    - ``True``
    - ``"true"`` / ``"t"``
    - ``"yes"`` / ``"y"``
    - ``"on"``
    - ``"1"``
    - ``1``

    Values mapping to `False`:

    - ``False``
    - ``"false"`` / ``"f"``
    - ``"no"`` / ``"n"``
    - ``"off"``
    - ``"0"``
    - ``0``

    Raises:
        ValueError: For any other value.

    .. versionadded:: 21.3.0
    """
    if isinstance(val, str):
        val = val.lower()

    if val in (True, "true", "t", "yes", "y", "on", "1", 1):
        return True
    if val in (False, "false", "f", "no", "n", "off", "0", 0):
        return False

    msg = f"Cannot convert value to bool: {val!r}"
    raise ValueError(msg)
