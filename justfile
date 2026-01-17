set dotenv-load := true
set fallback := true
set positional-arguments := true

# cli

@cli *args:
  conformalize-cli {{args}}
