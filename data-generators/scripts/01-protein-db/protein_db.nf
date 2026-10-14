nextflow.enable.dsl = 2

/*
 * One deduplicated protein FASTA for PyHMMER.
 *
 *   nextflow run protein_db.nf -profile all
 *   nextflow run protein_db.nf -profile hd
 *   nextflow run protein_db.nf -profile 20hm
 *   nextflow run protein_db.nf --manifest sources.tsv
 */

process PLAN {
    tag 'plan'

    output:
    path 'sources.tsv'

    script:
    def manifest = params.manifest ? "--manifest '${params.manifest}'" : ""
    def skip = params.skip_missing ? "--skip-missing" : ""
    """
    python3 ${projectDir}/run.py plan \\
        --batch '${params.batch}' \\
        --species-csv '${params.species_csv}' \\
        --hd-root '${params.hd_root}' \\
        --hm-root '${params.hm_root}' \\
        --hd-map '${params.hd_map}' \\
        --hm-map '${params.hm_map}' \\
        --faa-template '${params.faa_template}' \\
        ${manifest} \\
        ${skip} \\
        --jobs sources.tsv
    """
}

process STAGE {
    tag "${isolate}"

    input:
    tuple val(isolate), val(species), val(type_strain), val(collection), path(faa)

    output:
    path "${isolate}.jsonl"

    script:
    def flag = type_strain == "true" ? "--type-strain" : ""
    """
    python3 ${projectDir}/run.py stage \\
        --faa ${faa} \\
        --isolate '${isolate}' \\
        --species '${species}' \\
        --collection '${collection}' \\
        ${flag} \\
        --out '${isolate}.jsonl'
    """
}

process MERGE {
    tag 'merge'
    publishDir "${params.out}", mode: 'copy', overwrite: true

    input:
    path chunks

    output:
    tuple path('mett_proteins.faa'), path('members.tsv'), path('catalog.json')

    script:
    """
    mkdir -p chunks
    cp ${chunks} chunks/
    python3 ${projectDir}/run.py merge \\
        --chunks chunks \\
        --species-csv '${params.species_csv}' \\
        --out .
    """
}

process INDEX {
    tag 'index'
    publishDir "${params.out}", mode: 'copy', overwrite: true

    input:
    tuple path(faa), path(members), path(catalog)

    output:
    path 'members.sqlite'
    path 'mett_proteins.faa.ssi', optional: true

    script:
    """
    python3 ${projectDir}/run.py index \\
        --faa ${faa} \\
        --members ${members} \\
        --out .
    """
}

workflow {
    sources = PLAN()
        .splitCsv(header: true, sep: '\t')
        .map { row ->
            tuple(
                row.isolate,
                row.species,
                row.type_strain,
                row.collection,
                file(row.faa, checkIfExists: true),
            )
        }

    INDEX(MERGE(STAGE(sources).collect()))
}
