"""
MCP 서버 및 클라이언트 설정 관리 모듈
현업 3-4년차 수준의 설정 관리 시스템을 제공합니다.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LoggingConfig:
    """로깅 설정"""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = False

    @classmethod
    def from_env(cls, prefix: str = "") -> "LoggingConfig":
        """환경변수에서 로깅 설정을 로드합니다."""
        env_prefix = f"{prefix}_" if prefix else ""

        return cls(
            level=os.getenv(f"{env_prefix}LOG_LEVEL", "INFO"),
            format=os.getenv(f"{env_prefix}LOG_FORMAT", cls.format),
            file_path=os.getenv(f"{env_prefix}LOG_FILE_PATH"),
            max_file_size=int(
                os.getenv(f"{env_prefix}LOG_MAX_FILE_SIZE", cls.max_file_size)
            ),
            backup_count=int(
                os.getenv(f"{env_prefix}LOG_BACKUP_COUNT", cls.backup_count)
            ),
            enable_console=os.getenv(f"{env_prefix}LOG_ENABLE_CONSOLE", "true").lower()
            == "true",
            enable_file=os.getenv(f"{env_prefix}LOG_ENABLE_FILE", "false").lower()
            == "true",
        )


@dataclass
class CacheConfig:
    """캐시 설정"""

    ttl: int = 300  # 5분
    max_size: int = 1000
    enable_memory: bool = True
    enable_disk: bool = False
    disk_path: Optional[str] = None
    compression: bool = True

    @classmethod
    def from_env(cls, prefix: str = "") -> "CacheConfig":
        """환경변수에서 캐시 설정을 로드합니다."""
        env_prefix = f"{prefix}_" if prefix else ""

        return cls(
            ttl=int(os.getenv(f"{env_prefix}CACHE_TTL", cls.ttl)),
            max_size=int(os.getenv(f"{env_prefix}CACHE_MAX_SIZE", cls.max_size)),
            enable_memory=os.getenv(f"{env_prefix}CACHE_ENABLE_MEMORY", "true").lower()
            == "true",
            enable_disk=os.getenv(f"{env_prefix}CACHE_ENABLE_DISK", "false").lower()
            == "true",
            disk_path=os.getenv(f"{env_prefix}CACHE_DISK_PATH"),
            compression=os.getenv(f"{env_prefix}CACHE_COMPRESSION", "true").lower()
            == "true",
        )


@dataclass
class RetryConfig:
    """재시도 설정"""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True

    @classmethod
    def from_env(cls, prefix: str = "") -> "RetryConfig":
        """환경변수에서 재시도 설정을 로드합니다."""
        env_prefix = f"{env_prefix}_" if prefix else ""

        return cls(
            max_attempts=int(
                os.getenv(f"{env_prefix}RETRY_MAX_ATTEMPTS", cls.max_attempts)
            ),
            base_delay=float(
                os.getenv(f"{env_prefix}RETRY_BASE_DELAY", cls.base_delay)
            ),
            max_delay=float(os.getenv(f"{env_prefix}RETRY_MAX_DELAY", cls.max_delay)),
            exponential_backoff=os.getenv(
                f"{env_prefix}RETRY_EXPONENTIAL_BACKOFF", "true"
            ).lower()
            == "true",
            jitter=os.getenv(f"{env_prefix}RETRY_JITTER", "true").lower() == "true",
        )


@dataclass
class MonitoringConfig:
    """모니터링 설정"""

    enable_metrics: bool = True
    enable_health_check: bool = True
    metrics_interval: int = 60  # 1분
    health_check_interval: int = 30  # 30초
    enable_alerting: bool = False
    alert_threshold: float = 0.1  # 10% 에러율

    @classmethod
    def from_env(cls, prefix: str = "") -> "MonitoringConfig":
        """환경변수에서 모니터링 설정을 로드합니다."""
        env_prefix = f"{env_prefix}_" if prefix else ""

        return cls(
            enable_metrics=os.getenv(
                f"{env_prefix}MONITORING_ENABLE_METRICS", "true"
            ).lower()
            == "true",
            enable_health_check=os.getenv(
                f"{env_prefix}MONITORING_ENABLE_HEALTH_CHECK", "true"
            ).lower()
            == "true",
            metrics_interval=int(
                os.getenv(
                    f"{env_prefix}MONITORING_METRICS_INTERVAL", cls.metrics_interval
                )
            ),
            health_check_interval=int(
                os.getenv(
                    f"{env_prefix}MONITORING_HEALTH_CHECK_INTERVAL",
                    cls.health_check_interval,
                )
            ),
            enable_alerting=os.getenv(
                f"{env_prefix}MONITORING_ENABLE_ALERTING", "false"
            ).lower()
            == "true",
            alert_threshold=float(
                os.getenv(
                    f"{env_prefix}MONITORING_ALERT_THRESHOLD", cls.alert_threshold
                )
            ),
        )


@dataclass
class MCPServerConfig:
    """MCP 서버 설정"""

    name: str
    port: int = 8000
    host: str = "0.0.0.0"
    debug: bool = False
    max_connections: int = 100
    request_timeout: int = 30
    enable_metrics: bool = True
    enable_health_check: bool = True

    # 하위 설정들
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    @classmethod
    def from_env(cls, name: str, prefix: str = "") -> "MCPServerConfig":
        """환경변수에서 MCP 서버 설정을 로드합니다."""
        env_prefix = f"{prefix}_" if prefix else ""

        return cls(
            name=name,
            port=int(os.getenv(f"{env_prefix}PORT", 8000)),
            host=os.getenv(f"{env_prefix}HOST", "0.0.0.0"),
            debug=os.getenv(f"{env_prefix}DEBUG", "false").lower() == "true",
            max_connections=int(os.getenv(f"{env_prefix}MAX_CONNECTIONS", 100)),
            request_timeout=int(os.getenv(f"{env_prefix}REQUEST_TIMEOUT", 30)),
            enable_metrics=os.getenv(f"{env_prefix}ENABLE_METRICS", "true").lower()
            == "true",
            enable_health_check=os.getenv(
                f"{env_prefix}ENABLE_HEALTH_CHECK", "true"
            ).lower()
            == "true",
            logging=LoggingConfig.from_env(env_prefix),
            cache=CacheConfig.from_env(env_prefix),
            retry=RetryConfig.from_env(env_prefix),
            monitoring=MonitoringConfig.from_env(env_prefix),
        )


@dataclass
class MCPClientConfig:
    """MCP 클라이언트 설정"""

    name: str
    base_url: str = ""
    timeout: int = 30
    max_retries: int = 3
    cache_ttl: int = 300
    enable_metrics: bool = True

    # 하위 설정들
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    @classmethod
    def from_env(cls, name: str, prefix: str = "") -> "MCPClientConfig":
        """환경변수에서 MCP 클라이언트 설정을 로드합니다."""
        env_prefix = f"{prefix}_" if prefix else ""

        return cls(
            name=name,
            base_url=os.getenv(f"{env_prefix}BASE_URL", ""),
            timeout=int(os.getenv(f"{env_prefix}TIMEOUT", 30)),
            max_retries=int(os.getenv(f"{env_prefix}MAX_RETRIES", 3)),
            cache_ttl=int(os.getenv(f"{env_prefix}CACHE_TTL", 300)),
            enable_metrics=os.getenv(f"{env_prefix}ENABLE_METRICS", "true").lower()
            == "true",
            logging=LoggingConfig.from_env(env_prefix),
            cache=CacheConfig.from_env(env_prefix),
            retry=RetryConfig.from_env(env_prefix),
            monitoring=MonitoringConfig.from_env(env_prefix),
        )


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    설정 파일에서 설정을 로드합니다.

    Args:
        config_path: 설정 파일 경로

    Returns:
        설정 딕셔너리
    """
    import json

    import yaml

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.endswith(".json"):
                return json.load(f)
            elif config_path.endswith((".yml", ".yaml")):
                return yaml.safe_load(f)
            else:
                raise ValueError(f"지원하지 않는 설정 파일 형식: {config_path}")
    except FileNotFoundError:
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    except Exception as e:
        raise ValueError(f"설정 파일 로드 실패: {e}")


def merge_configs(
    base_config: Dict[str, Any], override_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    두 설정을 병합합니다. override_config가 우선순위를 가집니다.

    Args:
        base_config: 기본 설정
        override_config: 오버라이드 설정

    Returns:
        병합된 설정
    """

    def deep_merge(base: Any, override: Any) -> Any:
        if isinstance(base, dict) and isinstance(override, dict):
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        else:
            return override

    return deep_merge(base_config, override_config)
