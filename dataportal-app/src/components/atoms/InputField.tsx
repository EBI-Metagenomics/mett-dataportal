import React from 'react';

interface InputFieldProps {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    placeholder?: string;
}

const InputField: React.FC<InputFieldProps> = ({value, onChange, placeholder = "Enter text..."}) => {
    return (
        <input
            className="vf-form__input"
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            autoComplete="off"
        />
    );
};

export default InputField;
