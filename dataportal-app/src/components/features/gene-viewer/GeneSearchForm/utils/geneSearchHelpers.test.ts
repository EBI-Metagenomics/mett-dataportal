import {geneQueryGenomes, genomesForQuery, looksLikeLocusTag} from './geneSearchHelpers'

describe('geneSearchHelpers', () => {
  test('looksLikeLocusTag distinguishes locus tags from free text', () => {
    expect(looksLikeLocusTag('PV_CCUG68662_01886')).toBe(true)
    expect(looksLikeLocusTag('BU_ATCC8492_00001')).toBe(true)
    expect(looksLikeLocusTag('dnaA')).toBe(false)
    expect(looksLikeLocusTag('dnaA (PV_CCUG68662_01886)')).toBe(false)
  })

  test('genomesForQuery merges selected genomes and extra isolates', () => {
    const result = genomesForQuery(
      [{ isolate_name: 'BU_ATCC8492', type_strain: true }],
      ['PV_ATCC8482', 'BU_ATCC8492']
    )
    expect(result).toEqual([
      { isolate_name: 'BU_ATCC8492', type_strain: true },
      { isolate_name: 'PV_ATCC8482', type_strain: true },
    ])
  })

  test('geneQueryGenomes appends type-strain isolates', () => {
    expect(geneQueryGenomes([], ['BU_ATCC8492', 'PV_ATCC8482'])).toEqual([
      { isolate_name: 'BU_ATCC8492', type_strain: true },
      { isolate_name: 'PV_ATCC8482', type_strain: true },
    ])
  })
})
