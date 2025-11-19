import React from 'react';

interface ButtonProps {
    label: string;
    onClick: () => void;
    disabled?: boolean;
    className?: string;
}

const Button: React.FC<ButtonProps> = ({ label, onClick, disabled = false, className }) => {
    return (
        <button 
            onClick={onClick}
            disabled={disabled}
            className={`btn ${className}`}
        >
            {label}
        </button>
    );
};

export default Button;