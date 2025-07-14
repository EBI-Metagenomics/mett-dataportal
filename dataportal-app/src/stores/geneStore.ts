import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface GeneState {
  genes: any[]
  selectedGene: any | null
  loading: boolean
  error: string | null
  
  setGenes: (genes: any[]) => void
  setSelectedGene: (gene: any | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useGeneStore = create<GeneState>()(
  devtools(
    (set) => ({
      genes: [],
      selectedGene: null,
      loading: false,
      error: null,
      
      setGenes: (genes) => set({ genes }),
      setSelectedGene: (gene) => set({ selectedGene: gene }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
    }),
    { name: 'gene-store' }
  )
)
