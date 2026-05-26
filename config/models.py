from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096


class DatabaseConfig(BaseModel):
    backend: str = "postgresql"
    pool_size: int = 5


class MemoryConfig(BaseModel):
    backend: str = "faiss"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384


class CacheConfig(BaseModel):
    backend: str = "memory"
    default_ttl: int = 300


class SecurityConfig(BaseModel):
    rate_limit_per_minute: int = 60
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


class DefaultConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


class GraphConfig(DefaultConfig):
    tools: list[str] = Field(default_factory=list)
    validation: dict = Field(default_factory=dict)
    checkpointing: bool = False
