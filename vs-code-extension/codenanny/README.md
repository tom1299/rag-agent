# codenanny README
PoC / Hack for exploring possibilities to include an extension in VSCode that conntects via A2A protocol to
a remote agent.

Uses a2a protocol version 1.0

## Quick start

After checkout:

```bash
npm run setup
```

## TODO
Rebuild using ESM. Currently migration with help from CoPilot:
```
$ vs-code-extension$ ./node_modules/.bin/yo code

     _-----_     ╭──────────────────────────╮
    |       |    │   Welcome to the Visual  │
    |--(o)--|    │   Studio Code Extension  │
   `---------´   │        generator!        │
    ( _´U`_ )    ╰──────────────────────────╯
    /___A___\   /
     |  ~  |     
   __'.___.'__   
 ´   `  |° ´ Y ` 

`list` prompt is deprecated. Use `select` prompt instead.
✔ What type of extension do you want to create? New Extension (TypeScript)
✔ What's the name of your extension? CodeNanny
✔ What's the identifier of your extension? codenanny
✔ What's the description of your extension? Catching the quirks before the nitpickers arrive
✔ Initialize a git repository? No
`list` prompt is deprecated. Use `select` prompt instead.
✔ Which bundler to use? esbuild
```