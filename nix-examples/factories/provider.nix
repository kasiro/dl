# Фабрика провайдеров
# Принимает: name, npm, port, models
# Возвращает: атрибуты провайдера
name: npm: port: models:

{
  inherit npm name;
  options = {
    baseURL = "http://localhost:${builtins.toString port}/v1";
  };
  inherit models;
}
