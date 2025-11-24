import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import NewsCard from '../components/NewsCard';
import SearchBar from '../components/SearchBar';

// Use relative path to leverage Vite proxy
const API_BASE_URL = '/api';

const Home = () => {
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [view, setView] = useState('feed'); // 'feed' or 'search'
    const [selectedDate, setSelectedDate] = useState('');
    const navigate = useNavigate();

    const [availableDates, setAvailableDates] = useState([]);

    useEffect(() => {
        fetchAvailableDates();
        fetchFeed();
    }, [selectedDate]);

    const fetchAvailableDates = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/available-dates`);
            setAvailableDates(response.data);
        } catch (error) {
            console.error("Error fetching available dates:", error);
        }
    };

    const fetchFeed = async () => {
        setLoading(true);
        setError(null);
        try {
            let url = `${API_BASE_URL}/feed`;
            if (selectedDate) {
                url += `?date=${selectedDate}`;
            }
            console.log("Fetching feed from:", url);
            const response = await axios.get(url);
            setArticles(response.data);
            setView('feed');
        } catch (error) {
            console.error("Error fetching feed:", error);
            setError(`Failed to load news: ${error.message}`);
        }
        setLoading(false);
    };

    const handleSearch = async (query) => {
        if (!query.trim()) {
            fetchFeed();
            return;
        }
        setLoading(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/search`, { query });
            setArticles(response.data.results);
            setView('search');
        } catch (error) {
            console.error("Error searching:", error);
            setError(`Search failed: ${error.message}`);
        }
        setLoading(false);
    };

    const handleArticleClick = (article) => {
        // Navigate to article page with state
        navigate('/article', { state: { article } });
    };

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '40px 20px' }}>
            <header style={{ marginBottom: '50px', textAlign: 'center' }}>
                <h1 style={{ fontSize: '3rem', fontWeight: '800', marginBottom: '10px', letterSpacing: '-0.05em', color: '#333' }}>Daily Briefing</h1>
                <p style={{ color: '#666', fontSize: '1.1rem' }}>AI-Curated News Aggregator</p>
            </header>

            <SearchBar onSearch={handleSearch} />

            <div style={{ marginBottom: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: '600', margin: 0, color: '#444' }}>
                    {view === 'feed' ? 'Latest Stories' : 'Search Results'}
                </h2>

                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <select
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        style={{
                            padding: '8px 12px',
                            borderRadius: '8px',
                            border: '1px solid #ddd',
                            fontFamily: 'inherit',
                            backgroundColor: '#fff',
                            cursor: 'pointer',
                            fontSize: '0.95rem'
                        }}
                    >
                        <option value="">All Dates</option>
                        {availableDates.map(date => (
                            <option key={date} value={date}>
                                {new Date(date).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                            </option>
                        ))}
                    </select>

                    {view === 'search' && (
                        <button onClick={() => { setSelectedDate(''); fetchFeed(); }} style={{
                            background: 'none', border: 'none', color: '#007bff', cursor: 'pointer', textDecoration: 'underline'
                        }}>
                            Back to Feed
                        </button>
                    )}
                </div>
            </div>

            {error && (
                <div style={{
                    backgroundColor: '#ffebee',
                    color: '#c62828',
                    padding: '15px',
                    borderRadius: '8px',
                    marginBottom: '20px',
                    textAlign: 'center'
                }}>
                    {error}
                </div>
            )}

            {loading ? (
                <div style={{ textAlign: 'center', padding: '60px', color: '#888' }}>Processing news...</div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {articles.length > 0 ? (
                        articles.map((article) => (
                            <NewsCard
                                key={article.url}
                                article={article}
                                onClick={handleArticleClick}
                            />
                        ))
                    ) : (
                        <p style={{ textAlign: 'center', color: '#666', marginTop: '40px' }}>No articles found for this date.</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default Home;
