"""
title: Script Guion (Persistencia)
author: Idilio
description: Lee y escribe el guion.md de un show para la skill Idilio Script Intelligence -- el documento de trabajo persiste entre sesiones en disco.
required_open_webui_version: 0.5.0
version: 0.1.0
"""

import os
import re

from pydantic import BaseModel, Field


def _slug(show_slug: str) -> str:
    # Solo minúsculas, dígitos y guiones -- show_slug viene del modelo y
    # nunca debe usarse crudo en un path (podría intentar salirse del
    # directorio base con algo como "../../etc" sin este saneo).
    cleaned = re.sub(r'[^a-z0-9-]+', '-', show_slug.strip().lower()).strip('-')
    if not cleaned:
        raise ValueError('show_slug inválido')
    return cleaned


class Tools:
    class Valves(BaseModel):
        BASE_DIR: str = Field(
            default='/app/backend/data/guiones',
            description='Directorio base donde vive guiones/<show-slug>/guion.md.',
        )

    def __init__(self):
        self.valves = self.Valves()

    def _path(self, show_slug: str) -> str:
        return os.path.join(self.valves.BASE_DIR, _slug(show_slug), 'guion.md')

    def read_guion(self, show_slug: str) -> str:
        """
        Lee el guion.md completo de un show. Úsala al retomar un show existente, o antes de anexar un capítulo nuevo para revisar si ese número de capítulo ya existe.
        :param show_slug: El identificador del show en minúsculas-con-guiones (ej. "el-diagnostico-equivocado").
        :return: El contenido completo del archivo, o un mensaje indicando que no existe todavía.
        """
        path = self._path(show_slug)
        if not os.path.exists(path):
            return f"No existe todavía un guion.md para '{show_slug}' -- créalo con write_guion."
        with open(path, encoding='utf-8') as f:
            return f.read()

    def write_guion(self, show_slug: str, content: str) -> str:
        """
        Sobreescribe el guion.md completo de un show con el contenido dado. Úsala para crear el show por primera vez (Etapa 0) o para guardar el documento completo actualizado después de cualquier cambio -- nuevo personaje, capítulo nuevo anexado, etc. Siempre pasa el archivo COMPLETO, no un fragmento: esto reemplaza el archivo entero.
        :param show_slug: El identificador del show en minúsculas-con-guiones.
        :param content: El contenido completo y actualizado del guion.md.
        :return: Confirmación de que se guardó, con la ruta del archivo.
        """
        path = self._path(show_slug)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existed = os.path.exists(path)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Guardado ({'actualizado' if existed else 'creado'}): {path}"

    def chapter_exists(self, show_slug: str, chapter_number: int) -> str:
        """
        Revisa si un número de capítulo ya existe en el guion.md -- úsala antes de anexar un capítulo nuevo (Etapa 6) para no duplicar uno que ya se escribió.
        :param show_slug: El identificador del show en minúsculas-con-guiones.
        :param chapter_number: El número de capítulo a buscar.
        :return: Si existe o no, y en qué línea del archivo.
        """
        content = self.read_guion(show_slug)
        pattern = re.compile(
            rf'^CAP[IÍ]TULO\s+{chapter_number}\b', re.IGNORECASE | re.MULTILINE
        )
        match = pattern.search(content)
        if match:
            line_number = content[: match.start()].count('\n') + 1
            return f'Sí, CAPÍTULO {chapter_number} ya existe (línea {line_number}).'
        return f'No, CAPÍTULO {chapter_number} no existe todavía.'
