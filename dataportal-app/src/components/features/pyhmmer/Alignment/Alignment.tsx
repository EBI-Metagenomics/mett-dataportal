import React from 'react';
import {AlignmentDisplay} from '../../../../interfaces/Pyhmmer';
import './Alignment.scss';

interface AlignmentProps {
    alignment: AlignmentDisplay;
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

    const createPositionMarker = (sequence: string, start: number) => {
        const marker = [];
        for (let i = 0; i < sequence.length; i++) {
            const position = start + i;
            const char = sequence[i];

            if (char === '-' || char === ' ') {
                marker.push(' ');
            } else if (position % 10 === 0) {
                marker.push('*');
            } else {
                marker.push('·');
            }
        }
        const result = marker.join('');
        console.log(`Position marker for sequence "${sequence}" (start: ${start}): "${result}"`);
        console.log(`Sequence length: ${sequence.length}, Marker length: ${result.length}`);
        return result;
    };

    const queryLines = formatSequence(alignment.model, alignment.hmmfrom, alignment.hmmto);
    const targetLines = formatSequence(alignment.aseq, alignment.sqfrom, alignment.sqto);
    const matchLines = formatSequence(alignment.mline, alignment.hmmfrom, alignment.hmmto);

    console.log('Formatted lines:', {
        queryLines: queryLines,
        targetLines: targetLines,
        matchLines: matchLines,
        model: alignment.model,
        aseq: alignment.aseq,
        mline: alignment.mline
    });

    // Debug: Check if match line data exists
    console.log('Alignment data:', {
        mline: alignment.mline,
        mlineLength: alignment.mline?.length,
        matchLines: matchLines,
        hasMatchLines: matchLines.length > 0,
        queryLines: queryLines,
        queryLinesLength: queryLines.length
    });

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
                    <React.Fragment key={`block-${index}`}>
                        {/* Position marker line */}
                        <div className="sequence-line position-marker-line">
                            <div className="sequence-info">
                                <span className="sequence-name">Pos</span>
                            </div>
                            <div className="sequence-data">
                                <pre className="sequence-text position-marker">
                                    {line.position.toString().padStart(4)} {createPositionMarker(line.sequence, line.position)} {line.endPosition.toString().padStart(4)}
                                </pre>
                            </div>
                        </div>

                        {/* Query line */}
                        <div className="sequence-line">
                            <div className="sequence-info">
                                <span className="sequence-name">Query</span>
                            </div>
                            <div className="sequence-data">
                                <pre className="sequence-text">
                                    {line.position.toString().padStart(4)} {line.sequence} {line.endPosition.toString().padStart(4)}
                                </pre>
                            </div>
                        </div>

                        {/* PP line */}
                        {matchLines[index] && (
                            <div className="sequence-line match-line">
                                <div className="sequence-info">
                                    <span className="sequence-name">PP</span>
                                </div>
                                <div className="sequence-data">
                                    <pre className="sequence-text match-text">
                                        {matchLines[index].position.toString().padStart(4)} {matchLines[index].sequence}
                                    </pre>
                                </div>
                            </div>
                        )}

                        {/* Target line */}
                        {targetLines[index] && (
                            <div className="sequence-line">
                                <div className="sequence-info">
                                    <span className="sequence-name">Target</span>
                                </div>
                                <div className="sequence-data">
                                    <pre className="sequence-text">
                                        {targetLines[index].position.toString().padStart(4)} {targetLines[index].sequence} {targetLines[index].endPosition.toString().padStart(4)}
                                    </pre>
                                </div>
                            </div>
                        )}
                    </React.Fragment>
                ))}
            </div>


        </div>
    );
};

export default Alignment; 