import React from 'react';
import styles from './InfoPopup.module.scss';

interface InfoPopupProps {
    onClose: () => void;
    children: React.ReactNode;
}

const InfoPopup: React.FC<InfoPopupProps> = ({onClose, children}) => {
    return (
        <div className={styles.anchorWrapper}>
            <div className={styles.popupContent}>
                <button className={styles.closeButton} onClick={onClose}>×</button>
                {children}
            </div>
            <div className={styles.popupBackdrop} onClick={onClose}/>
        </div>
    );
};

export default InfoPopup;
