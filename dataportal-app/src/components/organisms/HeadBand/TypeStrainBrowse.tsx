import React, {useMemo, useState} from 'react';
import {GenomeMeta} from '../../../interfaces/Genome';
import {compareTypeStrainIsolates} from '../../../utils/common/homePageConstants';
import styles from './HomePageHeadBand.module.scss';

const COLLAPSE_GROUP_LIMIT = 12;

interface SpeciesInfo {
    acronym: string;
    scientific_name: string;
}

interface TypeStrainBrowseProps {
    typeStrains: GenomeMeta[];
    speciesList: SpeciesInfo[];
    linkTemplate: string;
}

const ArrowIcon: React.FC = () => (
    <svg
        aria-hidden="true"
        className="vf-icon vf-icon-arrow--inline-end"
        width="1.3em"
        height="1.3em"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
    >
        <path
            d="M0 12c0 6.627 5.373 12 12 12s12-5.373 12-12S18.627 0 12 0C5.376.008.008 5.376 0 12zm13.707-5.209l4.5 4.5a1 1 0 010 1.414l-4.5 4.5a1 1 0 01-1.414-1.414l2.366-2.367a.25.25 0 00-.177-.424H6a1 1 0 010-2h8.482a.25.25 0 00.177-.427l-2.366-2.368a1 1 0 011.414-1.414z"
            fill="currentColor"
            fillRule="nonzero"
        />
    </svg>
);

const TypeStrainBrowse: React.FC<TypeStrainBrowseProps> = ({
    typeStrains,
    speciesList,
    linkTemplate,
}) => {
    const [expanded, setExpanded] = useState(false);

    const groups = useMemo(() => {
        const speciesNameByAcronym = new Map(
            speciesList.map((species) => [species.acronym, species.scientific_name])
        );
        const strainsByAcronym = new Map<string, GenomeMeta[]>();

        typeStrains.forEach((strain) => {
            const acronym = strain.species_acronym || 'unknown';
            const existing = strainsByAcronym.get(acronym) || [];
            existing.push(strain);
            strainsByAcronym.set(acronym, existing);
        });

        strainsByAcronym.forEach((strains, acronym) => {
            strainsByAcronym.set(acronym, [...strains].sort((left, right) =>
                compareTypeStrainIsolates(left.isolate_name, right.isolate_name)
            ));
        });

        const orderedAcronyms = Array.from(strainsByAcronym.keys()).sort((left, right) => {
            const leftName = strainsByAcronym.get(left)?.[0]?.isolate_name || left;
            const rightName = strainsByAcronym.get(right)?.[0]?.isolate_name || right;
            return compareTypeStrainIsolates(leftName, rightName);
        });

        return orderedAcronyms.map((acronym) => ({
            acronym,
            scientific_name:
                speciesNameByAcronym.get(acronym) ||
                strainsByAcronym.get(acronym)?.[0]?.species_scientific_name ||
                acronym,
            strains: strainsByAcronym.get(acronym) || [],
        }));
    }, [typeStrains, speciesList]);

    const shouldCollapse = groups.length > COLLAPSE_GROUP_LIMIT;
    const visibleGroups = expanded || !shouldCollapse
        ? groups
        : groups.slice(0, COLLAPSE_GROUP_LIMIT);

    const generateLink = (strainName: string) => linkTemplate.replace('$strain_name', strainName);

    if (typeStrains.length === 0) {
        return null;
    }

    return (
        <div>
            <div className={styles.typeStrainGroups}>
                {visibleGroups.map((group) => (
                    <div key={group.acronym} className={styles.speciesGroup}>
                        <h4 className={styles.speciesGroupTitle}>
                            <i>{group.scientific_name}</i>
                        </h4>
                        <div className={styles.chipRow}>
                            {group.strains.map((strain) => (
                                <a
                                    key={strain.isolate_name}
                                    href={generateLink(strain.isolate_name)}
                                    className={`vf-link ${styles.strainChip}`}
                                >
                                    {strain.isolate_name}
                                    <ArrowIcon />
                                </a>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
            {shouldCollapse && (
                <button
                    type="button"
                    className={styles.showAllButton}
                    onClick={() => setExpanded((current) => !current)}
                >
                    {expanded ? 'Show fewer type strains' : 'Show all type strains'}
                </button>
            )}
        </div>
    );
};

export default TypeStrainBrowse;
