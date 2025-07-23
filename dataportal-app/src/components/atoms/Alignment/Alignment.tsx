import React from 'react';
import {LegacyAlignmentDisplay} from '../../../interfaces/Pyhmmer';
import './Alignment.scss';

interface AlignmentProps {
    alignment: LegacyAlignmentDisplay;
    algorithm: string;
    included?: boolean;
}

const Alignment: React.FC<AlignmentProps> = ({alignment, algorithm, included = true}) => {
    if (!alignment) {
        return <div className="alignment-error">No alignment data available</div>;
    }

    const formatSequence = (sequence: string, start: number, end: number) => {
        const lines = [];
        const lineLength = 60;

        for (let i = 0; i < sequence.length; i += lineLength) {
            const line = sequence.slice(i, i + lineLength);
            const position = start + i;
            lines.push({
                sequence: line,
                position: position,
                endPosition: Math.min(position + lineLength - 1, end)
            });
        }

        return lines;
    };

    const queryLines = formatSequence(alignment.model, alignment.hmmfrom, alignment.hmmto);
    const targetLines = formatSequence(alignment.aseq, alignment.sqfrom, alignment.sqto);
    const matchLines = formatSequence(alignment.mline, alignment.hmmfrom, alignment.hmmto);

    return (
        <div className={`alignment-container ${included ? 'included' : 'excluded'}`}>
            <div className="alignment-header">
                <div className="alignment-info">
                    <span className="algorithm">{algorithm.toUpperCase()}</span>
                    <span className="identity">
                        Identity: {(alignment.identity[0] * 100).toFixed(1)}% ({alignment.identity[1]})
                    </span>
                    <span className="similarity">
                        Similarity: {(alignment.similarity[0] * 100).toFixed(1)}% ({alignment.similarity[1]})
                    </span>
                </div>
            </div>

            <div className="alignment-sequences">
                {queryLines.map((line, index) => (
                    <div key={`query-${index}`} className="sequence-line">
                        <div className="sequence-info">
                            <span className="sequence-name">Query</span>
                            <span className="sequence-position">{line.position}-{line.endPosition}</span>
                        </div>
                        <div className="sequence-data">
                            <pre className="sequence-text">{line.sequence}</pre>
                        </div>
                    </div>
                ))}

                {matchLines.map((line, index) => (
                    <div key={`match-${index}`} className="sequence-line match-line">
                        <div className="sequence-info">
                            <span className="sequence-name"></span>
                            <span className="sequence-position"></span>
                        </div>
                        <div className="sequence-data">
                            <pre className="sequence-text match-text">{line.sequence}</pre>
                        </div>
                    </div>
                ))}

                {targetLines.map((line, index) => (
                    <div key={`target-${index}`} className="sequence-line">
                        <div className="sequence-info">
                            <span className="sequence-name">Target</span>
                            <span className="sequence-position">{line.position}-{line.endPosition}</span>
                        </div>
                        <div className="sequence-data">
                            <pre className="sequence-text">{line.sequence}</pre>
                        </div>
                    </div>
                ))}
            </div>

            {alignment.ppline && (
                <div className="posterior-probabilities">
                    <div className="sequence-info">
                        <span className="sequence-name">PP</span>
                        <span className="sequence-position"></span>
                    </div>
                    <div className="sequence-data">
                        <pre className="sequence-text pp-text">{alignment.ppline}</pre>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Alignment; 