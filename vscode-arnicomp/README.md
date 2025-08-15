# ArniComp Language Support (VS Code)

This extension adds basic syntax highlighting for the ArniComp high-level language.

Features
- Comments: `//`
- Preprocessor: `#def NAME VALUE`
- Keywords: `if/elif/else/endif`, `while/endwhile`, `break/continue`
- Types: `byte`, arrays like `byte[5]`
- Numbers: decimal and hex (`0x..`)

How to run (Extension Development Host)
1. Open this folder (`vscode-arnicomp`) in VS Code.
2. Press F5 to launch a new Extension Development Host.
3. In the new window, create a file `example.arn` and type some code.

Associate .txt temporarily (optional)
If your sources are `.txt`, you can associate them:

Settings (JSON):
"files.associations": {
	"*.txt": "arnicomp"
}

Files
- `package.json`: Extension manifest (declares language + grammar)
- `language-configuration.json`: Brackets, comments, pairs
- `syntaxes/arnicomp.tmLanguage.json`: TextMate grammar patterns
