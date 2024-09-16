import React from 'react';

interface ButtonProps {
  onClick?: () => void;
  children: React.ReactNode;
  type?: 'button' | 'submit';
}

const Button: React.FC<ButtonProps> = ({ onClick, children, type = 'button' }) => {
  return (
    <button className="vf-button vf-button--primary" onClick={onClick} type={type}>
      {children}
    </button>
  );
};

export default Button;
