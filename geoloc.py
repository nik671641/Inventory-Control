import math

# Данные для строительных проектов
projects = {
    "Straseni": {"latitude": 47.037518, "longitude": 28.774526, "radius": 300},
    "Albisoara": {"latitude": 47.036177, "longitude": 28.841908, "radius": 300}
}


def haversine(lat1, lon1, lat2, lon2):
    """Функция для расчета расстояния между двумя точками по их координатам."""
    R = 6371000  # Радиус Земли в метрах
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


