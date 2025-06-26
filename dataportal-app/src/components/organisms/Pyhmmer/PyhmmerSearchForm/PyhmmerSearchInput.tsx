import React, { useRef } from 'react';
import styles from './PyhmmerSearchInput.module.scss';
import { EXAMPLE_SEQUENCE } from '../../../../utils/appConstants';

interface PyhmmerSearchInputProps {
    sequence: string;
    setSequence: (value: string) => void;
    handleSubmit: (e?: React.FormEvent) => void;
}

const PyhmmerSearchInput: React.FC<PyhmmerSearchInputProps> = ({ sequence, setSequence, handleSubmit }) => {
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    const handleUseExample = (e: React.MouseEvent) => {
        e.preventDefault();
        setSequence(EXAMPLE_SEQUENCE);
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                setSequence(event.target?.result as string || '');
            };
            reader.readAsText(file);
        }
    };

    const handleReset = () => {
        setSequence('');
    };

    return (
        <div className={styles.formSection}>
            <label className={styles.label}>Sequence</label>
            <div className={styles.sequenceInputBox}>
                <textarea
                    className="vf-form__textarea"
                    value={sequence}
                    onChange={e => setSequence(e.target.value)}
                    // placeholder="Paste in your sequence, use the example, drag a file over or choose a file to upload"
                    placeholder="Paste in your sequence, use the example"
                    rows={10}
                />
                <div className={styles.sequenceInputHelp}>
                    Paste in your sequence, use the{' '}
                    <a href="#" onClick={handleUseExample}>example</a>
                    {/*, drag a file over or{' '}*/}
                    {/*<a href="#" onClick={e => {*/}
                    {/*    e.preventDefault();*/}
                    {/*    fileInputRef.current?.click();*/}
                    {/*}}>choose a file to upload</a>*/}
                    {/*<input*/}
                    {/*    type="file"*/}
                    {/*    accept=".fa,.fasta,.txt,.faa,.csv"*/}
                    {/*    style={{ display: 'none' }}*/}
                    {/*    ref={fileInputRef}*/}
                    {/*    onChange={handleFileChange}*/}
                    {/*/>*/}
                </div>
            </div>
            <div className={styles.buttonRow}>
                <button className="vf-button vf-button--primary vf-button--sm" onClick={handleSubmit}>Submit</button>
                <button className="vf-button vf-button--sm" type="button" onClick={handleReset}>Reset</button>
                <button className="vf-button vf-button--sm" type="button" onClick={handleReset}>Clean</button>
            </div>
        </div>
    );
};

export default PyhmmerSearchInput; 