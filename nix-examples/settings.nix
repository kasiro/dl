# Параметры конфигурации
# Аналог settings.dl
{ lib }:

{
  schema = "https://opencode.ai/config.json";
  npm = {
    openaicomp = "@ai-sdk/openai-compatible";
    voidrot = "@voidrot/openai-featherless-compatible";
  };
}
