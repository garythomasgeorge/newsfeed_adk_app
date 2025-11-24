import React from 'react';

const BiasMeter = ({ bias }) => {
    if (!bias) return null;

    const getBiasColor = (biasLabel) => {
        switch (biasLabel?.toLowerCase()) {
            case 'left':
                return '#3b82f6'; // Blue
            case 'lean left':
                return '#60a5fa'; // Light Blue
            case 'center':
                return '#a8a29e'; // Grey
            case 'lean right':
                return '#f87171'; // Light Red
            case 'right':
                return '#ef4444'; // Red
            default:
                return '#a8a29e';
        }
    };

    const color = getBiasColor(bias);

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: color
            }} />
            <span style={{
                fontSize: '0.75rem',
                fontWeight: '600',
                color: color,
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
            }}>
                {bias}
            </span>
        </div>
    );
};

export default BiasMeter;
