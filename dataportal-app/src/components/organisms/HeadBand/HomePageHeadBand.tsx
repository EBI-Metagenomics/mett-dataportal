import React from 'react';
import styles from './HomePageHeadBand.module.scss';
import {GenomeMeta} from "../../../interfaces/Genome";
import {EBI_FTP_SERVER} from "../../../utils/common/constants";
import {useFeatureFlags} from '../../../hooks/useFeatureFlags';
import {HOMEPAGE_TEXT} from "../../../utils/common/homePageConstants";
import TypeStrainBrowse from './TypeStrainBrowse';


interface HomePageHeadBandProps {
    typeStrains: GenomeMeta[];
    linkTemplate: string;
    speciesList: { acronym: string; scientific_name: string, common_name: string, taxonomy_id: number }[];
}

const HomePageHeadBand: React.FC<HomePageHeadBandProps> = ({
                                                               typeStrains,
                                                               linkTemplate,
                                                               speciesList,
                                                           }) => {
    const {isFeatureEnabled} = useFeatureFlags();

    return (
        <section className="vf-grid vf-grid__col-3 | vf-card-container | vf-u-fullbleed">
            <div className="vf-section-header vf-grid__col--span-3">
                <div className="vf-grid__col--span-2">
                    <div className={`vf-content ${styles.vfContent}`} style={{textAlign: 'justify'}}>

                        {/* Yellow Band - Feedback Link Section */}
                        {isFeatureEnabled('feedback') && (
                            <div className={styles.banner}>
                                <span className={styles.bannerMessage}>
                                    {HOMEPAGE_TEXT.FEEDBACK.MESSAGE}
                                </span>
                                <a
                                    href={HOMEPAGE_TEXT.FEEDBACK.LINK}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className={`vf-link ${styles.bannerLink}`}
                                >
                                    {HOMEPAGE_TEXT.FEEDBACK.LABEL}
                                    <svg
                                        aria-hidden="true"
                                        className={`vf-icon vf-icon-arrow--inline-end ${styles.bannerIcon}`}
                                        xmlns="http://www.w3.org/2000/svg"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle cx="12" cy="12" r="11" fill="currentColor"/>
                                        <path
                                            d="M8.5 7.5l7 4.5-7 4.5v-9z"
                                            fill="white"
                                            fillRule="nonzero"
                                        />
                                    </svg>
                                </a>
                            </div>
                        )}

                        {/* Yellow Band - Natural Search Query */}
                        {isFeatureEnabled('natural_query') && (
                            <div className={styles.banner}>
                                <span className={styles.bannerMessage}>
                                    {HOMEPAGE_TEXT.NATURAL_QUERY.TITLE}
                                </span>
                                <a
                                    href="/natural-query"
                                    className={`vf-link ${styles.bannerLink}`}
                                >
                                    {HOMEPAGE_TEXT.NATURAL_QUERY.BUTTON_TEXT}
                                    <svg
                                        aria-hidden="true"
                                        className="vf-icon vf-icon-arrow--inline-end"
                                        style={{
                                            verticalAlign: 'middle',
                                            display: 'block',
                                            overflow: 'visible',
                                        }}
                                        width="1.3em"
                                        height="1.3em"
                                        xmlns="http://www.w3.org/2000/svg"
                                    >
                                        <path
                                            d="M0 12c0 6.627 5.373 12 12 12s12-5.373 12-12S18.627 0 12 0C5.376.008.008 5.376 0 12zm13.707-5.209l4.5 4.5a1 1 0 010 1.414l-4.5 4.5a1 1 0 01-1.414-1.414l2.366-2.367a.25.25 0 00-.177-.424H6a1 1 0 010-2h8.482a.25.25 0 00.177-.427l-2.366-2.368a1 1 0 011.414-1.414z"
                                            fill="currentColor"
                                            fillRule="nonzero"
                                        ></path>
                                    </svg>
                                </a>
                            </div>
                        )}

                        <p>
                            {HOMEPAGE_TEXT.MAIN_CONTENT.PARAGRAPH_1}
                            <i>{HOMEPAGE_TEXT.MAIN_CONTENT.B_UNIFORMIS}</i>
                            {HOMEPAGE_TEXT.MAIN_CONTENT.AND}
                            <i>{HOMEPAGE_TEXT.MAIN_CONTENT.P_VULGATUS}</i>
                            {HOMEPAGE_TEXT.MAIN_CONTENT.PARAGRAPH_1_CONTINUATION}
                        </p>
                        <p>
                            {HOMEPAGE_TEXT.MAIN_CONTENT.PARAGRAPH_2}
                            <i>{HOMEPAGE_TEXT.MAIN_CONTENT.B_UNIFORMIS}</i>
                            {HOMEPAGE_TEXT.MAIN_CONTENT.AND} <i>{HOMEPAGE_TEXT.MAIN_CONTENT.P_VULGATUS}</i>
                            {HOMEPAGE_TEXT.MAIN_CONTENT.PARAGRAPH_2_CONTINUATION}&nbsp;
                            <a href={EBI_FTP_SERVER} target="_blank" rel="noopener noreferrer">
                                {HOMEPAGE_TEXT.MAIN_CONTENT.FTP_SERVER_LINK}
                            </a>
                            &nbsp;{HOMEPAGE_TEXT.MAIN_CONTENT.PARAGRAPH_2_CONTINUATION_2}
                        </p>
                        <p>
                            {HOMEPAGE_TEXT.MAIN_CONTENT.PARAGRAPH_3} &nbsp;
                            <a href={HOMEPAGE_TEXT.MAIN_CONTENT.METTANNOTATOR_URL}
                               target="_blank"
                               rel="noopener noreferrer">
                                {HOMEPAGE_TEXT.MAIN_CONTENT.METTANNOTATOR_LINK}
                            </a>.
                        </p>


                    </div>
                </div>
                <div>&nbsp;</div>
                <hr className="vf-divider"></hr>
            </div>

            <div className={`vf-section-header vf-grid__col--span-3 ${styles.catalogue}`}>
                <div className={styles.sectionHeader}>
                    <h3 className={`vf-section-header__heading ${styles.sectionTitle}`}>
                        Browse type strains
                    </h3>
                </div>
                <TypeStrainBrowse
                    typeStrains={typeStrains}
                    speciesList={speciesList}
                    linkTemplate={linkTemplate}
                />
            </div>
        </section>
    );
};

export default HomePageHeadBand;
