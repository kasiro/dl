; Highlights for DL language

; Keywords
[
  "json"
  "toml"
  "yaml"
  "schema"
  "let"
  "import"
  "class"
  "enum"
  "map"
] @keyword

; Literals
(NUMBER) @number
(FLOAT) @float
(STRING) @string
[
  "true"
  "false"
] @boolean
"null" @constant.builtin

; Types
(type_atom) @type
(named_type) @type

; Functions
(call (IDENT) @function)
(call_stmt (call (IDENT) @function))

; Variables
(ref_path (IDENT) @variable)
(field_path (IDENT) @variable)
(param (IDENT) @variable)

; Parameters
(param (IDENT) @variable.parameter)

; Comments
(DOC_COMMENT) @comment.documentation
(COMMENT) @comment

; Punctuation
"{" @punctuation.bracket
"}" @punctuation.bracket
"[" @punctuation.bracket
"]" @punctuation.bracket
"(" @punctuation.bracket
")" @punctuation.bracket
":" @punctuation.delimiter
";" @punctuation.delimiter
"," @punctuation.delimiter
"." @punctuation.delimiter

; Operators
"=>" @operator
"=" @operator
"?" @operator
"..." @operator
"|" @operator
