#!/bin/sh
set -e

substitute() {
  placeholder="$1"
  value="$2"
  if [ -n "$value" ]; then
    find /usr/share/nginx/html/assets -type f -name '*.js' -exec sed -i "s|${placeholder}|${value}|g" {} +
  fi
}

substitute 'VITE_API_BASE_URL_PLACEHOLDER' "${VITE_API_BASE_URL}"
substitute 'VITE_ASSEMBLY_INDEXES_PATH_PLACEHOLDER' "${VITE_ASSEMBLY_INDEXES_PATH}"
substitute 'VITE_GFF_INDEXES_PATH_PLACEHOLDER' "${VITE_GFF_INDEXES_PATH}"
substitute 'VITE_BACINTERACTOME_SHINY_APP_URL_PLACEHOLDER' "${VITE_BACINTERACTOME_SHINY_APP_URL}"
substitute 'VITE_PFAM_URL_PLACEHOLDER' "${VITE_PFAM_URL}"
substitute 'VITE_INTERPRO_URL_PLACEHOLDER' "${VITE_INTERPRO_URL}"
substitute 'VITE_KEGG_URL_PLACEHOLDER' "${VITE_KEGG_URL}"
substitute 'VITE_COG_URL_PLACEHOLDER' "${VITE_COG_URL}"
substitute 'VITE_NETWORK_VIEW_ENABLED_PLACEHOLDER' "${VITE_NETWORK_VIEW_ENABLED:-false}"

exec nginx -g 'daemon off;'
