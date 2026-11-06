# Фабрика options для провайдеров
# Принимает: port
# Возвращает: атрибуты с baseURL
{ port }:

{
  baseURL = "http://localhost:${builtins.toString port}/v1";
}
