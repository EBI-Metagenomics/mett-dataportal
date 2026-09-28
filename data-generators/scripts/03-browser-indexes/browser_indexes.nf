nextflow.enable.dsl = 2

/*
 * One Nextflow task per assembly and per GFF.
 *
 * Python plans the file list (mapping TSV + the two input roots). Each
 * index_* task only sees the file it compresses, so 20hm and HD differ
 * only by --fasta-dir, --gff-base, and --map-tsv.
 *
 *   nextflow run browser_indexes.nf -profile 20hm
 *   nextflow run browser_indexes.nf -profile hd --isolates BU_ATCC8492
 */

process PLAN {
    tag 'plan'

    input:
    path map_tsv

    output:
    path 'jobs.tsv'

    script:
    def skip = params.skip_missing ? '--skip-missing' : ''
    def isolates = params.isolates ? "--isolates '${params.isolates}'" : ''
    """
    python3 ${projectDir}/run.py plan \\
        --map-tsv ${map_tsv} \\
        --fasta-dir '${params.fasta_dir}' \\
        --gff-base '${params.gff_base}' \\
        --gff-dir-template '${params.gff_dir_template}' \\
        --release '${params.release}' \\
        --only ${params.only} \\
        ${isolates} \\
        ${skip} \\
        --jobs jobs.tsv
    """
}

process INDEX_FASTA {
    tag "${isolate}"
    publishDir "${params.out}/${release}/${species}/fasta/${assembly_folder}", mode: 'copy', overwrite: true

    input:
    tuple val(isolate), val(species), val(assembly_folder), val(release), path(fasta)

    output:
    path "${fasta.name}.gz"
    path "${fasta.name}.gz.fai"
    path "${fasta.name}.gz.gzi"

    script:
    """
    python3 ${projectDir}/index_fasta.py --fasta ${fasta} --out .
    """
}

process INDEX_GFF {
    tag "${isolate}"
    publishDir "${params.out}/${release}/${species}/gff3/${isolate}", mode: 'copy', overwrite: true

    input:
    tuple val(isolate), val(species), val(release), path(gff)

    output:
    path "${gff.name}.gz"
    path "${gff.name}.gz.tbi"
    path "trix/${gff.name}.gz.ix"
    path "trix/${gff.name}.gz.ixx"
    path "trix/${gff.name}.gz_meta.json"

    script:
    def base = params.index_base_url ? "--index-base-url '${params.index_base_url}'" : ''
    """
    python3 ${projectDir}/index_gff.py \\
        --gff ${gff} \\
        --out . \\
        --file-id '${gff.baseName}' \\
        ${base}
    """
}

workflow {
    if (!params.map_tsv) {
        error "Pass --map-tsv, or select -profile hd / -profile 20hm"
    }
    if (!params.fasta_dir) {
        error "Pass --fasta-dir, or select -profile hd / -profile 20hm"
    }
    if (!params.gff_base) {
        error "Pass --gff-base, or select -profile hd / -profile 20hm"
    }

    jobs = PLAN(file(params.map_tsv, checkIfExists: true))
        .splitCsv(header: true, sep: '\t')
        .branch { row ->
            fasta: row.kind == 'fasta'
            gff: row.kind == 'gff'
        }

    INDEX_FASTA(
        jobs.fasta.map { row ->
            tuple(
                row.isolate,
                row.species,
                row.assembly_folder,
                row.release,
                file(row.src, checkIfExists: true),
            )
        }
    )
    INDEX_GFF(
        jobs.gff.map { row ->
            tuple(row.isolate, row.species, row.release, file(row.src, checkIfExists: true))
        }
    )
}
