import React from 'react';

const BiasMeter = ({ label }) => {
    let color = 'gray';
    if (label === 'Left') color = 'blue';
    if (label === 'Right') color = 'red';
    if (label === 'Center') color = 'purple';

    const style = {
        display: 'inline-block',
        width: '10px',
        height: '10px',
        borderRadius: '50%',
        backgroundColor: color,
        marginRight: '5px',
    };

    return (
        <div style={{ display: 'flex', alignItems: 'center', fontSize: '0.8rem', color: '#666' }}>
            <span style={style}></span>
            {label}
        </div>
    );
};

export default BiasMeter;
