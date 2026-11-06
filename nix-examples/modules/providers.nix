# Модуль провайдеров
{ lib
, settings
, factories
, ...
}:

{
  providers = {
    localproxy = factories.provider "localproxy" settings.npm.openaicomp 9625 {
      "free-gemini-2.5-pro" = { name = "free-gemini-2.5-pro"; };
      "free-minimax-m2.7" = { name = "free-minimax-m2.7"; };
      "free-claude-haiku-4-5-20251001" = { name = "free-claude-haiku-4-5-20251001"; };
      "free-gemini-2.5-flash" = { name = "free-gemini-2.5-flash"; };
      "free-qwen3.5-plus" = { name = "free-qwen3.5-plus"; };
      "free-qwen3.5-flash" = { name = "free-qwen3.5-flash"; };
      "free-minimax-m2.5" = { name = "free-minimax-m2.5"; };
      "free-gemini-2.5-flash-lite" = { name = "free-gemini-2.5-flash-lite"; };
      "free-gemini-3-flash-preview" = { name = "free-gemini-3-flash-preview"; };
    };

    deepseek-proxy = {
      npm = settings.npm.voidrot;
      name = "deepseek-proxy";
      options = factories.makeoptions { port = 9626; } // {
        toolCallFallback = "auto";
        useCompletionUrls = true;
      };
      models = {
        "deepseek/deepseek-v4.1-flash" = { name = "deepseek/deepseek-v4.1-flash"; };
      };
    };

    zen-free = factories.provider "zen-free" settings.npm.openaicomp 9627 {
      "deepseek-v4-flash-free" = { name = "deepseek-v4-flash-free"; };
      "big-pickle" = { name = "big-pickle"; };
      "mimo-v2.6-flash-free" = { name = "mimo-v2.6-flash-free"; };
    };
  };
}
