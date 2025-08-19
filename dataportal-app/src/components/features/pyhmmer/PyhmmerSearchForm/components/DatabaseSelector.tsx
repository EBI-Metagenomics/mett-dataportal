import React from 'react';
import styles from './DatabaseSelector.module.scss';

interface DatabaseSelectorProps {
    database: string;
    databases: { id: string; name: string }[];
    onDatabaseChange: (database: string) => void;
}

const DatabaseSelector: React.FC<DatabaseSelectorProps> = ({
    database,
    databases,
    onDatabaseChange
}) => {
    return (
        <div className={styles.formSection}>
            <label className={`vf-form__label ${styles.label}`}>Sequence database</label>
            <select
                className={`vf-form__select ${styles.databaseSelect}`}
                value={database}
                onChange={e => onDatabaseChange(e.target.value)}
            >
                {databases.length > 0 ? (
                    databases.map(db => (
                        <option key={db.id} value={db.id}>
                            {db.name}
                        </option>
                    ))
                ) : (
                    <option value="">No databases available</option>
                )}
            </select>
        </div>
    );
};

export default DatabaseSelector;
