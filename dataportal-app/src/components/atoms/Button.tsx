import React from 'react';

interface ButtonProps {
    label: string;
    onClick?: () => void;
    type?: "submit" | "button";
}

const Button: React.FC<ButtonProps> = ({label, onClick, type = "button"}) => {
    return (
        <button className="vf-button vf-button--primary" type={type} onClick={onClick}>
            {label}
        </button>
    );
};

export default Button;
