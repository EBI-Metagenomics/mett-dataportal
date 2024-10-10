import React from 'react';

interface Track {
    name: string;
}

interface Category {
    name: string;
    collapsed?: boolean;
}

interface TrackSelectorModel {
    tracks: Array<Track>;
    categories?: Array<Category>; // Make categories optional
}

interface ViewerTrackSelectorProps {
    model: TrackSelectorModel;
}

// Custom track selector component
const ViewerTrackSelector: React.FC<ViewerTrackSelectorProps> = ({model}) => {
    const sortedTracks = [...model.tracks].sort((a, b) => a.name.localeCompare(b.name));

    if (model.categories) {
        model.categories.forEach(category => {
            if (category.name === 'VCF') {
                category.collapsed = true;
            }
        });
    }

    return (
        <div>
            <p>Track Selector (Customized)</p>
            {sortedTracks.map(track => (
                <div key={track.name}>{track.name}</div>
            ))}
        </div>
    );
};

export default ViewerTrackSelector;
