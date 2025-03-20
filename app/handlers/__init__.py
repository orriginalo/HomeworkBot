import importlib
import pkgutil
from aiogram import Router

# Автоматически находим все файлы в пакете `handlers`, кроме `__init__.py`
package_name = __name__
routers = []

for _, module_name, _ in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f"{package_name}.{module_name}")

    # Проверяем, есть ли в модуле `router`
    if hasattr(module, "router") and isinstance(module.router, Router):
        routers.append(module.router)
