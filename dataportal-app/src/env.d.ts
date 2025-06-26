/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_ASSEMBLY_INDEXES_PATH?: string
  readonly VITE_GFF_INDEXES_PATH?: string
  readonly VITE_BACINTERACTOME_SHINY_APP_URL?: string

}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
