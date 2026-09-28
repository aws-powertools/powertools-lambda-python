#!/usr/bin/env bash

set -euo pipefail

POLICY_FILE=${1:?Policy file is required}

if jq -e '
  (.Policy | if type == "string" then fromjson else . end)
  | any(.Statement[]?;
      .Effect == "Allow"
      and ((.Action // [] | if type == "array" then . else [.] end) | any(. == "*" or . == "lambda:*" or . == "lambda:GetLayerVersion"))
      and (((.Principal | if type == "object" then .AWS // "" else . end) | if type == "array" then . else [.] end) | index("*") != null)
      and ((.Condition // {}) | length == 0)
    )
' "$POLICY_FILE" > /dev/null; then
  echo public
else
  RESULT=$?
  if (( RESULT > 1 )); then
    echo "Unable to evaluate layer policy ${POLICY_FILE} (jq exit ${RESULT})" >&2
    exit "$RESULT"
  fi
  echo private
fi
