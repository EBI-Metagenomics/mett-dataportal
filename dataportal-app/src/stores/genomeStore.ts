import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface GenomeState {
  genomes: any[]
  typeStrains: any[]
  speciesList: any[]
  loading: boolean
  error: string | null
  
  setGenomes: (genomes: any[]) => void
  setTypeStrains: (strains: any[]) => void
  setSpeciesList: (species: any[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useGenomeStore = create<GenomeState>()(
  devtools(
    (set) => ({
      genomes: [],
      typeStrains: [],
      speciesList: [],
      loading: false,
      error: null,
      
      setGenomes: (genomes) => set({ genomes }),
      setTypeStrains: (strains) => set({ typeStrains: strains }),
      setSpeciesList: (species) => set({ speciesList: species }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
    }),
    { name: 'genome-store' }
  )
)
