import React from 'react';

interface DropdownProps {
  options: { value: string, label: string }[];
  selectedValue: string;
  onChange: (value: string) => void;
}

const Dropdown: React.FC<DropdownProps> = ({ options, selectedValue, onChange }) => {
  return (
    <select className="vf-dropdown" value={selectedValue} onChange={e => onChange(e.target.value)}>
      {options.map(option => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
};

export default Dropdown;
