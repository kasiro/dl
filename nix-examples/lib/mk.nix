{ lib }:

{
  # Значение по умолчанию (низкий приоритет)
  mkDefault = lib.mkDefault;

  # Принудительное значение (высокий приоритет)
  mkForce = lib.mkForce;

  # Значение по умолчанию с явным приоритетом
  mkOptionDefault = lib.mkOptionDefault;
}
