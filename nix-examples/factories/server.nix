# Фабрика MCP серверов
# Принимает: name, type, url?, command?, headers?, timeout?
# Возвращает: атрибуты сервера
name: type: url: command: headers: timeout:

{
  inherit name type timeout;
}
// (if url != null then { inherit url; } else { })
// (if command != null && command != [ ] then { inherit command; } else { })
// (if headers != { } then { inherit headers; } else { })
