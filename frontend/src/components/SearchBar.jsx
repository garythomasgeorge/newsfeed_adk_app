import React, { useState } from 'react';

const SearchBar = ({ onSearch }) => {
    const [query, setQuery] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        onSearch(query);
    };

    return (
        <form onSubmit={handleSubmit} style={{ marginBottom: '24px', display: 'flex' }}>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask the Librarian..."
                style={{
                    flex: 1,
                    padding: '10px',
                    borderRadius: '4px',
                    border: '1px solid #ccc',
                    marginRight: '8px',
                    fontSize: '1rem'
                }}
            />
            <button type="submit" style={{
                padding: '10px 20px',
                backgroundColor: '#333',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '1rem'
            }}>
                Search
            </button>
        </form>
    );
};

export default SearchBar;
