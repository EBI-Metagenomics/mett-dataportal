import {Dispatch, SetStateAction, useEffect, useState} from 'react';
import {useParams} from 'react-router-dom';
import {GenomeService} from '../services/genome';
import {GeneService} from '../services/gene';
import {GenomeMeta} from '../interfaces/Genome';
import {GeneMeta} from '../interfaces/Gene';
import {APP_CONSTANTS} from '../utils/common/constants';

interface UseGeneViewerDataReturn {
    geneMeta: GeneMeta | null;
    genomeMeta: GenomeMeta | null;

    loading: boolean;
    error: string | null;

    setLoading: Dispatch<SetStateAction<boolean>>;
    setError: (error: string | null) => void;
}

export const useGeneViewerData = (): UseGeneViewerDataReturn => {
    const {strainName} = useParams<{ strainName?: string }>();
    const searchParams = new URLSearchParams(location.search);
    const geneId = searchParams.get('locus_tag');

    // Local state
    const [geneMeta, setGeneMeta] = useState<GeneMeta | null>(null);
    const [genomeMeta, setGenomeMeta] = useState<GenomeMeta | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch gene and genome data
    useEffect(() => {
        const fetchGeneAndGenomeMeta = async () => {
            setLoading(true);
            setError(null);

            try {
                if (geneId) {
                    const geneResponse = await GeneService.fetchGeneByLocusTag(geneId);
                    setGeneMeta(geneResponse);

                    const genomeResponse = await GenomeService.fetchGenomeByIsolateNames([geneResponse.isolate_name]);
                    setGenomeMeta(genomeResponse[0]);
                } else if (strainName) {
                    const genomeResponse = await GenomeService.fetchGenomeByIsolateNames([strainName]);
                    setGenomeMeta(genomeResponse[0]);
                }
            } catch (err) {
                console.error('Error fetching gene/genome meta information', err);
                setError('Failed to load gene or genome data');
            } finally {
                setTimeout(() => setLoading(false), APP_CONSTANTS.SPINNER_DELAY);
            }
        };

        fetchGeneAndGenomeMeta();
    }, [geneId, strainName]);

    return {
        geneMeta,
        genomeMeta,
        loading,
        error,
        setLoading,
        setError,
    };
}; 