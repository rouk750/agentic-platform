# Backend Providers Technical Specification

## Overview
This directory (`backend/app/providers`) implements the **Strategy Pattern** for LLM integrations. It abstracts the differences between vendors (OpenAI, Ollama, Anthropic) into a unified interface.

## 1. Base Strategy (`base.py`)

### `BaseLLMProvider` (Abstract Base Class)
 Defines the contract that all providers must follow.

#### `create_client(profile: LLMProfile, api_key: str) -> BaseChatModel`
*   **Abstract Method**: Must be implemented by subclasses.
*   **Returns**: A `langchain-core` runnable (typically `ChatOpenAI`, `ChatAnthropic`, etc).
*   **Logic**: Maps the generic `profile` fields (base_url, temperature) to the specific client constructor.

#### `test_connection(profile: LLMProfile, api_key: str)` (Async)
*   **Default**: Attempts `client.ainvoke("Hi")`.
*   **Override**: Subclasses can optimize this (e.g. hitting a `/tags` endpoint instead of running inference).

## 2. Factory (`factory.py`)

### `LLMProviderFactory`
Static registry and creator.

#### `register(provider_type: ProviderType, provider: BaseLLMProvider)`
*   Registers an instance of a provider against an Enum key.

#### `get_provider(provider_type: ProviderType) -> BaseLLMProvider`
*   Retrieves the singleton strategy instance.

#### `create(profile: LLMProfile, api_key: str)`
*   Convenience wrapper: `get_provider(p.provider).create_client(...)`

## 3. Implementations

### `OpenAIProvider` (`openai.py`)
*   Wraps `langchain_openai.ChatOpenAI`.
*   Directly passes `base_url` (supports proxies).

### `OllamaProvider` (`ollama.py`)
*   Wraps `langchain_ollama.ChatOllama`.
*   Specifics: If `profile.model_id` contains "ollama/", strips prefix.

### `LMStudioProvider` (`openai.py`)
*   Subclass of OpenAI but defaults `base_url` to `http://localhost:1234/v1` and sets dummy api key.
