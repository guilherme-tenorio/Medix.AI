from __future__ import annotations

import math
from dataclasses import dataclass

from django.conf import settings
from django.utils.module_loading import import_string


@dataclass(frozen=True, slots=True)
class EmergencyUnit:
    name: str
    address: str
    city: str
    neighborhood: str
    latitude: float
    longitude: float
    distance_km: float | None = None

    @property
    def external_route_url(self) -> str:
        return f'https://www.openstreetmap.org/directions?to={self.latitude},{self.longitude}'


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    raio_terra_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return round(2 * raio_terra_km * math.asin(math.sqrt(a)), 2)


class BaseHospitalDirectoryAdapter:
    def find_nearby(
        self,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        manual_query: str = '',
    ) -> list[EmergencyUnit]:
        raise NotImplementedError


class SandboxHospitalDirectoryAdapter(BaseHospitalDirectoryAdapter):
    """Diretório simulado de prontos-socorros para desenvolvimento e testes do MVP."""

    _UNITS = (
        EmergencyUnit(
            name='Pronto-Socorro Municipal Central',
            address='Av. da Saúde, 100 - Centro',
            city='São Paulo',
            neighborhood='Centro',
            latitude=-23.5505,
            longitude=-46.6333,
        ),
        EmergencyUnit(
            name='Hospital de Emergência Zona Sul',
            address='Rua das Clínicas, 450 - Vila Mariana',
            city='São Paulo',
            neighborhood='Vila Mariana',
            latitude=-23.5890,
            longitude=-46.6347,
        ),
        EmergencyUnit(
            name='UPA 24h Norte',
            address='Av. Voluntários, 1200 - Santana',
            city='São Paulo',
            neighborhood='Santana',
            latitude=-23.5015,
            longitude=-46.6250,
        ),
    )

    def find_nearby(
        self,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        manual_query: str = '',
    ) -> list[EmergencyUnit]:
        if latitude is not None and longitude is not None:
            calculadas = [
                EmergencyUnit(
                    name=u.name,
                    address=u.address,
                    city=u.city,
                    neighborhood=u.neighborhood,
                    latitude=u.latitude,
                    longitude=u.longitude,
                    distance_km=_haversine_km(latitude, longitude, u.latitude, u.longitude),
                )
                for u in self._UNITS
            ]
            return sorted(calculadas, key=lambda item: item.distance_km or 0.0)

        termo = (manual_query or '').strip().casefold()
        if not termo:
            return list(self._UNITS)

        filtradas = [
            u
            for u in self._UNITS
            if termo in u.city.casefold()
            or termo in u.neighborhood.casefold()
            or termo in u.address.casefold()
            or termo in u.name.casefold()
        ]
        return filtradas or list(self._UNITS)


def get_hospital_directory_adapter() -> BaseHospitalDirectoryAdapter:
    backend_path = getattr(
        settings,
        'MEDIX_HOSPITAL_DIRECTORY_BACKEND',
        'core.integrations.geolocation.SandboxHospitalDirectoryAdapter',
    )
    adapter_cls = import_string(backend_path)
    return adapter_cls()
