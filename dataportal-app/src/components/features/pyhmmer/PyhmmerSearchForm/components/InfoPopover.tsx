import React from 'react';
import * as Popover from '@radix-ui/react-popover';
import styles from './InfoPopover.module.scss';

interface InfoPopoverProps {
    label: string;
    helpText: string;
    ariaLabel: string;
}

const InfoPopover: React.FC<InfoPopoverProps> = ({
    label,
    helpText,
    ariaLabel
}) => {
    return (
        <div className={styles.flexRow}>
            <label className={`vf-form__label ${styles.label}`}>
                {label}
                <Popover.Root>
                    <Popover.Trigger asChild>
                        <button
                            className={styles.infoIcon}
                            onClick={e => e.stopPropagation()}
                            aria-label={ariaLabel}
                            type="button"
                        >
                            ℹ️
                        </button>
                    </Popover.Trigger>
                    <Popover.Portal>
                        <Popover.Content
                            className={styles.popoverContent}
                            side="top"
                            align="end"
                            sideOffset={5}
                        >
                            <div className={styles.popoverInner}>
                                <strong>{label}:</strong><br/>
                                <p style={{whiteSpace: 'pre-line'}}>{helpText}</p>
                            </div>
                        </Popover.Content>
                    </Popover.Portal>
                </Popover.Root>
            </label>
        </div>
    );
};

export default InfoPopover;
