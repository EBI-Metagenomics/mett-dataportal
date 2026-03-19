/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend API base URL (e.g. http://localhost:8000/api). PPI/STRING requests use this. */
  readonly VITE_API_BASE_URL?: string
  readonly VITE_ASSEMBLY_INDEXES_PATH?: string
  readonly VITE_GFF_INDEXES_PATH?: string
  readonly VITE_BACINTERACTOME_SHINY_APP_URL?: string
  /** STRING DB web UI base for links (default: https://string-db.org). API calls go via backend. */
  readonly VITE_STRING_DB_WEB_BASE?: string
  /** Enable Network View tab in Gene Viewer (default: false). Set via Kubernetes. */
  readonly VITE_NETWORK_VIEW_ENABLED?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
