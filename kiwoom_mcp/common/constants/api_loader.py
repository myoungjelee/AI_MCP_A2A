"""
키움증권 API Registry 로더

YAML 파일에서 API 정의를 로드하고 관리합니다.
"""

from pathlib import Path
from typing import Optional

import yaml


class APIRegistryLoader:
    """키움 API 레지스트리 로더"""

    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            # 현재 파일 기준으로 상대 경로 설정
            current_dir = Path(__file__).parent
            # constants 폴더에서 한 단계 위로 올라가서 api_registry 폴더 접근
            registry_path = current_dir.parent / "api_registry" / "kiwoom_api_registry.yaml"

        self.registry_path = Path(registry_path)
        self._registry: dict[str, any] = {}
        self._api_map: dict[str, dict[str, any]] = {}
        self._load_registry()

    @property
    def registry(self) -> dict[str, any]:
        """전체 레지스트리 반환"""
        return self._registry

    @property
    def api_map(self) -> dict[str, dict[str, any]]:
        """API ID별 매핑 반환"""
        return self._api_map

    def _load_registry(self):
        """YAML 파일에서 레지스트리 로드"""
        if not self.registry_path.exists():
            raise FileNotFoundError(
                f"API 레지스트리 파일을 찾을 수 없습니다: {self.registry_path}"
            )

        with open(self.registry_path, "r", encoding="utf-8") as f:
            self._registry = yaml.safe_load(f)

        self._build_api_map()

    def _build_api_map(self):
        """API ID별 매핑 구축"""
        self._api_map = {}
        # api_registry 키 아래의 모든 API ID를 직접 매핑
        api_registry = self._registry.get("api_registry", {})
        for api_id, api_info in api_registry.items():
            self._api_map[api_id] = api_info

    def get_api(self, api_id: str) -> Optional[dict[str, any]]:
        """API ID로 API 정보 조회"""
        return self._api_map.get(api_id)

    def get_apis_by_category(self, category: str) -> list[dict[str, any]]:
        """카테고리별 API 목록 조회"""
        apis = []
        api_registry = self._registry.get("api_registry", {})
        for api_id, api_info in api_registry.items():
            if api_info.get("category") == category:
                # api_id 정보도 포함
                api_with_id = api_info.copy()
                api_with_id["api_id"] = api_id
                apis.append(api_with_id)
        return apis

    def get_required_params(self, api_id: str) -> list[str]:
        """API의 필수 파라미터 목록 반환"""
        api = self.get_api(api_id)
        if not api:
            return []

        params = api.get("parameters", {})
        required = []

        for param_name, param_info in params.items():
            if isinstance(param_info, dict):
                if param_info.get("required", False):
                    required.append(param_name)
            elif isinstance(param_info, str):
                # 간단한 문자열 형태의 파라미터는 필수로 간주
                required.append(param_name)

        return required

    def get_optional_params(self, api_id: str) -> list[str]:
        """API의 선택적 파라미터 목록 반환"""
        api = self.get_api(api_id)
        if not api:
            return []

        params = api.get("parameters", {})
        optional = []

        for param_name, param_info in params.items():
            if isinstance(param_info, dict):
                if not param_info.get("required", False):
                    optional.append(param_name)
            # 문자열 형태는 필수로 간주하므로 제외

        return optional

    def validate_params(
        self, api_id: str, params: dict[str, any]
    ) -> tuple[bool, list[str]]:
        """파라미터 유효성 검증"""
        required_params = self.get_required_params(api_id)
        missing_params = []

        for required_param in required_params:
            if required_param not in params:
                missing_params.append(required_param)

        is_valid = len(missing_params) == 0
        return is_valid, missing_params

    def get_categories(self) -> list[str]:
        """사용 가능한 API 카테고리 목록 반환"""
        return list(self._registry.get("apis", {}).keys())

    def get_statistics(self) -> dict[str, any]:
        """레지스트리 통계 정보 반환"""
        total_apis = 0
        category_counts = {}

        for category, apis in self._registry.get("apis", {}).items():
            count = len(apis)
            category_counts[category] = count
            total_apis += count

        return {
            "total_apis": total_apis,
            "category_counts": category_counts,
            "categories": list(category_counts.keys()),
            "registry_version": self._registry.get("version", "unknown"),
            "last_updated": self._registry.get("last_updated", "unknown"),
        }

    def verify_completeness(self) -> tuple[bool, list[str]]:
        """레지스트리 완성도 검증"""
        issues = []

        # 필수 필드 검증
        required_fields = ["version", "apis"]
        for field in required_fields:
            if field not in self._registry:
                issues.append(f"필수 필드 누락: {field}")

        # API 정보 검증
        if "apis" in self._registry:
            for category, apis in self._registry["apis"].items():
                if not isinstance(apis, list):
                    issues.append(f"카테고리 {category}: API 목록이 리스트가 아님")
                    continue

                for i, api in enumerate(apis):
                    if not isinstance(api, dict):
                        issues.append(
                            f"카테고리 {category} API {i}: API 정보가 딕셔너리가 아님"
                        )
                        continue

                    # 필수 API 필드 검증
                    api_required_fields = ["api_id", "name", "description"]
                    for api_field in api_required_fields:
                        if api_field not in api:
                            issues.append(
                                f"카테고리 {category} API {api.get('api_id', i)}: 필수 필드 누락: {api_field}"
                            )

        is_complete = len(issues) == 0
        return is_complete, issues


# 싱글톤 인스턴스
_loader_instance: Optional[APIRegistryLoader] = None


def get_loader() -> APIRegistryLoader:
    """기본 로더 인스턴스 반환"""
    return APIRegistryLoader()


def get_api(api_id: str) -> Optional[dict[str, any]]:
    """API ID로 API 정보 조회 (편의 함수)"""
    loader = get_loader()
    return loader.get_api(api_id)


def get_required_params(api_id: str) -> list[str]:
    """API의 필수 파라미터 목록 반환 (편의 함수)"""
    loader = get_loader()
    return loader.get_required_params(api_id)


def validate_params(api_id: str, params: dict[str, any]) -> tuple[bool, list[str]]:
    """파라미터 유효성 검증 (편의 함수)"""
    loader = get_loader()
    return loader.validate_params(api_id, params)
