import React from 'react';

interface InputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
}

const Input: React.FC<InputProps> = ({ value, onChange, placeholder }) => {
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

export default Input;
